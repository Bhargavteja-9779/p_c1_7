"""Representation-robustness ablation (E5): do the conclusions hold under an alternative
molecular fingerprint (FCFP4, functional-class) as well as ECFP4? Runs key methods on two
scaffold datasets and two temporal panel targets under both representations.
Writes results/representation_ablation.csv.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger
from src.data.datasets import load_dataset, load_panel_target
from src.preprocessing import features as F
import src.pipeline as P
from src.pipeline import run_single

log = get_logger()
METHODS = ["split", "mondrian", "weighted_ad", "mwcp", "adecp"]


def main():
    cfg = load_config("config/default.yaml")
    cfg["conformal_methods"] = METHODS
    rows = []
    specs = [("esol", "scaffold", None), ("bace", "scaffold", None),
             ("panel_egfr", "temporal", (0.6, 0.1, 0.3)), ("panel_cox2", "temporal", (0.6, 0.1, 0.3))]
    for variant, use_feat in [("ECFP4", False), ("FCFP4", True)]:
        F.set_fp_variant(use_feat)
        P._FEATURE_CACHE.clear()
        for ds, split, fr in specs:
            if ds.startswith("panel_"):
                df = load_panel_target(ds.replace("panel_", ""), cfg)
            else:
                df = load_dataset(ds, cfg)
            for seed in range(3):
                meta, rr = run_single(df, cfg, ds, "lgbm", seed, split, 0.1, fracs=fr)
                for r in rr:
                    rows.append({"representation": variant, "dataset": ds, "split": split,
                                 "seed": seed, "method": r["method"],
                                 "worst_stratum_coverage": r["worst_stratum_coverage"],
                                 "marginal_coverage": r["marginal_coverage"],
                                 "mean_width": r["mean_width"], "shift_auc": meta.get("shift_auc")})
            log.info(f"[repr {variant}] {ds} done")
    F.set_fp_variant(False); P._FEATURE_CACHE.clear()
    df = pd.DataFrame(rows)
    df.to_csv(Path(cfg["paths"]["results_dir"]) / "representation_ablation.csv", index=False)
    # summary: MW-CP worst-stratum under each representation
    summ = (df[df.method == "mwcp"].groupby(["representation", "dataset"])
            .worst_stratum_coverage.mean().round(3).reset_index())
    log.info("MW-CP worst-stratum by representation:\n" + summ.to_string(index=False))
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
