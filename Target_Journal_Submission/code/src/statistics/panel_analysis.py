"""Analysis of the expanded multi-target temporal panel (Priority 4).
Per-target and pooled coverage, paired statistics (MW-CP vs each baseline), and the
per-target forest figure. Reads results/panel_results.csv.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ..utils import save_json, get_logger
from .tests import wilcoxon_paired, holm_bonferroni, paired_bootstrap_diff_ci

log = get_logger()

METHODS = ["split", "normalized", "mondrian", "localized", "weighted_ad", "weighted_kmm",
           "weighted_kde", "adecp", "mwcp"]
PROPOSED = "mwcp"
LABELS = {"split": "Split", "normalized": "Normalized", "mondrian": "Mondrian-AD",
          "localized": "Localized", "weighted_ad": "ADR-CP", "weighted_kmm": "KMM",
          "weighted_kde": "KDE-wt", "adecp": "ADE-CP", "mwcp": "MW-CP"}


def panel_tables_and_stats(cfg):
    rdir = Path(cfg["paths"]["results_dir"])
    csv = rdir / "panel_results.csv"
    if not csv.exists():
        log.warning("panel_results.csv missing"); return None
    d = pd.read_csv(csv)
    d = d[d.model == "lgbm"]
    tgt = sorted(d.dataset.unique())

    # per-target pooled (over windows, seeds) worst-stratum coverage
    rows = []
    for t in tgt:
        g = d[d.dataset == t]
        rec = {"target": t.replace("panel_", ""), "shift_auc": round(g.shift_auc.mean(), 2)}
        for m in METHODS:
            rec[LABELS[m]] = round(g[g.method == m].worst_stratum_coverage.mean(), 3)
        rows.append(rec)
    tab = pd.DataFrame(rows).sort_values("shift_auc")
    (rdir / "..").resolve()
    tabdir = Path(cfg["paths"]["tables_dir"]); tabdir.mkdir(parents=True, exist_ok=True)
    tab.to_csv(tabdir / "table_panel_per_target.csv", index=False)

    # paired stats: MW-CP vs each baseline over (target,window,seed)
    key = ["dataset", "window", "seed"]
    piv = d.pivot_table(index=key, columns="method", values="worst_stratum_coverage")
    stats, pvals = [], []
    for base in METHODS:
        if base == PROPOSED or base not in piv or PROPOSED not in piv:
            continue
        a, b = piv[PROPOSED].to_numpy(), piv[base].to_numpy()
        w = wilcoxon_paired(a, b)
        mdiff, lo, hi = paired_bootstrap_diff_ci(a, b, n_boot=2000, seed=0)
        stats.append({"baseline": base, "label": LABELS[base], "median_diff": w["median_diff"],
                      "mean_diff": round(mdiff, 4), "ci95": [round(lo, 4), round(hi, 4)],
                      "p": w["p_value"], "rank_biserial": w["rank_biserial"], "n": w["n"]})
        pvals.append(w["p_value"])
    for r, h in zip(stats, holm_bonferroni(pvals)):
        r["p_holm"] = round(h["p_adj"], 5)
        r["significant"] = bool(h["reject"] and (r["ci95"][0] > 0 or r["ci95"][1] < 0))

    # pooled coverage/width per method
    pooled = []
    for m in METHODS:
        g = d[d.method == m]
        pooled.append({"method": LABELS[m],
                       "marginal": round(g.marginal_coverage.mean(), 3),
                       "worst_stratum": round(g.worst_stratum_coverage.mean(), 3),
                       "mean_width": round(g.mean_width.mean(), 3),
                       "saturated": round(g.saturated_fraction.mean(), 3)})
    pd.DataFrame(pooled).to_csv(tabdir / "table_panel_pooled.csv", index=False)

    out = {"n_targets": len(tgt), "pooled": pooled, "mwcp_vs_baselines": stats,
           "per_target": tab.to_dict(orient="records")}
    save_json(out, rdir / "panel_stats.json")
    log.info(f"panel analysis: {len(tgt)} targets; MW-CP pooled worst="
             f"{d[d.method==PROPOSED].worst_stratum_coverage.mean():.3f}, "
             f"split={d[d.method=='split'].worst_stratum_coverage.mean():.3f}")
    return out


def fig_panel_forest(cfg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rdir = Path(cfg["paths"]["results_dir"])
    d = pd.read_csv(rdir / "panel_results.csv")
    d = d[d.model == "lgbm"]
    tgt = (d.groupby("dataset").shift_auc.mean().sort_values().index.tolist())
    fig, ax = plt.subplots(figsize=(6.4, max(3.5, 0.42 * len(tgt))))
    yy = np.arange(len(tgt))
    for m, col, mk in [("split", "#000000", "o"), ("mondrian", "#56B4E9", "s"),
                       ("weighted_kmm", "#CC79A7", "^"), ("mwcp", "#009E73", "D")]:
        xs = [d[(d.dataset == t) & (d.method == m)].worst_stratum_coverage.mean() for t in tgt]
        ax.scatter(xs, yy, s=34, color=col, marker=mk, label=LABELS[m], zorder=3, edgecolors="white", linewidths=0.4)
    ax.axvline(0.9, ls="--", color="0.3", lw=1)
    ax.set_yticks(yy)
    ax.set_yticklabels([t.replace("panel_", "") + f"  (AUC {d[d.dataset==t].shift_auc.mean():.2f})" for t in tgt], fontsize=8)
    ax.set_xlabel("Worst-stratum coverage (temporal shift; target 0.90)")
    ax.set_xlim(0.4, 1.02)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.set_title("Per-target conditional coverage across the temporal panel", fontsize=9.5, pad=22)
    figdir = Path(cfg["paths"]["figures_dir"]); figdir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(figdir / f"fig_panel_forest.{ext}", dpi=600 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)
    log.info("panel forest figure saved")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils import load_config
    cfg = load_config("config/default.yaml")
    panel_tables_and_stats(cfg); fig_panel_forest(cfg)
