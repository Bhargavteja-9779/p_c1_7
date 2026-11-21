"""Unit tests for ADCC-CP (function-class conditional conformal on the AD axis).
Run: python tests/test_adcc.py . No network; synthetic data."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.conformal.methods import (conditional_conformal_threshold, ad_basis, _ad_edges)


def _edges(a):
    return _ad_edges(a, 4)


def test_marginal_coverage_exchangeable():
    """On exchangeable data, ADCC-CP (spline class) attains >= nominal marginal coverage."""
    rng = np.random.default_rng(0)
    covs = []
    for _ in range(60):
        a = rng.uniform(0, 1, 400)
        s = np.abs(rng.normal(0, 1 + a, 400))        # heteroscedastic in a
        e = _edges(a); P = ad_basis(np.round(a, 2), e, "spline")
        at = rng.uniform(0, 1, 300)
        st = np.abs(rng.normal(0, 1 + at, 300))
        Pt = ad_basis(np.round(at, 2), e, "spline")
        cov = []
        # cache by rounded a
        cache = {}
        for j in range(len(at)):
            key = round(at[j], 2)
            if key not in cache:
                cache[key] = conditional_conformal_threshold(s, P, Pt[j], 0.9)
            cov.append(st[j] <= cache[key])
        covs.append(np.mean(cov))
    assert np.mean(covs) >= 0.88, np.mean(covs)


def test_group_coverage_within_strata():
    """Coverage holds within each AD stratum (soft Mondrian), not only marginally."""
    rng = np.random.default_rng(1)
    bins = {0: [], 1: [], 2: [], 3: []}
    for _ in range(40):
        a = rng.uniform(0, 1, 500)
        s = np.abs(rng.normal(0, 1 + 2 * a, 500))
        e = _edges(a); P = ad_basis(np.round(a, 2), e, "spline")
        at = rng.uniform(0, 1, 400); st = np.abs(rng.normal(0, 1 + 2 * at, 400))
        Pt = ad_basis(np.round(at, 2), e, "spline")
        tb = np.digitize(at, e)
        cache = {}
        for j in range(len(at)):
            key = round(at[j], 2)
            if key not in cache:
                cache[key] = conditional_conformal_threshold(s, P, Pt[j], 0.9)
            bins[int(tb[j])].append(st[j] <= cache[key])
    for b, v in bins.items():
        assert np.mean(v) >= 0.84, (b, np.mean(v))   # group-conditional, allow small-sample slack


def test_coverage_under_ad_aligned_shift_no_estimation():
    """Known shift whose ratio is piecewise-linear in a (inside the class): ADCC-CP keeps
    coverage WITHOUT any density ratio being estimated, while split conformal under-covers."""
    rng = np.random.default_rng(2)
    adcc_cov, split_cov = [], []
    for _ in range(40):
        a = rng.uniform(0, 1, 600)
        s = np.abs(rng.normal(0, 1 + 2 * a, 600))
        e = _edges(a); P = ad_basis(np.round(a, 2), e, "spline")
        from src.conformal.weighting import unweighted_quantile_threshold
        qsplit = unweighted_quantile_threshold(s, 0.9)
        # test pool tilted toward high-a (novel) with ratio proportional to a
        pool_a = rng.uniform(0, 1, 4000)
        keep = rng.uniform(0, 1, 4000) < pool_a            # p(keep) ~ a  (pw-linear ratio)
        at = pool_a[keep][:400]
        st = np.abs(rng.normal(0, 1 + 2 * at, len(at)))
        Pt = ad_basis(np.round(at, 2), e, "spline")
        cache = {}
        cov = []
        for j in range(len(at)):
            key = round(at[j], 2)
            if key not in cache:
                cache[key] = conditional_conformal_threshold(s, P, Pt[j], 0.9)
            cov.append(st[j] <= cache[key])
        adcc_cov.append(np.mean(cov)); split_cov.append(np.mean(st <= qsplit))
    assert np.mean(split_cov) < 0.9, np.mean(split_cov)
    assert np.mean(adcc_cov) > np.mean(split_cov), (np.mean(split_cov), np.mean(adcc_cov))
    assert np.mean(adcc_cov) >= 0.86, np.mean(adcc_cov)


def test_indicator_class_recovers_mondrian():
    """The indicator function class yields per-stratum (Mondrian) thresholds."""
    rng = np.random.default_rng(3)
    a = rng.uniform(0, 1, 800); s = np.abs(rng.normal(0, 1 + a, 800))
    e = _edges(a); P = ad_basis(np.round(a, 3), e, "grp")
    # test point in stratum 0 -> threshold near the stratum-0 split quantile
    from src.conformal.weighting import unweighted_quantile_threshold
    sel = np.digitize(a, e) == 0
    q0 = unweighted_quantile_threshold(s[sel], 0.9)
    pt = ad_basis(np.array([0.5 * e[0]]), e, "grp")[0]
    q = conditional_conformal_threshold(s, P, pt, 0.9)
    assert abs(q - q0) < 0.25 * q0 + 0.2, (q, q0)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\nAll {len(fns)} ADCC-CP tests passed.")
