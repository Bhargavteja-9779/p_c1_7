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
    shift_calib: np.ndarray | None = None   # (n_folds, n_calib) cross-fitted shift score
    shift_test: np.ndarray | None = None    # (n_test,) out-of-fold shift score
    test_fold: np.ndarray | None = None     # (n_test,) fold id of each test point
    ad2_calib: np.ndarray | None = None     # second AD coordinate (e.g. physicochemical), calib
    ad2_test: np.ndarray | None = None      # second AD coordinate, test

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


# ---------------------------------------------------------------------------
# ADCC-CP: Applicability-Domain Conditional Conformal prediction
# ---------------------------------------------------------------------------
# Function-class conditional conformal (Gibbs, Cherian & Candes, JRSSB 2025)
# instantiated on a low-dimensional applicability-domain function class F_AD.
# For every nonnegative f in F_AD the augmented quantile-regression set satisfies
#     E[ f(X) (1{Y in C(X)} - (1-alpha)) ] >= 0,
# i.e. (i) exact finite-sample coverage within every AD stratum G_k (f = 1{G_k}) and
# (ii) coverage under EVERY covariate shift whose density ratio, as a function of the
# AD coordinate, lies in F_AD (f = dP_test/dP_cal) -- simultaneously, and WITHOUT
# estimating any density ratio. Computed exactly via the dual of the augmented
# quantile regression (the test score is in the set iff its dual variable < 1-alpha),
# with a bisection over the imputed test score.

def _ad_edges(ad_calib, n_strata):
    qs = np.linspace(0, 1, n_strata + 1)[1:-1]
    return np.unique(np.quantile(ad_calib, qs))


def ad_basis(a, edges, kind="pl", sigma=None, wfun=None):
    """Feature map phi(a) spanning the AD function class F_AD.
    pl     : stratum indicators + within-stratum linear tilt  (d = 2K)
    grp    : stratum indicators only (Mondrian-equivalent class; d = K)
    spline : continuous linear spline in a with knots at stratum edges (d = K+1)
    pl_sig : pl + local difficulty sigma(x) (adaptive width)
    pl_w   : pl + an externally supplied (estimated) density ratio w(a)."""
    a = np.asarray(a, float)
    K = len(edges) + 1
    k = np.digitize(a, edges)
    n = len(a)
    if kind == "spline":
        cols = [np.ones(n), a] + [np.maximum(a - e, 0.0) for e in edges]
        return np.column_stack(cols)
    G = np.zeros((n, K)); G[np.arange(n), k] = 1.0
    if kind == "grp":
        return G
    L = G * a[:, None]
    P = np.hstack([G, L])
    if kind == "pl_sig":
        P = np.hstack([P, np.asarray(sigma, float)[:, None]])
    elif kind == "pl_w":
        P = np.hstack([P, np.asarray(wfun(a), float)[:, None]])
    return P


def ad_basis_2d(a1, a2, edges1, edges2):
    """Additive continuous-linear-spline feature map over TWO applicability-domain coordinates
    (e.g. structural max-Tanimoto a1 and physicochemical-distance a2). Spans the class of
    functions f(x)=g1(a1(x))+g2(a2(x)) with g1,g2 piecewise linear; a single shared intercept.
    d = (1 + 1 + |edges1|) + (1 + |edges2|)."""
    a1 = np.asarray(a1, float); a2 = np.asarray(a2, float); n = len(a1)
    cols = [np.ones(n), a1] + [np.maximum(a1 - e, 0.0) for e in edges1]
    cols += [a2] + [np.maximum(a2 - e, 0.0) for e in edges2]
    return np.column_stack(cols)


def _drop_empty_cols(Pc):
    keep = np.abs(Pc).sum(axis=0) > 0
    return keep


