"""Publication figures generated from machine-readable results.
Palette: Okabe-Ito (colorblind-safe by construction). No dual axes; legends present;
sequential ramp for stratum heatmaps. Every figure traces to raw_results.csv / *.json.
Saves both .png (600 dpi) and .pdf (vector) to figures/.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..utils import get_logger

log = get_logger()

# Okabe-Ito colorblind-safe categorical palette (fixed order, never cycled)
OI = {"black": "#000000", "orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73",
      "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7"}
METHOD_COLOR = {
    "split": OI["black"], "normalized": "#777777", "mondrian": OI["skyblue"],
    "localized": OI["yellow"], "weighted_disc": OI["orange"], "weighted_logistic": OI["purple"],
    "weighted_kde": "#B07AA1", "weighted_kmm": "#7F7F7F", "weighted_ad": OI["blue"], "adwcp": OI["vermillion"],
    "adecp": OI["green"], "raw_ensemble": "#BBBBBB"}
METHOD_LABEL = {
    "split": "Split CP", "normalized": "Normalized CP", "mondrian": "Mondrian-AD CP",
    "localized": "Localized CP", "weighted_disc": "Weighted (FP disc.)",
    "weighted_logistic": "Weighted (logistic)", "weighted_kde": "Weighted (KDE)",
    "weighted_ad": "ADR-CP (ours)", "weighted_kmm": "KMM-CP (weighting)", "adwcp": "AD-strat. weighted", "adecp": "ADE-CP (ours)",
    "raw_ensemble": "Raw ensemble"}

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
                     "figure.dpi": 120, "savefig.bbox": "tight", "font.family": "DejaVu Sans"})


def _save(fig, outdir, name):
    for ext in ("png", "pdf"):
        fig.savefig(Path(outdir) / f"{name}.{ext}", dpi=600 if ext == "png" else None)
    plt.close(fig)


def fig_coverage_vs_shift(raw, outdir):
    """Diagnostic law: worst-stratum coverage vs discriminator AUC (shift magnitude)."""
    d = raw.dropna(subset=["shift_auc"]).copy()
    d = d[np.isclose(d.alpha, 0.1)]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    for m in ["split", "mondrian", "weighted_ad", "adecp"]:
        g = d[d.method == m]
        if g.empty:
            continue
        x = pd.to_numeric(g.shift_auc); y = pd.to_numeric(g.worst_stratum_coverage)
        # bin by AUC for a trend line
        bins = np.linspace(0.5, 1.0, 11)
        idx = np.digitize(x, bins)
        bx, by = [], []
        for b in range(1, len(bins)):
            sel = idx == b
            if sel.sum() >= 3:
                bx.append((bins[b-1]+bins[b])/2); by.append(y[sel].mean())
        ax.scatter(x, y, s=9, color=METHOD_COLOR[m], alpha=0.25, edgecolors="none")
        if bx:
            ax.plot(bx, by, "-o", color=METHOD_COLOR[m], lw=2, ms=5, label=METHOD_LABEL[m])
    ax.axhline(0.9, ls="--", color="0.3", lw=1)
    ax.text(0.52, 0.905, "nominal 0.90", fontsize=8, color="0.3")
    ax.set_xlabel("Shift magnitude  (train-vs-pool discriminator AUC)")
    ax.set_ylabel("Worst-stratum coverage")
    ax.set_ylim(0.3, 1.02)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title("Achievable conditional coverage falls as chemical shift grows", fontsize=9.5)
    _save(fig, outdir, "fig_diagnostic_coverage_vs_shift")


def fig_coverage_by_stratum(raw, outdir, dataset, model, split_type="scaffold"):
    """Per-AD-stratum coverage for each method (bin 0 = most out-of-domain)."""
    d = raw[(raw.dataset == dataset) & (raw.model == model) & (raw.split_type == split_type)
            & np.isclose(raw.alpha, 0.1)]
    if d.empty:
        return
    methods = ["split", "mondrian", "weighted_ad", "adecp"]
    perbin = {m: {} for m in methods}
    for _, r in d.iterrows():
        if r.method not in methods:
            continue
        try:
            pb = json.loads(r["ad_per_bin_coverage"])
        except Exception:
            continue
        for b, c in pb.items():
            perbin[r.method].setdefault(int(b), []).append(c)
    nb = max((max(v.keys()) for v in perbin.values() if v), default=0) + 1
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    width = 0.8 / len(methods)
    xs = np.arange(nb)
    for i, m in enumerate(methods):
        means = [np.mean(perbin[m].get(b, [np.nan])) for b in range(nb)]
        ax.bar(xs + i*width, means, width=width*0.92, color=METHOD_COLOR[m],
               label=METHOD_LABEL[m], edgecolor="white", linewidth=0.5)
    ax.axhline(0.9, ls="--", color="0.3", lw=1)
    ax.set_xticks(xs + 0.4 - width/2)
    ax.set_xticklabels([f"S{b}\n{'(far)' if b==0 else '(near)' if b==nb-1 else ''}" for b in range(nb)])
    ax.set_xlabel("Applicability-domain stratum (S0 = most out-of-domain)")
    ax.set_ylabel("Coverage")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="lower right")
    ax.set_title(f"Per-stratum coverage — {dataset} ({model}, {split_type})", fontsize=9.5)
    _save(fig, outdir, f"fig_stratum_coverage_{dataset}_{model}")


def fig_coverage_width_pareto(raw, outdir, split_type="temporal"):
    """Coverage-restoration vs efficiency trade-off: worst coverage (x) vs mean width (y)."""
    d = raw[(raw.split_type == split_type) & np.isclose(raw.alpha, 0.1)]
    if d.empty:
        return
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    for m in METHOD_COLOR:
        g = d[d.method == m]
        if g.empty:
            continue
        wc = pd.to_numeric(g.worst_stratum_coverage).mean()
        mw = pd.to_numeric(g.mean_width).mean()
        sat = pd.to_numeric(g.saturated_fraction).mean()
        mk = "X" if sat > 0.2 else "o"
        ax.scatter(wc, mw, s=70, color=METHOD_COLOR[m], marker=mk, edgecolors="white", zorder=3)
        ax.annotate(METHOD_LABEL[m], (wc, mw), fontsize=7.5, xytext=(4, 3),
                    textcoords="offset points")
    ax.axvline(0.9, ls="--", color="0.3", lw=1)
    ax.text(0.9, ax.get_ylim()[1]*0.97, "nominal", fontsize=8, color="0.3", rotation=90, va="top")
    ax.set_xlabel("Worst-stratum coverage  (→ better)")
    ax.set_ylabel("Mean interval width  (↓ better)")
    ax.set_title(f"Coverage–efficiency trade-off ({split_type} shift)\n(× = >20% intervals saturated)",
                 fontsize=9.5)
    _save(fig, outdir, f"fig_pareto_{split_type}")


def fig_decision_utility(cfg, outdir):
    """Screening 'surprise rate' (true value outside predicted interval among selected)
    vs interval width, by method, on temporal data."""
    dec_path = Path(cfg["paths"]["results_dir"]) / "decision_rows.jsonl"
    raw = pd.read_csv(Path(cfg["paths"]["results_dir"]) / "raw_results.csv")
    if not dec_path.exists():
        return
    dec = pd.DataFrame([json.loads(l) for l in open(dec_path)])
    dec = dec[(dec.split_type == "temporal") & np.isclose(dec.select_frac, 0.1)]
    if dec.empty:
        return
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    for m in ["split", "mondrian", "weighted_ad", "adecp"]:
        g = dec[dec.method == m]
        if g.empty:
            continue
        sr = g.surprise_rate.mean()
        w = raw[(raw.split_type == "temporal") & (raw.method == m) & np.isclose(raw.alpha, 0.1)]
        mw = pd.to_numeric(w.mean_width).mean() if not w.empty else np.nan
        ax.scatter(mw, sr, s=70, color=METHOD_COLOR[m], label=METHOD_LABEL[m], edgecolors="white", zorder=3)
        ax.annotate(METHOD_LABEL[m], (mw, sr), fontsize=7.5, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Mean interval width")
    ax.set_ylabel("Surprise rate among top-10% selected")
    ax.set_title("Screening reliability: fewer surprises, controlled width", fontsize=9.5)
    _save(fig, outdir, "fig_decision_utility")


def fig_main_bars(raw, outdir, model, split_type="scaffold"):
    """Marginal & worst-stratum coverage per method (pooled over datasets/seeds)."""
    d = raw[(raw.model == model) & (raw.split_type == split_type) & np.isclose(raw.alpha, 0.1)]
    if d.empty:
        return
    order = ["split", "normalized", "mondrian", "localized", "weighted_disc",
             "weighted_logistic", "weighted_kde", "weighted_ad", "adwcp", "adecp"]
    order = [m for m in order if m in set(d.method)]
    marg = [pd.to_numeric(d[d.method == m].marginal_coverage).mean() for m in order]
    worst = [pd.to_numeric(d[d.method == m].worst_stratum_coverage).mean() for m in order]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    x = np.arange(len(order)); w = 0.38
    ax.bar(x - w/2, marg, w, color=OI["skyblue"], label="Marginal coverage", edgecolor="white")
    ax.bar(x + w/2, worst, w, color=OI["vermillion"], label="Worst-stratum coverage", edgecolor="white")
    ax.axhline(0.9, ls="--", color="0.3", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([METHOD_LABEL[m] for m in order], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Coverage"); ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title(f"Marginal vs conditional coverage ({split_type} shift, {model})", fontsize=9.5)
    _save(fig, outdir, f"fig_main_bars_{split_type}_{model}")


def generate_all_figures(cfg):
    outdir = Path(cfg["paths"]["figures_dir"]); outdir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(Path(cfg["paths"]["results_dir"]) / "raw_results.csv")
    pm = cfg["primary_model"]
    fig_coverage_vs_shift(raw, outdir)
    fig_coverage_width_pareto(raw, outdir, "temporal")
    fig_coverage_width_pareto(raw, outdir, "scaffold")
    fig_main_bars(raw, outdir, pm, "scaffold")
    fig_decision_utility(cfg, outdir)
    for ds in ["lipophilicity", "bace"]:
        fig_coverage_by_stratum(raw, outdir, ds, pm)
    for ds in cfg["temporal_datasets"]:
        fig_coverage_by_stratum(raw, outdir, ds, "lgbm", "temporal")
    log.info(f"figures -> {outdir}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils import load_config
    generate_all_figures(load_config("config/default.yaml"))
