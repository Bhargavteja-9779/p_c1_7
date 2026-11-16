"""Generate publication tables (CSV + Markdown) from machine-readable results.
Nothing is hand-entered; every number traces to results/*.json / raw_results.csv."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ..utils import get_logger
from ..data.datasets import DATASET_META

log = get_logger()

METHOD_LABELS = {
    "raw_ensemble": "Raw ensemble (B0)", "split": "Split CP (B1)",
    "normalized": "Normalized CP (B2)", "mondrian": "Mondrian-AD CP (B3)",
    "localized": "Localized CP (B4)", "weighted_disc": "Weighted CP, FP discriminator (B5)",
    "weighted_ad": "AD-reweighted CP [ADR-CP, ours]", "weighted_logistic": "Weighted CP, logistic (CoDrug-style)",
    "weighted_kde": "Weighted CP, KDE (CoDrug-style)", "adwcp": "AD-stratified weighted CP",
    "adecp": "AD-extrapolated CP [ADE-CP, ours]"}
METHOD_ORDER = ["raw_ensemble", "split", "normalized", "mondrian", "localized",
                "weighted_disc", "weighted_logistic", "weighted_kde", "weighted_ad", "adwcp", "adecp"]


def _fmt(mean, sd=None, p=3):
    if mean is None or (isinstance(mean, float) and not np.isfinite(mean)):
        return "--"
    s = f"{mean:.{p}f}"
    if sd is not None and np.isfinite(sd):
        s += f"$\\pm${sd:.{p}f}"
    return s


def _df_to_md(df, path_md):
    with open(path_md, "w") as f:
        f.write("| " + " | ".join(df.columns) + " |\n")
        f.write("|" + "|".join(["---"] * len(df.columns)) + "|\n")
        for _, r in df.iterrows():
            f.write("| " + " | ".join(str(x) for x in r.values) + " |\n")


def table_dataset_summary(cfg, outdir):
    summ_path = Path(cfg["paths"]["results_dir"]) / "dataset_summaries.json"
    rows = []
    if summ_path.exists():
        summ = json.load(open(summ_path))
        for k, s in summ.items():
            rows.append({"Dataset": s["name"], "Endpoint/unit": s["unit"], "Shift": s["shift"],
                         "N": s["n"], "#Scaffolds": s["n_scaffolds"],
                         "y range": f"[{s['y_min']:.2f}, {s['y_max']:.2f}]",
                         "Years": f"{s.get('year_min','-')}-{s.get('year_max','-')}" if "year_min" in s else "--"})
    df = pd.DataFrame(rows)
    df.to_csv(Path(outdir) / "table1_datasets.csv", index=False)
    _df_to_md(df, Path(outdir) / "table1_datasets.md")
    return df


def _method_summary_table(raw, outdir, name, split_type, model=None, alphas=None, caption=""):
    d = raw[raw.split_type == split_type].copy()
    if model is not None:
        d = d[d.model == model]
    if alphas is not None:
        d = d[d.alpha.isin(alphas)]
    rows = []
    for m in METHOD_ORDER:
        g = d[d.method == m]
        if g.empty:
            continue
        def ms(col):
            v = pd.to_numeric(g[col], errors="coerce"); v = v[np.isfinite(v)]
            return (v.mean(), v.std(ddof=1) if len(v) > 1 else 0.0) if len(v) else (None, None)
        mc = ms("marginal_coverage"); wc = ms("worst_stratum_coverage")
        mw = ms("mean_width"); sat = ms("saturated_fraction")
        rows.append({"Method": METHOD_LABELS.get(m, m),
                     "Marginal cov.": _fmt(*mc), "Worst-stratum cov.": _fmt(*wc),
                     "Mean width": _fmt(*mw, p=2), "Saturated frac.": _fmt(*sat, p=2),
                     "n": len(g)})
    df = pd.DataFrame(rows)
    df.to_csv(Path(outdir) / f"{name}.csv", index=False)
    _df_to_md(df, Path(outdir) / f"{name}.md")
    return df


def table_stats(cfg, outdir, key="temporal_worstcov", name="table_stats_temporal"):
    stat_path = Path(cfg["paths"]["results_dir"]) / "statistics.json"
    if not stat_path.exists():
        return None
    stats = json.load(open(stat_path))
    recs = stats.get(key, [])
    rows = []
    for r in recs:
        rows.append({"Proposed": METHOD_LABELS.get(r["proposed"], r["proposed"]),
                     "vs Baseline": METHOD_LABELS.get(r["baseline"], r["baseline"]),
                     "Median Δ": _fmt(r["median_diff"], p=3),
                     "Mean Δ [95% CI]": f"{r['mean_diff']:.3f} [{r['diff_ci95'][0]:.3f}, {r['diff_ci95'][1]:.3f}]",
                     "p (Holm)": f"{r['p_holm']:.4f}", "Effect (rb)": f"{r['rank_biserial']:.2f}",
                     "Sig.": "yes" if r["significant_holm"] else "no"})
    df = pd.DataFrame(rows)
    df.to_csv(Path(outdir) / f"{name}.csv", index=False)
    _df_to_md(df, Path(outdir) / f"{name}.md")
    return df


def table_by_model(cfg, outdir):
    raw = pd.read_csv(Path(cfg["paths"]["results_dir"]) / "raw_results.csv")
    d = raw[raw.split_type == "scaffold"]
    rows = []
    for model in ["lgbm", "rf", "ridge", "mlp"]:
        gm = d[d.model == model]
        if gm.empty:
            continue
        for m in ["split", "mondrian", "weighted_ad", "adecp"]:
            g = gm[gm.method == m]
            if g.empty:
                continue
            wc = pd.to_numeric(g["worst_stratum_coverage"], errors="coerce")
            rows.append({"Model": model, "Method": METHOD_LABELS.get(m, m),
                         "Worst-stratum cov.": _fmt(wc.mean(), wc.std(ddof=1))})
    df = pd.DataFrame(rows)
    df.to_csv(Path(outdir) / "table_by_model.csv", index=False)
    _df_to_md(df, Path(outdir) / "table_by_model.md")
    return df


def generate_all_tables(cfg):
    outdir = Path(cfg["paths"]["tables_dir"]); outdir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(Path(cfg["paths"]["results_dir"]) / "raw_results.csv")
    pm = cfg["primary_model"]
    table_dataset_summary(cfg, outdir)
    _method_summary_table(raw, outdir, "table2_main_scaffold", "scaffold", model=pm,
                          alphas=[0.1], caption="Scaffold shift, primary model, 90% intervals")
    _method_summary_table(raw, outdir, "table3_temporal", "temporal", alphas=[0.1],
                          caption="Temporal shift, 90% intervals")
    table_stats(cfg, outdir, "temporal_worstcov", "table4_stats_temporal")
    table_stats(cfg, outdir, "scaffold_primary_worstcov", "table5_stats_scaffold")
    table_by_model(cfg, outdir)
    log.info(f"tables -> {outdir}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils import load_config
    generate_all_tables(load_config("config/default.yaml"))
