"""Aggregate raw results into per-method summaries, paired statistical tests
(Wilcoxon signed-rank + Holm-Bonferroni, bootstrap CIs, effect sizes), and the
shift-magnitude diagnostic law. Writes results/metrics.json and results/statistics.json.

Unit of analysis = one independent split, keyed by (dataset, seed, alpha). Methods are
compared paired on the same splits.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as sps

from ..utils import save_json, get_logger
from .tests import wilcoxon_paired, holm_bonferroni, bootstrap_ci, paired_bootstrap_diff_ci

log = get_logger()

PROPOSED = ["adecp", "weighted_ad"]
METRICS = ["marginal_coverage", "marginal_gap", "worst_stratum_coverage", "max_stratum_gap",
           "mean_width", "median_width", "saturated_fraction", "value_worst_coverage",
           "eff_sample_size"]


def _load(results_dir):
    return pd.read_csv(Path(results_dir) / "raw_results.csv")


def summarize_by_method(df, group_cols=("split_type", "method")):
    """Mean, sd, n and bootstrap 95% CI of each metric per group."""
    out = []
    for keys, g in df.groupby(list(group_cols)):
        rec = dict(zip(group_cols, keys if isinstance(keys, tuple) else (keys,)))
        rec["n"] = int(len(g))
        for m in METRICS:
            if m in g:
                vals = pd.to_numeric(g[m], errors="coerce").to_numpy()
                vals = vals[np.isfinite(vals)]
                if len(vals):
                    mean, lo, hi = bootstrap_ci(vals, n_boot=1000, seed=0)
                    rec[f"{m}_mean"] = round(float(np.mean(vals)), 4)
                    rec[f"{m}_sd"] = round(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0, 4)
                    rec[f"{m}_ci"] = [round(lo, 4), round(hi, 4)]
        out.append(rec)
    return out


def paired_tests(df, split_type, model=None, alpha=None, metric="worst_stratum_coverage",
                 higher_better=True):
    """Paired Wilcoxon of each PROPOSED method vs every other method on `metric`,
    pooled across (dataset, seed, alpha). Holm-corrected across the family."""
    sub = df[df.split_type == split_type].copy()
    if model is not None:
        sub = sub[sub.model == model]
    if alpha is not None:
        sub = sub[np.isclose(sub.alpha, alpha)]
    key = ["dataset", "seed", "alpha"]
    piv = sub.pivot_table(index=key, columns="method", values=metric, aggfunc="mean")
    methods = [m for m in piv.columns]
    results = []
    pvals = []
    comparisons = []
    for prop in PROPOSED:
        if prop not in piv:
            continue
        for base in methods:
            if base == prop:
                continue
            a = piv[prop].to_numpy(); b = piv[base].to_numpy()
            w = wilcoxon_paired(a, b)
            diff_mean, dlo, dhi = paired_bootstrap_diff_ci(a, b, n_boot=1000, seed=0)
            rec = {"proposed": prop, "baseline": base, "metric": metric,
                   "median_diff": w["median_diff"], "mean_diff": round(diff_mean, 4),
                   "diff_ci95": [round(dlo, 4), round(dhi, 4)],
                   "p_value": w["p_value"], "rank_biserial": w["rank_biserial"], "n_pairs": w["n"]}
            results.append(rec); pvals.append(w["p_value"])
            comparisons.append((prop, base))
    holm = holm_bonferroni(pvals)
    for r, h in zip(results, holm):
        r["p_holm"] = round(h["p_adj"], 5)
        r["significant_holm"] = bool(h["reject"] and (r["diff_ci95"][0] > 0 or r["diff_ci95"][1] < 0))
    return results


def diagnostic_law(df, methods=None):
    """Relationship between achievable coverage and shift magnitude (discriminator AUC).
    Spearman correlation of worst-stratum coverage vs shift_auc, per method and pooled."""
    d = df.dropna(subset=["shift_auc"]).copy()
    out = {}
    pool = d[d.method.isin(PROPOSED + ["split", "mondrian"])]
    for m, g in pool.groupby("method"):
        x = pd.to_numeric(g["shift_auc"], errors="coerce")
        y = pd.to_numeric(g["worst_stratum_coverage"], errors="coerce")
        ok = x.notna() & y.notna()
        if ok.sum() > 5:
            rho, p = sps.spearmanr(x[ok], y[ok])
            out[m] = {"spearman_rho": round(float(rho), 3), "p_value": float(p), "n": int(ok.sum())}
    # pooled split as the reference (coverage falls as shift grows)
    x = pd.to_numeric(d["shift_auc"], errors="coerce"); y = pd.to_numeric(d["marginal_coverage"], errors="coerce")
    ok = x.notna() & y.notna()
    rho, p = sps.spearmanr(x[ok], y[ok])
    out["_pooled_marginal_vs_auc"] = {"spearman_rho": round(float(rho), 3), "p_value": float(p), "n": int(ok.sum())}
    return out


def run_aggregation(cfg):
    rdir = Path(cfg["paths"]["results_dir"])
    df = _load(rdir)
    pm = cfg["primary_model"]
    metrics = {
        "by_split_method": summarize_by_method(df, ("split_type", "method")),
        "scaffold_primary_by_dataset_method":
            summarize_by_method(df[(df.split_type == "scaffold") & (df.model == pm)],
                                ("dataset", "method")),
        "temporal_by_dataset_method":
            summarize_by_method(df[df.split_type == "temporal"], ("dataset", "model", "method")),
        "by_model_method_scaffold":
            summarize_by_method(df[df.split_type == "scaffold"], ("model", "method")),
    }
    save_json(metrics, rdir / "metrics.json")

    statistics = {
        "scaffold_primary_worstcov":
            paired_tests(df, "scaffold", model=pm, metric="worst_stratum_coverage"),
        "scaffold_primary_marginal":
            paired_tests(df, "scaffold", model=pm, metric="marginal_coverage"),
        "scaffold_primary_width":
            paired_tests(df, "scaffold", model=pm, metric="mean_width"),
        "temporal_worstcov":
            paired_tests(df, "temporal", metric="worst_stratum_coverage"),
        "temporal_marginal":
            paired_tests(df, "temporal", metric="marginal_coverage"),
        "diagnostic_law": diagnostic_law(df),
    }
    save_json(statistics, rdir / "statistics.json")
    log.info(f"Aggregation done: metrics.json, statistics.json "
             f"({len(df)} rows, primary model={pm})")
    return metrics, statistics


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils import load_config
    run_aggregation(load_config("config/default.yaml"))
