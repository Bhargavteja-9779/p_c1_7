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


def _within_stratum_ad_weights(ad_calib_k, ad_test_k, clip=(0.02, 0.98), cap=20.0):
    """1-D within-stratum covariate-shift weights along the AD coordinate:
    w(a) = p_test(a|G)/p_cal(a|G), estimated by logistic regression separating
    calibration a-values from pool a-values restricted to the stratum. Returns a
    function; near-uniform when the stratum has little internal AD gradient."""
    from sklearn.linear_model import LogisticRegression
    if len(ad_test_k) < 5 or len(ad_calib_k) < 5 or np.ptp(ad_calib_k) < 1e-6:
        return lambda a: np.ones(len(a))
    A = np.concatenate([ad_calib_k, ad_test_k]).reshape(-1, 1)
    y = np.concatenate([np.zeros(len(ad_calib_k)), np.ones(len(ad_test_k))])
    try:
        lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced").fit(A, y)
    except Exception:
        return lambda a: np.ones(len(a))
    prior = len(ad_calib_k) / max(1, len(ad_test_k))

    def wfun(a):
        p = np.clip(lr.predict_proba(np.asarray(a).reshape(-1, 1))[:, 1], clip[0], clip[1])
        return np.clip((p / (1 - p)) * prior, 1.0 / cap, cap)
    return wfun


def method_mwcp(ctx: CPContext):
    """Mondrian-Weighted Conformal Prediction (MW-CP) — proposed primary method.

    Partition by applicability-domain stratum (Mondrian cells on the AD coordinate);
    within each stratum apply *within-stratum* covariate-shift-weighted split conformal,
    with weights estimated from the unlabeled pool restricted to that stratum. This
    targets GROUP-CONDITIONAL coverage: under within-stratum weighted exchangeability,
    weighted conformal applied within cell G_k yields P(Y in C(X) | X in G_k) >= 1-alpha
    in finite samples (Tibshirani 2019, restricted to G_k). Strata with too few
    calibration points fall back to the pooled (global weighted) threshold; the number
    of strata is chosen so each cell meets a minimum calibration count.
    """
    nmin = _min_calib_for_level(ctx.level)
    nb = ctx.n_strata
    hw = np.empty(len(ctx.yhat_test))
    # precompute per-stratum within-stratum weights and calibration
    for k in range(nb):
        cmask = ctx.calib_bin == k
        tmask = ctx.test_bin == k
        if not np.any(tmask):
            continue
        if cmask.sum() >= nmin:
            wfun = _within_stratum_ad_weights(ctx.ad_calib[cmask], ctx.ad_test[tmask])
            wc = wfun(ctx.ad_calib[cmask])
            wt = wfun(ctx.ad_test[tmask])
            s_k = ctx.resid_calib[cmask]
            tj = np.where(tmask)[0]
            for jj, j in enumerate(tj):
                hw[j] = weighted_quantile_threshold(s_k, wc, wt[jj], ctx.level)
        else:
            # fallback: global weighted threshold (marginal) for sparse strata
            tj = np.where(tmask)[0]
            for j in tj:
                hw[j] = weighted_quantile_threshold(ctx.resid_calib, ctx.w_calib,
                                                    ctx.w_test[j] if len(ctx.w_test) == len(hw) else 1.0,
                                                    ctx.level)
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

    Construction (proper CQR, two-fold calibration split for validity):
      features f = [AD_score, local_sigma]. Split calibration into folds A and B.
      Fit linear quantile regression of |resid| at level tau on fold A -> q_hat(f).
      Conformity on fold B: E_i = |resid_i| - q_hat(f_i); correction c = (1-alpha) quantile of E_B.
      Half-width(test) = max(0, q_hat(f*) + c). Because the quantile model is fit on fold A
      (independent of fold B), the E_B scores are exchangeable with the test score, so the
      CQR marginal guarantee holds (under exchangeability). The linear fit extrapolates with
      slope beyond the calibrated AD range. Falls back to split conformal if the fit is singular.
    """
    try:
        import statsmodels.api as sm
    except Exception:
        return method_split(ctx)
    tau = ctx.level
    ac = np.asarray(ctx.ad_calib, float); at = np.asarray(ctx.ad_test, float)
    sc = np.asarray(ctx.sigma_calib, float); st = np.asarray(ctx.sigma_test, float)
    s = np.asarray(ctx.resid_calib, float)
    n = len(s)
    if n < 40:   # too few to split; fall back
        return method_split(ctx)
    # deterministic two-fold split of calibration (seeded upstream via set_global_seed)
    perm = np.random.permutation(n)
    half = n // 2
    A, B = perm[:half], perm[half:]
    XcA = np.column_stack([np.ones(half), ac[A], sc[A]])
    Xt = np.column_stack([np.ones_like(at), at, st])
    XcB = np.column_stack([np.ones(len(B)), ac[B], sc[B]])
    try:
        mod = sm.QuantReg(s[A], XcA).fit(q=tau, max_iter=2000)
        qB = np.maximum(mod.predict(XcB), 0.0)
        qt = np.maximum(mod.predict(Xt), 0.0)
    except Exception:
        return method_split(ctx)
    E = s[B] - qB
    c = unweighted_quantile_threshold(E, tau)   # (n_B+1) quantile; CQR correction
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
    "mwcp": method_mwcp,
    "adecp": method_adecp,
}


def run_method(name: str, ctx: CPContext):
    return DISPATCH[name](ctx)