def conditional_conformal_threshold(S_cal, P_cal, p_test, level, n_bisect=18):
    """Largest imputed score S such that the augmented quantile regression leaves the
    test point strictly inside (dual variable eta_{n+1} < level). Exact up to bisection
    tolerance (max(S)*2^-n_bisect). Returns +inf if the test point is never covered."""
    from scipy.optimize import linprog
    tau = level
    A = np.vstack([P_cal, p_test[None, :]]).T          # d x (n+1)
    keep = np.abs(A).sum(axis=1) > 0
    A = A[keep]
    b = np.zeros(A.shape[0])

    def eta_last(s):
        c = -np.append(S_cal, s)
        r = linprog(c, A_eq=A, b_eq=b, bounds=(tau - 1.0, tau), method="highs")
        if r.status != 0:
            return tau
        return r.x[-1]

    hi = 2.0 * float(np.max(S_cal)) + 1e-6
    if eta_last(hi) < tau - 1e-9:
        return np.inf
    lo = 0.0
    for _ in range(n_bisect):
        mid = 0.5 * (lo + hi)
        if eta_last(mid) < tau - 1e-9:
            lo = mid
        else:
            hi = mid
    return hi   # conservative end of the bracket


def _adcc_generic(ctx: CPContext, kind="pl", score="abs", round_a=0.01, wfun=None, knots="calib"):
    if knots == "pool":
        # deployment-aware knots: quantiles of the UNLABELED pool's AD values merged with the
        # calibration quartiles (exploratory, post-registration variant)
        e1 = _ad_edges(ctx.ad_calib, 4); e2 = _ad_edges(ctx.ad_test, 4)
        edges = np.unique(np.round(np.concatenate([e1, e2]), 2))
    else:
        edges = _ad_edges(ctx.ad_calib, ctx.n_strata if ctx.n_strata > 1 else 4)
    ac = np.asarray(ctx.ad_calib, float); at = np.asarray(ctx.ad_test, float)
    if round_a and kind != "pl_sig":
        ac = np.round(ac / round_a) * round_a; at = np.round(at / round_a) * round_a
    if score == "norm":
        S = ctx.resid_calib / ctx.sigma_calib
        scale = ctx.sigma_test
    else:
        S = ctx.resid_calib
        scale = np.ones(len(at))
    Pc = ad_basis(ac, edges, kind, sigma=ctx.sigma_calib, wfun=wfun)
    Pt = ad_basis(at, edges, kind, sigma=ctx.sigma_test, wfun=wfun)
    hw = np.empty(len(at))
    cache = {}
    for j in range(len(at)):
        key = tuple(np.round(Pt[j], 6))
        if key not in cache:
            cache[key] = conditional_conformal_threshold(S, Pc, Pt[j], ctx.level)
        hw[j] = cache[key]
    return _interval(ctx.yhat_test, hw * scale)


def method_adcc(ctx):
    """ADCC-CP primary (locked 2026-11-21 by dev selection on MoleculeNet scaffold sets only):
    F_AD = continuous linear splines in a(x) with knots at the AD-stratum edges."""
    return _adcc_generic(ctx, "spline")


def method_adcc_pl(ctx):
    return _adcc_generic(ctx, "pl")


def method_adcc_grp(ctx):
    return _adcc_generic(ctx, "grp")


def method_adcc_sig(ctx):
    return _adcc_generic(ctx, "pl_sig", round_a=None)


def method_adcc_norm(ctx):
    return _adcc_generic(ctx, "pl", score="norm")


def _spline1d(v, knots):
    v = np.asarray(v, float)
    return np.column_stack([v] + [np.maximum(v - k, 0.0) for k in knots])


