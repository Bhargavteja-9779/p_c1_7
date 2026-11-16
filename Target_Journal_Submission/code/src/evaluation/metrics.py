"""Coverage, conditional coverage, efficiency, and decision-utility metrics.
All operate on machine-readable arrays; nothing is hand-entered downstream."""
from __future__ import annotations
import numpy as np


def _finite(a):
    a = np.asarray(a, float)
    return a[np.isfinite(a)]


def coverage(y, lo, hi):
    y, lo, hi = map(lambda z: np.asarray(z, float), (y, lo, hi))
    return float(np.mean((y >= lo) & (y <= hi)))


def mean_width(lo, hi):
    w = np.asarray(hi, float) - np.asarray(lo, float)
    fin = _finite(w)
    return float(np.mean(fin)) if len(fin) else float("inf")


def median_width(lo, hi):
    w = np.asarray(hi, float) - np.asarray(lo, float)
    fin = _finite(w)
    return float(np.median(fin)) if len(fin) else float("inf")


def inf_fraction(lo, hi):
    w = np.asarray(hi, float) - np.asarray(lo, float)
    return float(np.mean(~np.isfinite(w)))


def conditional_coverage(y, lo, hi, bins):
    """Coverage within each stratum. Returns dict with per-bin coverage, the
    worst (minimum) stratum coverage, and the max absolute gap to `target` added
    by the caller."""
    y, lo, hi, bins = (np.asarray(z) for z in (y, lo, hi, bins))
    out = {}
    covs = {}
    for b in np.unique(bins):
        sel = bins == b
        if sel.sum() == 0:
            continue
        covs[int(b)] = coverage(y[sel], lo[sel], hi[sel])
    out["per_bin"] = covs
    out["worst"] = float(min(covs.values())) if covs else float("nan")
    out["n_per_bin"] = {int(b): int((bins == b).sum()) for b in np.unique(bins)}
    return out


def max_stratum_gap(cond, target):
    covs = cond.get("per_bin", {})
    if not covs:
        return float("nan")
    return float(max(abs(c - target) for c in covs.values()))


def value_quartile_bins(yhat, n=4):
    """Stratify test points by predicted value (activity strata, per Guo 2027)."""
    qs = np.linspace(0, 1, n + 1)[1:-1]
    edges = np.quantile(yhat, qs)
    return np.digitize(yhat, edges).astype(int)


def decision_utility(y, yhat, lo, hi, select_frac=0.1, maximize=True):
    """Risk-controlled screening: select the top `select_frac` candidates by predicted
    value. Report: surprise_rate = fraction of selected whose TRUE value falls outside
    the predicted interval (an unflagged failure); hit_rate = fraction of selected that
    are truly in the top `select_frac` by true value; base_rate = select_frac."""
    y, yhat, lo, hi = (np.asarray(z, float) for z in (y, yhat, lo, hi))
    n = len(y)
    k = max(1, int(round(select_frac * n)))
    order = np.argsort(-yhat if maximize else yhat)
    sel = order[:k]
    surprise = float(np.mean((y[sel] < lo[sel]) | (y[sel] > hi[sel])))
    thr = np.quantile(y, 1 - select_frac if maximize else select_frac)
    truly_top = (y >= thr) if maximize else (y <= thr)
    hit = float(np.mean(truly_top[sel]))
    return {"select_frac": select_frac, "k": k, "surprise_rate": surprise,
            "hit_rate": hit, "base_rate": float(select_frac)}


def effective_sample_size(w):
    w = np.asarray(w, float)
    s1, s2 = w.sum(), (w ** 2).sum()
    return float(s1 * s1 / s2) if s2 > 0 else 0.0


def saturated_fraction(lo, hi, span, tol=0.999):
    """Fraction of intervals that hit the trivial (full training-range) width —
    these 'cover' trivially and must be counted against efficiency, not rewarded."""
    w = np.asarray(hi, float) - np.asarray(lo, float)
    if not np.isfinite(span) or span <= 0:
        return float(np.mean(~np.isfinite(w)))
    return float(np.mean(w >= tol * span))


def summarize(name, y, lo, hi, test_bin, level, yhat=None, value_bins=None,
              w_test=None, extra=None, span=None):
    target = level
    cond = conditional_coverage(y, lo, hi, test_bin)
    row = {
        "method": name,
        "marginal_coverage": coverage(y, lo, hi),
        "target": target,
        "marginal_gap": coverage(y, lo, hi) - target,
        "mean_width": mean_width(lo, hi),
        "median_width": median_width(lo, hi),
        "inf_fraction": inf_fraction(lo, hi),
        "worst_stratum_coverage": cond["worst"],
        "max_stratum_gap": max_stratum_gap(cond, target),
        "ad_per_bin_coverage": cond["per_bin"],
        "ad_n_per_bin": cond["n_per_bin"],
    }
    if span is not None:
        row["saturated_fraction"] = saturated_fraction(lo, hi, span)
    if value_bins is not None:
        vcond = conditional_coverage(y, lo, hi, value_bins)
        row["value_worst_coverage"] = vcond["worst"]
        row["value_max_gap"] = max_stratum_gap(vcond, target)
        row["value_per_bin_coverage"] = vcond["per_bin"]
    if w_test is not None:
        row["eff_sample_size"] = effective_sample_size(w_test)
    if extra:
        row.update(extra)
    return row
