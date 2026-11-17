"""All conformal methods under one dispatcher. Each returns per-test-point
(lower, upper) prediction bounds for the regression target.

Methods
  raw_ensemble      B0  non-conformal Gaussian reference (RF tree std)
  split             B1  standard split conformal (absolute residual)
  normalized        B2  normalized split conformal (local sigma)
  mondrian          B3  AD-stratified split conformal (unweighted)
  localized         B4  Tanimoto-kernel localized conformal (Guan/dAD-style)
  weighted_disc     B5  covariate-shift weighted CP, fingerprint discriminator  [ours-marginal]
  weighted_logistic B5' weighted CP, logistic density ratio  (CoDrug-style)
  weighted_kde      B5' weighted CP, KDE density ratio        (CoDrug-style)
  adwcp             M1  AD-stratified weighted CP             [ours, proposed]
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .base import knn_local_sigma, z_half_width
from .weighting import (weighted_quantile_threshold, unweighted_quantile_threshold)


@dataclass
class CPContext:
    level: float
    yhat_calib: np.ndarray
    y_calib: np.ndarray
    yhat_test: np.ndarray
    resid_calib: np.ndarray        # |y_calib - yhat_calib|
    sigma_calib: np.ndarray
    sigma_test: np.ndarray
    ad_calib: np.ndarray
    ad_test: np.ndarray
    calib_bin: np.ndarray
    test_bin: np.ndarray
    w_calib: np.ndarray            # covariate-shift weights (shared by weighted methods)
    w_test: np.ndarray
    raw_std_test: np.ndarray | None = None
    sim_te_ca: np.ndarray | None = None   # (n_test, n_calib) Tanimoto, for localized CP
    bandwidth: float = 0.25

    @property
    def n_strata(self):
        return int(max(self.calib_bin.max(), self.test_bin.max())) + 1 if len(self.calib_bin) else 1


def _min_calib_for_level(level):
    # need ceil((n+1)*level) <= n  ->  n >= level/(1-level); use a safe small floor
    return max(10, int(np.ceil(1.0 / (1.0 - level))) + 1)


def _interval(yhat, hw):
    hw = np.asarray(hw, float)
    return yhat - hw, yhat + hw


def method_split(ctx: CPContext):
    q = unweighted_quantile_threshold(ctx.resid_calib, ctx.level)
    return _interval(ctx.yhat_test, np.full(len(ctx.yhat_test), q))


def method_normalized(ctx: CPContext):
    scores = ctx.resid_calib / ctx.sigma_calib
    q = unweighted_quantile_threshold(scores, ctx.level)
    return _interval(ctx.yhat_test, q * ctx.sigma_test)


def method_raw_ensemble(ctx: CPContext):
    if ctx.raw_std_test is None:
        return method_split(ctx)
    return _interval(ctx.yhat_test, z_half_width(ctx.raw_std_test, ctx.level))


def method_mondrian(ctx: CPContext):
    nmin = _min_calib_for_level(ctx.level)
    global_q = unweighted_quantile_threshold(ctx.resid_calib, ctx.level)
    nb = ctx.n_strata
    q_by_bin = {}
    for b in range(nb):
        sel = ctx.calib_bin == b
        if sel.sum() >= nmin:
            q_by_bin[b] = unweighted_quantile_threshold(ctx.resid_calib[sel], ctx.level)
        else:
            q_by_bin[b] = global_q  # fallback for sparse strata
    hw = np.array([q_by_bin.get(int(b), global_q) for b in ctx.test_bin])
    return _interval(ctx.yhat_test, hw)


def method_localized(ctx: CPContext):
    """Tanimoto-kernel localized conformal (Guan/dAD-style). Kernel exp(-(1-sim)/h)
    is bounded to (0,1], maximal (=1) at identity, so the test atom cannot dominate."""
    w_self = 1.0
    S = ctx.sim_te_ca                      # (n_test, n_calib)
    K = np.exp(-(1.0 - S) / ctx.bandwidth)
    hw = np.empty(len(ctx.yhat_test))
    for j in range(len(ctx.yhat_test)):
        hw[j] = weighted_quantile_threshold(ctx.resid_calib, K[j], w_self, ctx.level)
    return _interval(ctx.yhat_test, hw)


def _weighted_marginal(ctx: CPContext):
    hw = np.empty(len(ctx.yhat_test))
    for j in range(len(ctx.yhat_test)):
        hw[j] = weighted_quantile_threshold(ctx.resid_calib, ctx.w_calib, ctx.w_test[j], ctx.level)
    return _interval(ctx.yhat_test, hw)


# weighted_disc / weighted_logistic / weighted_kde all use _weighted_marginal with
# the appropriate weights precomputed into ctx.w_calib / ctx.w_test by the runner.
method_weighted = _weighted_marginal


def method_adwcp(ctx: CPContext):
    """Proposed: AD-stratified weighted conformal (ADW-CP). Within an AD-similarity
    stratum, apply covariate-shift-weighted conformal. To avoid fragmenting the
    calibration set (which inflates intervals), each stratum BORROWS calibration
    points from adjacent bins (|bin - test_bin| <= radius), so conditioning is soft.
    The density-ratio weights still correct residual within-neighbourhood shift.
    Sparse neighbourhoods fall back to the global weighted threshold."""
    nmin = _min_calib_for_level(ctx.level)
    radius = 1
    hw = np.empty(len(ctx.yhat_test))
    for j in range(len(ctx.yhat_test)):
        b = int(ctx.test_bin[j])
        sel = np.abs(ctx.calib_bin - b) <= radius
        if sel.sum() >= nmin:
            hw[j] = weighted_quantile_threshold(ctx.resid_calib[sel], ctx.w_calib[sel],
                                                ctx.w_test[j], ctx.level)
        else:
            hw[j] = weighted_quantile_threshold(ctx.resid_calib, ctx.w_calib,
                                                ctx.w_test[j], ctx.level)
    return _interval(ctx.yhat_test, hw)


def method_adecp(ctx: CPContext):
    """Proposed: Applicability-Domain Conformal Extrapolation (ADE-CP).

    Rationale: under chemical covariate shift the test compounds in the out-of-domain
    stratum are MORE novel than any calibration compound, so a per-bin constant quantile
    (Mondrian) or a point sigma (normalized) cannot cover them. ADE-CP models the
    conformal residual quantile as a monotone function of the applicability-domain
    coordinate (similarity-to-training) and EXTRAPOLATES it beyond the calibrated range,
    then applies a split-conformal (CQR-style) correction for finite-sample marginal
    validity. Deployable (needs only AD score + calibration), model-agnostic, cheap.

    Construction:
      features f = [AD_score, local_sigma]; fit linear quantile regression of |resid|
      at level tau on calibration -> q_hat(f). Conformity E_i = |resid_i| - q_hat(f_i).
      Correction c = unweighted (1-alpha) quantile of E. Half-width(test) = max(0, q_hat(f*) + c).
    The linear quantile fit extrapolates with slope, widening intervals for novelty
    outside the calibrated domain. Falls back to split conformal if the fit is singular.
    """
    try:
        import statsmodels.api as sm
    except Exception:
        return method_split(ctx)
    tau = ctx.level
    # feature: AD score (novelty) and local sigma; standardize AD for conditioning
    ac = np.asarray(ctx.ad_calib, float); at = np.asarray(ctx.ad_test, float)
    sc = np.asarray(ctx.sigma_calib, float); st = np.asarray(ctx.sigma_test, float)
    Xc = np.column_stack([np.ones_like(ac), ac, sc])
    Xt = np.column_stack([np.ones_like(at), at, st])
    s = np.asarray(ctx.resid_calib, float)
    try:
        mod = sm.QuantReg(s, Xc).fit(q=tau, max_iter=2000)
        qc = mod.predict(Xc); qt = mod.predict(Xt)
    except Exception:
        return method_split(ctx)
    qc = np.maximum(qc, 0.0); qt = np.maximum(qt, 0.0)
    E = s - qc
    c = unweighted_quantile_threshold(E, tau)   # may be negative; CQR correction
    if not np.isfinite(c):
        c = float(np.max(E)) if len(E) else 0.0
    hw = np.maximum(qt + c, 0.0)
    return _interval(ctx.yhat_test, hw)


def method_kmm(ctx: CPContext):
    """KMM-weighted conformal (KMM-CP style): normalized weighted quantile of
    calibration scores using Kernel-Mean-Matching importance weights (no test atom),
    giving a single reweighted threshold. ctx.w_calib holds the KMM weights."""
    q = weighted_quantile_threshold(ctx.resid_calib, ctx.w_calib, 0.0, ctx.level)
    return _interval(ctx.yhat_test, np.full(len(ctx.yhat_test), q))


DISPATCH = {
    "raw_ensemble": method_raw_ensemble,
    "weighted_kmm": method_kmm,
    "split": method_split,
    "normalized": method_normalized,
    "mondrian": method_mondrian,
    "localized": method_localized,
    "weighted_disc": method_weighted,
    "weighted_ad": method_weighted,
    "weighted_logistic": method_weighted,
    "weighted_kde": method_weighted,
    "adwcp": method_adwcp,
    "adecp": method_adecp,
}


def run_method(name: str, ctx: CPContext):
    return DISPATCH[name](ctx)