def method_adcc_plus(ctx: CPContext, n_knots=2, r=0.01):
    """ADCC-CP+ : F = F_AD (linear spline in a) (+) linear spline in a cross-fitted, label-free
    shift score p(x) = P(pool | x) from a train-vs-pool fingerprint classifier. For a test point
    in fold k the basis uses the classifier trained WITHOUT fold k, so F is independent of the
    calibration labels and of that test point: the finite-sample guarantee of ADCC-CP holds for
    the enlarged class, whether or not p is a good density-ratio estimate. The estimate enters as
    a basis function (a direction in which coverage is enforced), never as an importance weight,
    so it cannot collapse the effective sample size."""
    edges = _ad_edges(ctx.ad_calib, ctx.n_strata if ctx.n_strata > 1 else 4)
    rnd = lambda v: np.round(np.asarray(v, float) / r) * r
    ac, at = rnd(ctx.ad_calib), rnd(ctx.ad_test)
    Pa_c = ad_basis(ac, edges, "spline"); Pa_t = ad_basis(at, edges, "spline")
    S = ctx.resid_calib
    hw = np.empty(len(at))
    for k in np.unique(ctx.test_fold):
        pc = rnd(ctx.shift_calib[k]); tsel = np.where(ctx.test_fold == k)[0]
        pt = rnd(ctx.shift_test[tsel])
        knots = np.unique(np.quantile(pc, np.linspace(0, 1, n_knots + 2)[1:-1]))
        Pc = np.hstack([Pa_c, _spline1d(pc, knots)])
        Pt = np.hstack([Pa_t[tsel], _spline1d(pt, knots)])
        cache = {}
        for jj, j in enumerate(tsel):
            key = tuple(np.round(Pt[jj], 6))
            if key not in cache:
                cache[key] = conditional_conformal_threshold(S, Pc, Pt[jj], ctx.level)
            hw[j] = cache[key]
    return _interval(ctx.yhat_test, hw)


def method_adcc_plus_norm(ctx: CPContext):
    """ADCC-CP+ with the normalized score |r|/sigma(x)."""
    import copy
    c2 = copy.copy(ctx)
    c2.resid_calib = ctx.resid_calib / ctx.sigma_calib
    lo, hi = method_adcc_plus(c2)
    hw = (hi - lo) / 2.0 * ctx.sigma_test
    return _interval(ctx.yhat_test, hw)


def method_adcc_2d(ctx, r=0.04):
    """Multi-coordinate ADCC-CP: function class = additive piecewise-linear functions of TWO
    applicability-domain coordinates (structural a(x) and physicochemical a2(x)). By Theorem 1
    the single interval is valid under every covariate shift whose density ratio is additive
    piecewise-linear in (a, a2) — i.e. shifts aligned with structural novelty, physicochemical
    novelty, or any additive combination — still WITHOUT estimating any density ratio."""
    if ctx.ad2_calib is None:
        return method_adcc(ctx)   # second coordinate unavailable -> fall back to 1-D
    e1 = _ad_edges(ctx.ad_calib, ctx.n_strata if ctx.n_strata > 1 else 4)
    e2 = _ad_edges(ctx.ad2_calib, ctx.n_strata if ctx.n_strata > 1 else 4)
    rnd = lambda v: np.round(np.asarray(v, float) / r) * r
    a1c, a1t = rnd(ctx.ad_calib), rnd(ctx.ad_test)
    a2c, a2t = rnd(ctx.ad2_calib), rnd(ctx.ad2_test)
    Pc = ad_basis_2d(a1c, a2c, e1, e2)
    Pt = ad_basis_2d(a1t, a2t, e1, e2)
    S = ctx.resid_calib
    hw = np.empty(len(a1t)); cache = {}
    for j in range(len(a1t)):
        key = (round(float(a1t[j]), 4), round(float(a2t[j]), 4))
        if key not in cache:
            cache[key] = conditional_conformal_threshold(S, Pc, Pt[j], ctx.level, n_bisect=14)
        hw[j] = cache[key]
    return _interval(ctx.yhat_test, hw)


def method_adcc_pk(ctx):
    return _adcc_generic(ctx, "spline", knots="pool")


DISPATCH.update({
    "adcc_2d": method_adcc_2d,
    "adcc_pk": method_adcc_pk,
    "adcc_plus": method_adcc_plus,
    "adcc_plus_norm": method_adcc_plus_norm,
    "adcc": method_adcc,
    "adcc_grp": method_adcc_grp,
    "adcc_pl": method_adcc_pl,
    "adcc_sig": method_adcc_sig,
    "adcc_norm": method_adcc_norm,
})
