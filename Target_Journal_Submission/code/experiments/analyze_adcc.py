"""Round-6 analysis of the held-out ADCC-CP panel (results/panel_adcc_rows.jsonl) and the
validity controls (results/validity_adcc_rows.jsonl). Target-level (n=13) statistics:
cluster bootstrap CIs and Wilcoxon signed-rank tests (Holm). Writes
results/adcc_stats.json, tables/table_adcc_*.csv, figures/fig_adcc_*.{png,pdf}."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT.parent / "tables"; FIG = ROOT.parent / "figures"
NAMES = {"split": "Split CP", "normalized": "Normalized CP", "mondrian": "Mondrian-AD CP",
         "weighted_ad": "ADR-CP (1-D AD weights)", "weighted_kmm": "KMM-weighted CP",
         "mwcp": "MW-CP (stratified weights)", "adcc": "ADCC-CP (proposed)",
         "adcc_grp": "ADCC: indicator class", "adcc_pl": "ADCC: piecewise-linear class",
         "adcc_norm": "ADCC: normalized score", "adcc_sig": "ADCC: + sigma(x)"}
BASE = ["split", "normalized", "mondrian", "weighted_kmm", "weighted_ad", "mwcp"]
MET = ["marginal_coverage", "worst_stratum_coverage", "s0_coverage", "tail10_coverage",
       "mean_width", "saturated_fraction", "mean_abs_stratum_gap"]


def _bin(d, b):
    if isinstance(d, dict):
        return d.get(str(b), d.get(b))
    return d[b] if d is not None and len(d) > b else None


def load_panel():
    df = pd.read_json(ROOT / "results/panel_adcc_rows.jsonl", lines=True)
    df = df[df.method != "adcc_sig"]
    df["s0_coverage"] = df.ad_per_bin_coverage.apply(lambda d: _bin(d, 0))
    def gap(row):
        cov = row.ad_per_bin_coverage; n = row.ad_n_per_bin
        ks = list(cov.keys()) if isinstance(cov, dict) else range(len(cov))
        c = np.array([_bin(cov, k) for k in ks], float); m = np.array([_bin(n, k) for k in ks], float)
        ok = np.isfinite(c) & (m > 0)
        return float(np.sum(m[ok] * np.abs(c[ok] - 0.9)) / m[ok].sum())
    df["mean_abs_stratum_gap"] = df.apply(gap, axis=1)
    return df


def boot_ci(x, B=10000, seed=0):
    rng = np.random.default_rng(seed); x = np.asarray(x, float)
    bs = rng.choice(x, size=(B, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def holm(ps):
    ps = np.asarray(ps); o = np.argsort(ps); adj = np.empty_like(ps); m = len(ps); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * ps[i]); adj[i] = min(1.0, run)
    return adj


def main():
    TAB.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    df = load_panel()
    out = {"n_runs": int(df.groupby(["target", "model", "seed", "window"]).ngroups),
           "n_targets": int(df.target.nunique())}
    pooled = df.groupby("method")[MET].mean()
    out["pooled"] = pooled.round(4).to_dict(orient="index")
    order = BASE + ["adcc", "adcc_grp", "adcc_pl", "adcc_norm"]
    tp = pooled.reindex([m for m in order if m in pooled.index]).copy()
    tp.insert(0, "Method", [NAMES[m] for m in tp.index])
    tp.round(3).to_csv(TAB / "table_adcc_pooled.csv", index=False)
    # target-level
    T = df.groupby(["target", "method"])[MET].mean().reset_index()
    stats = {}
    rows = []
    for metric in ["worst_stratum_coverage", "s0_coverage", "tail10_coverage", "marginal_coverage",
                   "mean_abs_stratum_gap", "mean_width"]:
        piv = T.pivot(index="target", columns="method", values=metric)
        ps, recs = [], []
        for b in BASE:
            d = (piv["adcc"] - piv[b]).dropna()
            try:
                p = float(wilcoxon(d).pvalue)
            except ValueError:
                p = 1.0
            lo, hi = boot_ci(d.values)
            recs.append({"baseline": b, "mean_diff": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
                         "n_better": int((d > 0).sum()), "n": int(len(d)), "p": p})
            ps.append(p)
        for r, pa in zip(recs, holm(ps)):
            r["p_holm"] = float(pa)
        stats[metric] = recs
        if metric in ("s0_coverage", "worst_stratum_coverage", "mean_abs_stratum_gap", "mean_width"):
            for r in recs:
                rows.append({"Metric": metric, "Baseline": NAMES[r["baseline"]],
                             "ADCC − baseline (mean over 13 targets)": round(r["mean_diff"], 3),
                             "95% cluster-bootstrap CI": f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]",
                             "Targets ADCC higher": f"{r['n_better']}/{r['n']}",
                             "Holm p": f"{r['p_holm']:.3g}"})
    out["target_level"] = stats
    pd.DataFrame(rows).to_csv(TAB / "table_adcc_stats.csv", index=False)
    # per-target table (s0 coverage / width)
    pt = T[T.method.isin(["split", "weighted_ad", "mwcp", "adcc"])].pivot(index="target", columns="method",
                                                                          values=["s0_coverage", "mean_width"])
    pt.columns = [f"{a}:{NAMES[b]}" for a, b in pt.columns]
    pt.round(3).reset_index().to_csv(TAB / "table_adcc_per_target.csv", index=False)
    # by window and model
    out["by_window"] = df[df.method.isin(["split", "weighted_ad", "adcc"])].groupby(["window", "method"])[
        ["s0_coverage", "worst_stratum_coverage", "mean_width"]].mean().round(4).reset_index().to_dict(orient="records")
    out["by_model"] = df[df.method.isin(["split", "weighted_ad", "adcc"])].groupby(["model", "method"])[
        ["s0_coverage", "worst_stratum_coverage", "mean_width"]].mean().round(4).reset_index().to_dict(orient="records")
    # validity controls
    vp = ROOT / "results/validity_adcc_rows.jsonl"
    if vp.exists():
        V = pd.read_json(vp, lines=True)
        V["s0_coverage"] = V.ad_per_bin_coverage.apply(lambda d: _bin(d, 0))
        g = V.groupby(["setting", "method"])[["marginal_coverage", "worst_stratum_coverage", "s0_coverage",
                                               "tail10_coverage", "mean_width"]].mean().round(3)
        out["validity"] = g.reset_index().to_dict(orient="records")
        gg = g.reset_index(); gg["Method"] = gg.method.map(NAMES)
        gg[["setting", "Method", "marginal_coverage", "worst_stratum_coverage", "s0_coverage",
            "tail10_coverage", "mean_width"]].to_csv(TAB / "table_adcc_validity.csv", index=False)
    json.dump(out, open(ROOT / "results/adcc_stats.json", "w"), indent=1, default=float)
    figures(df, T)
    print(json.dumps({k: out[k] for k in ("n_runs", "n_targets")}))
    print(pooled.round(3).to_string())


def figures(df, T):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ms = ["split", "mondrian", "weighted_kmm", "weighted_ad", "mwcp", "adcc"]
    col = {"split": "#888888", "mondrian": "#56B4E9", "weighted_kmm": "#E69F00", "weighted_ad": "#009E73",
           "mwcp": "#CC79A7", "adcc": "#D55E00"}
    mk = {"split": "o", "mondrian": "s", "weighted_kmm": "^", "weighted_ad": "D", "mwcp": "v", "adcc": "*"}
    piv = T.pivot(index="target", columns="method", values="s0_coverage")
    tg = piv["split"].sort_values().index.tolist()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    for i, m in enumerate(ms):
        ax.scatter(piv.loc[tg, m], np.arange(len(tg)) + (i - 2.5) * 0.11, label=NAMES[m], c=col[m],
                   marker=mk[m], s=60 if m == "adcc" else 28, zorder=3 if m == "adcc" else 2, edgecolor="k", lw=0.3)
    ax.axvline(0.9, ls="--", c="k", lw=1); ax.set_yticks(range(len(tg))); ax.set_yticklabels([t.upper() for t in tg])
    ax.set_xlabel("Coverage in the most out-of-domain AD stratum (S0)"); ax.set_title("a  Per-target coverage (target 0.90)", loc="left")
    ax.legend(fontsize=7, loc="lower right")
    ax = axes[1]
    P = df.groupby("method")[["s0_coverage", "mean_width"]].mean()
    for m in ms:
        ax.scatter(P.loc[m, "mean_width"], P.loc[m, "s0_coverage"], c=col[m], marker=mk[m], s=120 if m == "adcc" else 60,
                   edgecolor="k", lw=0.4)
        ax.annotate(NAMES[m].split(" (")[0], (P.loc[m, "mean_width"], P.loc[m, "s0_coverage"]), fontsize=7,
                    xytext=(4, -9), textcoords="offset points")
    ax.axhline(0.9, ls="--", c="k", lw=1)
    ax.set_xlabel("Mean interval width (log units)"); ax.set_ylabel("S0 coverage")
    ax.set_title("b  Coverage–width trade-off (pooled)", loc="left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"fig_adcc_panel.{ext}", dpi=300)


if __name__ == "__main__":
    main()
