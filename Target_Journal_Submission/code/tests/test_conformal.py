"""Unit tests for conformal correctness and weighting. Run: python -m pytest tests/
or `python tests/test_conformal.py`. No network; uses synthetic data."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.conformal.weighting import (weighted_quantile_threshold, unweighted_quantile_threshold,
                                      DensityRatioWeights)


def test_unweighted_equals_split_marginal_coverage():
    """Split conformal achieves >= nominal coverage on exchangeable data."""
    rng = np.random.default_rng(0)
    covs = []
    for _ in range(200):
        s = np.abs(rng.normal(size=500))
        q = unweighted_quantile_threshold(s, 0.9)
        test = np.abs(rng.normal(size=2000))
        covs.append(np.mean(test <= q))
    assert abs(np.mean(covs) - 0.9) < 0.02, np.mean(covs)


def test_weighted_equals_unweighted_when_uniform():
    """Uniform weights -> weighted threshold matches the unweighted (n+1) quantile."""
    rng = np.random.default_rng(1)
    s = np.abs(rng.normal(size=300))
    qu = unweighted_quantile_threshold(s, 0.9)
    qw = weighted_quantile_threshold(s, np.ones_like(s), 1.0, 0.9)
    assert abs(qu - qw) < 1e-9, (qu, qw)


def test_weighted_quantile_monotone_in_level():
    rng = np.random.default_rng(2)
    s = np.abs(rng.normal(size=400)); w = rng.uniform(0.5, 2, size=400)
    q80 = weighted_quantile_threshold(s, w, 1.0, 0.8)
    q95 = weighted_quantile_threshold(s, w, 1.0, 0.95)
    assert q95 >= q80


def test_weighted_quantile_infinite_when_unreachable():
    s = np.array([1.0, 2.0, 3.0])
    # huge test atom -> cannot reach high level -> +inf
    q = weighted_quantile_threshold(s, np.ones(3), 1e6, 0.9)
    assert not np.isfinite(q)


def test_weighted_cp_restores_coverage_under_known_shift():
    """On a controlled covariate shift with a KNOWN density ratio, weighted CP restores
    coverage better than unweighted split CP. Gaussian location shift."""
    rng = np.random.default_rng(3)
    # train/calib X ~ N(0,1); test X ~ N(1,1). y = 2x + noise; residual scale grows with |x|.
    def gen(n, mu):
        x = rng.normal(mu, 1.0, size=n)
        resid = np.abs(rng.normal(0, 0.5 + 0.5 * np.abs(x)))
        return x, resid
    xc, sc = gen(2000, 0.0)
    xt, st = gen(5000, 1.5)
    # true density ratio N(1.5,1)/N(0,1)
    def ratio(x):
        from scipy.stats import norm
        return norm.pdf(x, 1.5, 1) / norm.pdf(x, 0, 1)
    wc = ratio(xc)
    # unweighted
    qu = unweighted_quantile_threshold(sc, 0.9)
    cov_unw = np.mean(st <= qu)
    # weighted (per test point weight)
    wt = ratio(xt)
    cov_w = np.mean([st[i] <= weighted_quantile_threshold(sc, wc, wt[i], 0.9)
                     for i in range(0, 1000)])  # subsample for speed
    # weighted should be closer to 0.9 than unweighted (which under-covers)
    assert abs(cov_w - 0.9) < abs(cov_unw - 0.9) + 1e-6, (cov_unw, cov_w)
    assert cov_unw < 0.9  # unweighted under-covers under this shift


def test_density_ratio_weights_finite_and_capped():
    rng = np.random.default_rng(4)
    Xtr = rng.normal(0, 1, size=(400, 50)); Xpo = rng.normal(0.5, 1, size=(400, 50))
    dr = DensityRatioWeights(kind="logistic", cap=50, seed=0, pca_dim=16).fit(Xtr, Xpo)
    w = dr.weights(Xpo)
    assert np.all(np.isfinite(w)) and w.max() <= 50 + 1e-6 and w.min() >= 1/50 - 1e-6


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\nAll {len(fns)} conformal tests passed.")
