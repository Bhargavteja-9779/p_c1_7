#!/usr/bin/env python3
"""End-to-end reproduction entry point.

  python run_all.py --mode quick     # fast pipeline check (2 datasets, LightGBM, 3 seeds)
  python run_all.py --mode full      # full study (all datasets/models/seeds)
  python run_all.py --mode full --stage analysis   # re-run only aggregation+tables+figures

Stages: experiments -> aggregation (stats) -> tables -> figures.
All outputs land in results/, tables/, figures/. Experiments are resumable
(completed runs are skipped), so re-invoking continues an interrupted run.
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.utils import load_config, apply_quick_overrides, get_logger, detect_hardware

log = get_logger()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["quick", "full"], default="quick")
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--stage", choices=["all", "experiments", "analysis"], default="all")
    ap.add_argument("--which", default="scaffold,temporal,sweep")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.mode == "quick":
        cfg = apply_quick_overrides(cfg)
    log.info(f"Hardware: {detect_hardware()}")
    log.info(f"Mode={args.mode} stage={args.stage}")

    t0 = time.time()
    if args.stage in ("all", "experiments"):
        from experiments.run_experiments import run_all_experiments
        run_all_experiments(cfg, which=tuple(args.which.split(",")))
    if args.stage in ("all", "analysis"):
        from experiments.run_experiments import compile_csv
        compile_csv(cfg)
        from src.statistics.aggregate import run_aggregation
        run_aggregation(cfg)
        from src.visualization.tables import generate_all_tables
        generate_all_tables(cfg)
        from src.visualization.plots import generate_all_figures
        generate_all_figures(cfg)
    log.info(f"run_all complete in {time.time()-t0:.1f}s. See results/, tables/, figures/.")


if __name__ == "__main__":
    main()
