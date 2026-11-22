"""Expanded multi-target temporal evaluation.
Runs every ChEMBL panel target over multiple chronological windows, for the primary
model (and RF for model-agnosticism), recording per-target rows. Resumable.
Writes results/panel_rows.jsonl and results/panel_decision.jsonl.
"""
from __future__ import annotations
import sys, json, itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger, ensure_dir
from src.data.datasets import load_panel_target, panel_summary
from src.pipeline import run_single

log = get_logger()

WINDOWS = {  # label -> (train, calib, test) fractions, chronological
    "w40": (0.50, 0.10, 0.40),
    "w30": (0.60, 0.10, 0.30),
    "w20": (0.70, 0.10, 0.20),
}
SCALARS = ["method", "dataset", "model", "seed", "split_type", "alpha", "window",
           "marginal_coverage", "marginal_gap", "worst_stratum_coverage", "max_stratum_gap",
           "mean_width", "median_width", "saturated_fraction", "value_worst_coverage",
           "eff_sample_size", "n_train", "n_calib", "n_test", "shift_auc", "ad_test_median"]


def _done(path):
    d = set()
    if Path(path).exists():
        for l in open(path):
            try:
                r = json.loads(l); d.add((r["dataset"], r["model"], r["seed"], r["window"]))
            except Exception:
                pass
    return d


def main():
    cfg = load_config("config/default.yaml")
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    meta_path = Path(rdir) / "panel_meta.jsonl"
    raw_path = Path(rdir) / "panel_rows.jsonl"
    dec_path = Path(rdir) / "panel_decision.jsonl"
    done = _done(meta_path)

    panel_summ = json.load(open(Path(rdir) / "panel_summaries.json"))
    targets = list(panel_summ.keys())
    models = [cfg["primary_model"], "rf"]
    seeds = [0, 1, 2]
    combos = list(itertools.product(targets, models, seeds, WINDOWS.items()))
    log.info(f"panel: {len(targets)} targets x {len(models)} models x {len(seeds)} seeds x {len(WINDOWS)} windows = {len(combos)} runs")
    for i, (key, model, seed, (wlabel, fr)) in enumerate(combos):
        ds = f"panel_{key}"
        if (ds, model, seed, wlabel) in done:
            continue
        df = load_panel_target(key, cfg)
        if len(df) < 800:
            continue
        meta, rows = run_single(df, cfg, ds, model, seed, "temporal", cfg["primary_alpha"],
                                fracs=fr, window=wlabel,
                                decision_fracs=cfg["decision"]["select_fractions"])
        if not rows:
            continue
        with open(meta_path, "a") as f:
            f.write(json.dumps({"dataset": ds, "model": model, "seed": seed, "window": wlabel,
                                "shift_auc": meta.get("shift_auc"), "n": meta.get("n")}, default=float) + "\n")
        with open(raw_path, "a") as f:
            for r in rows:
                f.write(json.dumps({k: r.get(k) for k in SCALARS}, default=float) + "\n")
                for fr_, d in (r.get("decision") or {}).items():
                    rec = {"dataset": ds, "model": model, "seed": seed, "window": wlabel,
                           "method": r["method"], **d}
                    with open(dec_path, "a") as g:
                        g.write(json.dumps(rec, default=float) + "\n")
        log.info(f"[panel {i+1}/{len(combos)}] {key}/{model}/s{seed}/{wlabel} "
                 f"auc={meta.get('shift_auc', float('nan')):.2f} n={meta.get('n')}")
    # compile
    import pandas as pd
    if raw_path.exists():
        pd.DataFrame([json.loads(l) for l in open(raw_path)]).to_csv(Path(rdir) / "panel_results.csv", index=False)
        log.info("compiled panel_results.csv")


if __name__ == "__main__":
    main()
