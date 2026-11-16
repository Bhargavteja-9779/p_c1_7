"""Experiment orchestrator. Writes machine-readable results incrementally to
results/ (resumable: completed runs are skipped on re-invocation).

Produces:
  results/raw_rows.jsonl      one JSON row per (method, dataset, model, seed, alpha, split, sweep_q)
  results/raw_results.csv     flat scalar table compiled from raw_rows.jsonl
  results/decision_rows.jsonl decision-utility records
  results/run_meta.jsonl      per-run metadata (shift AUC, sizes, runtime)
"""
from __future__ import annotations
import sys, json, itertools, argparse
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, apply_quick_overrides, get_logger, ensure_dir, detect_hardware, save_json
from src.data.datasets import load_dataset, dataset_summary

log = get_logger()

SCALAR_KEYS = ["method", "dataset", "model", "seed", "split_type", "alpha", "sweep_q",
               "marginal_coverage", "marginal_gap", "target", "mean_width", "median_width",
               "inf_fraction", "saturated_fraction", "worst_stratum_coverage",
               "max_stratum_gap", "value_worst_coverage", "value_max_gap",
               "eff_sample_size", "n_train", "n_calib", "n_test", "shift_auc", "ad_test_median"]


def _done_keys(path: Path):
    done = set()
    if path.exists():
        for line in open(path):
            try:
                r = json.loads(line)
                done.add((r["dataset"], r["model"], r["seed"], r["alpha"],
                          r["split_type"], r.get("sweep_q")))
            except Exception:
                pass
    return done


def _row_key(r):
    return (r["dataset"], r["model"], r["seed"], r["alpha"], r["split_type"], r.get("sweep_q"))


def run_all_experiments(cfg, which=("scaffold", "temporal", "sweep")):
    from src.pipeline import run_single
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    ensure_dir(Path(rdir) / "experiment_logs")
    raw_path = Path(rdir) / "raw_rows.jsonl"
    dec_path = Path(rdir) / "decision_rows.jsonl"
    meta_path = Path(rdir) / "run_meta.jsonl"
    done = _done_keys(meta_path)

    save_json(detect_hardware(), Path(rdir) / "hardware.json")

    def emit(meta, rows):
        with open(meta_path, "a") as f:
            f.write(json.dumps({k: meta.get(k) for k in
                     ["dataset", "model", "seed", "alpha", "split_type", "sweep_q",
                      "shift_auc", "n", "runtime_s"]}, default=float) + "\n")
        with open(raw_path, "a") as f:
            for r in rows:
                flat = {k: r.get(k) for k in SCALAR_KEYS}
                flat["ad_per_bin_coverage"] = json.dumps(r.get("ad_per_bin_coverage", {}))
                flat["ad_n_per_bin"] = json.dumps(r.get("ad_n_per_bin", {}))
                flat["value_per_bin_coverage"] = json.dumps(r.get("value_per_bin_coverage", {}))
                f.write(json.dumps(flat, default=float) + "\n")
                if "decision" in r:
                    for fr, d in r["decision"].items():
                        rec = {"dataset": r["dataset"], "model": r["model"], "seed": r["seed"],
                               "alpha": r["alpha"], "split_type": r["split_type"],
                               "sweep_q": r.get("sweep_q"), "method": r["method"], **d}
                        with open(dec_path, "a") as g:
                            g.write(json.dumps(rec, default=float) + "\n")

    # ---- scaffold main: primary model, all datasets/seeds/alphas ----
    if "scaffold" in which:
        pm = cfg["primary_model"]
        combos = list(itertools.product(cfg["scaffold_datasets"], [pm],
                                        cfg["seed_list"], cfg["alphas"]))
        # model-agnosticism ablation: other models, fewer seeds, primary alpha
        abl = list(itertools.product(cfg["scaffold_datasets"], cfg["ablation_models"],
                                     cfg["seed_list"][:cfg["ablation_seeds"]], [cfg["primary_alpha"]]))
        combos = combos + abl
        for di, (ds, model, seed, alpha) in enumerate(combos):
            if (ds, model, seed, alpha, "scaffold", None) in done:
                continue
            df = load_dataset(ds, cfg)
            meta, rows = run_single(df, cfg, ds, model, seed, "scaffold", alpha,
                                    decision_fracs=cfg["decision"]["select_fractions"])
            if rows:
                emit(meta, rows)
            log.info(f"[scaffold {di+1}/{len(combos)}] {ds}/{model}/s{seed}/a{alpha} "
                     f"auc={meta.get('shift_auc', float('nan')):.2f} t={meta.get('runtime_s')}s")

    # ---- temporal (held-out confirmation) ----
    if "temporal" in which:
        combos = list(itertools.product(cfg["temporal_datasets"], [cfg["primary_model"], "rf"],
                                        cfg["seed_list"][:5], cfg["alphas"]))
        for di, (ds, model, seed, alpha) in enumerate(combos):
            if (ds, model, seed, alpha, "temporal", None) in done:
                continue
            try:
                df = load_dataset(ds, cfg)
            except Exception as e:
                log.warning(f"temporal dataset {ds} unavailable: {e}")
                break
            meta, rows = run_single(df, cfg, ds, model, seed, "temporal", alpha,
                                    decision_fracs=cfg["decision"]["select_fractions"])
            if rows:
                emit(meta, rows)
            log.info(f"[temporal {di+1}/{len(combos)}] {ds}/{model}/s{seed}/a{alpha} "
                     f"auc={meta.get('shift_auc', float('nan')):.2f}")

    # ---- controlled similarity-shift sweep (diagnostic law) ----
    if "sweep" in which:
        sweep_ds = cfg.get("sweep_datasets", ["lipophilicity", "bace"])
        model = cfg["primary_model"]; alpha = cfg["primary_alpha"]
        combos = list(itertools.product(sweep_ds, cfg["seed_list"][:10],
                                        cfg["robustness"]["shift_sweep_quantiles"]))
        for di, (ds, seed, q) in enumerate(combos):
            if (ds, model, seed, alpha, "similarity", q) in done:
                continue
            df = load_dataset(ds, cfg)
            meta, rows = run_single(df, cfg, ds, model, seed, "similarity", alpha, sweep_q=q)
            if rows:
                emit(meta, rows)
            log.info(f"[sweep {di+1}/{len(combos)}] {ds} q={q} s{seed} "
                     f"auc={meta.get('shift_auc', float('nan')):.2f}")

    compile_csv(cfg)


def compile_csv(cfg):
    rdir = Path(cfg["paths"]["results_dir"])
    raw_path = rdir / "raw_rows.jsonl"
    if not raw_path.exists():
        return
    rows = [json.loads(l) for l in open(raw_path)]
    df = pd.DataFrame(rows)
    df.to_csv(rdir / "raw_results.csv", index=False)
    log.info(f"compiled {len(df)} rows -> raw_results.csv")
    # dataset summaries
    summ = {}
    for ds in set(cfg["scaffold_datasets"] + cfg["temporal_datasets"]):
        try:
            summ[ds] = dataset_summary(ds, load_dataset(ds, cfg))
        except Exception:
            pass
    save_json(summ, rdir / "dataset_summaries.json")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--mode", default="full", choices=["quick", "full"])
    ap.add_argument("--which", default="scaffold,temporal,sweep")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.mode == "quick":
        cfg = apply_quick_overrides(cfg)
    run_all_experiments(cfg, which=tuple(args.which.split(",")))
