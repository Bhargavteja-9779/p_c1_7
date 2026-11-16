"""Statistical comparisons: paired Wilcoxon signed-rank, Holm-Bonferroni,
bootstrap CIs, rank-biserial effect size. Tests chosen for the design in
experimental_design.md (paired over independent splits; non-parametric)."""
from __future__ import annotations
import numpy as np
from scipy import stats


def wilcoxon_paired(a, b):
    """Paired Wilcoxon signed-rank on a-b. Returns statistic, p (two-sided),
    median difference, and rank-biserial effect size. NaN-safe."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    d = a - b
    out = {"n": int(len(d)), "median_diff": float(np.median(d)) if len(d) else float("nan")}
    nz = d[d != 0]
    if len(nz) < 1:
        out.update({"stat": float("nan"), "p_value": 1.0, "rank_biserial": 0.0})
        return out
    try:
        res = stats.wilcoxon(a, b, zero_method="wilcox", alternative="two-sided", mode="auto")
        stat, p = float(res.statistic), float(res.pvalue)
        # rank-biserial = (W+ - W-)/(W+ + W-)
        ranks = stats.rankdata(np.abs(nz))
        wp = ranks[nz > 0].sum(); wn = ranks[nz < 0].sum()
        rb = (wp - wn) / (wp + wn) if (wp + wn) > 0 else 0.0
        out.update({"stat": stat, "p_value": p, "rank_biserial": float(rb)})
    except Exception as e:
        out.update({"stat": float("nan"), "p_value": 1.0, "rank_biserial": 0.0, "error": str(e)})
    return out


def holm_bonferroni(pvals, alpha=0.05):
    """Holm-Bonferroni step-down. Returns list of (index, p, adjusted_p, reject)."""
    idx = list(range(len(pvals)))
    order = sorted(idx, key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    reject = [False] * m
    prev = 0.0
    for rank, i in enumerate(order):
        a = (m - rank) * pvals[i]
        a = min(1.0, max(a, prev))
        prev = a
        adj[i] = a
        reject[i] = a < alpha
    return [{"index": i, "p": float(pvals[i]), "p_adj": float(adj[i]), "reject": bool(reject[i])}
            for i in idx]


def bootstrap_ci(values, n_boot=2000, ci=0.95, seed=0, stat=np.mean):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    boots = np.array([stat(rng.choice(values, len(values), replace=True)) for _ in range(n_boot)])
    lo = np.percentile(boots, 100 * (1 - ci) / 2)
    hi = np.percentile(boots, 100 * (1 - (1 - ci) / 2))
    return (float(stat(values)), float(lo), float(hi))


def paired_bootstrap_diff_ci(a, b, n_boot=2000, ci=0.95, seed=0):
    """Bootstrap CI of the paired mean difference a-b over splits."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    d = a[m] - b[m]
    return bootstrap_ci(d, n_boot=n_boot, ci=ci, seed=seed, stat=np.mean)
