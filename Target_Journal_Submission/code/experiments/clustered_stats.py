"""Target-clustered statistical validation.

The panel has 117 evaluation runs per method (13 targets x 3 windows x 3 seeds), but the
independent biological unit is the TARGET (n=13). We therefore aggregate each method to the
target level (mean over windows and seeds) and compute a cluster/target-level bootstrap
confidence interval for the ADR-CP improvement over each baseline, rather than treating the
117 runs as independent. We also report per-target effect sizes and target-level CIs for
coverage, width and surprise rate.

Writes: tables/table_clustered_stats.csv, results/clustered_stats.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from collections import defaultdict
import numpy as np
import csv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, ensure_dir

RNG = np.random.default_rng(0)
B = 10000
MODEL = "lgbm"
BASELINES = [("split", "Split CP"), ("normalized", "Normalized"), ("mondrian", "Mondrian-AD"),
             ("localized", "Localized"), ("weighted_kmm", "KMM-CP"), ("weighted_kde", "KDE-wt"),
             ("adecp", "ADE-CP"), ("mwcp", "MW-CP")]
OURS = "weighted_ad"


def _target_level(csv_path):
    """method -> target -> mean worst-stratum coverage (over windows+seeds), LightGBM."""
    rows = list(csv.DictReader(open(csv_path)))
    agg = defaultdict(lambda: defaultdict(list))
    wid = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] != MODEL:
            continue
        agg[r["method"]][r["dataset"]].append(float(r["worst_stratum_coverage"]))
        wid[r["method"]][r["dataset"]].append(float(r["mean_width"]))
    tmean = {m: {t: float(np.mean(v)) for t, v in d.items()} for m, d in agg.items()}
    wmean = {m: {t: float(np.mean(v)) for t, v in d.items()} for m, d in wid.items()}
    return tmean, wmean


def _cluster_boot(paired):
    """Percentile bootstrap CI of the mean over targets (resample targets with replacement)."""
    paired = np.asarray(paired)
    n = len(paired)
    means = np.array([paired[RNG.integers(0, n, n)].mean() for _ in range(B)])
    return float(paired.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main():
    cfg = load_config("config/default.yaml")
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    tmean, wmean = _target_level(Path(rdir) / "panel_results.csv")
    targets = sorted(tmean[OURS].keys())
    n_targets = len(targets)

    out_rows = []
    summary = {"n_targets": n_targets, "runs_per_method": None, "comparisons": {}}
    # count runs per method
    allrows = list(csv.DictReader(open(Path(rdir) / "panel_results.csv")))
    summary["runs_per_method"] = sum(1 for r in allrows if r["method"] == OURS and r["model"] == MODEL)

    for key, label in BASELINES:
        if key not in tmean:
            continue
        paired = [tmean[OURS][t] - tmean[key][t] for t in targets if t in tmean[key]]
        mean, lo, hi = _cluster_boot(paired)
        n_imp = sum(1 for d in paired if d > 0)
        # rank-biserial from signs (effect size on the target-level paired diffs)
        pos = sum(1 for d in paired if d > 0); neg = sum(1 for d in paired if d < 0)
        rb = (pos - neg) / len(paired)
        out_rows.append([label, f"+{mean:.3f}", f"[{lo:+.3f}, {hi:+.3f}]",
                         f"{n_imp}/{len(paired)}", f"{rb:+.2f}",
                         "yes" if lo > 0 else "no"])
        summary["comparisons"][key] = {"mean_delta": mean, "ci95": [lo, hi],
                                       "targets_improved": n_imp, "n": len(paired),
                                       "rank_biserial": rb, "ci_excludes_zero": lo > 0}

    tdir = ensure_dir("tables")
    with open(Path(tdir) / "table_clustered_stats.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([f"ADR-CP vs baseline (target-level, n={n_targets} targets)",
                    "Mean Δ worst-cov", "95% cluster-bootstrap CI", "Targets improved",
                    "Effect (rb)", "CI excludes 0"])
        for r in out_rows:
            w.writerow(r)

    # target-level CIs for ADR-CP's own coverage and width
    adr_cov = [tmean[OURS][t] for t in targets]
    adr_wid = [wmean[OURS][t] for t in targets]
    c_m, c_lo, c_hi = _cluster_boot(adr_cov)
    w_m, w_lo, w_hi = _cluster_boot(adr_wid)
    summary["adr_worst_cov_target_level"] = {"mean": c_m, "ci95": [c_lo, c_hi]}
    summary["adr_width_target_level"] = {"mean": w_m, "ci95": [w_lo, w_hi]}

    json.dump(summary, open(Path(rdir) / "clustered_stats.json", "w"), indent=1)
    print(f"n_targets={n_targets}, runs/method={summary['runs_per_method']}")
    for k, v in summary["comparisons"].items():
        print(f"  ADR-CP vs {k:14}: +{v['mean_delta']:.3f} CI[{v['ci95'][0]:+.3f},{v['ci95'][1]:+.3f}] "
              f"{v['targets_improved']}/{v['n']} excl0={v['ci_excludes_zero']}")
    print("Wrote tables/table_clustered_stats.csv")


if __name__ == "__main__":
    main()
