"""Is the AD-aligned correction robust to the
*definition* of the applicability-domain coordinate? Run the SAME ADR-CP procedure with
four pre-defined AD coordinates and compare. Model features stay ECFP4 throughout; only the
AD axis changes. The comparison is predefined (no post-hoc selection of the best coordinate).

AD coordinates:
  max_ecfp       - max ECFP4 Tanimoto to training set (the paper's default)
  meantop5_ecfp  - mean of top-5 ECFP4 Tanimoto to training set
  max_fcfp       - max FCFP4 Tanimoto to training set
  physchem       - 1/(1+nearest-train Euclidean distance) in standardized
                   physicochemical-descriptor space (MW, logP, TPSA, HBD, HBA, RotB)

Writes: tables/table_ad_representation.csv, results/ad_representation.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger, ensure_dir
from src.data.datasets import load_panel_target
from src.pipeline import run_single

log = get_logger()
VARIANTS = ["max_ecfp", "meantop5_ecfp", "max_fcfp", "physchem"]
LABEL = {"max_ecfp": "Max ECFP4 (default)", "meantop5_ecfp": "Mean top-5 ECFP4",
         "max_fcfp": "Max FCFP4", "physchem": "Physchem-distance"}
FR = (0.60, 0.10, 0.30)   # window w30
SEEDS = [0, 1, 2]
MODEL = "lgbm"


def _get(rows, method):
    for r in rows:
        if r["method"] == method:
            return r
    return None


def main():
    cfg = load_config("config/default.yaml")
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    panel = cfg["chembl_panel"]
    acc = {v: {"adr_worst": [], "adr_marg": [], "adr_width": [], "adr_sat": [],
               "adr_ess": [], "split_worst": [], "delta": [], "per_target": {}}
           for v in VARIANTS}

    for key in panel:
        try:
            df = load_panel_target(key, cfg)
        except Exception as e:
            log.warning(f"{key}: {e}"); continue
        if len(df) < 800:
            continue
        for v in VARIANTS:
            dworst, dmarg, dwid, dsat, dess, sworst = [], [], [], [], [], []
            for seed in SEEDS:
                meta, rows = run_single(df, cfg, f"panel_{key}", MODEL, seed, "temporal",
                                        cfg["primary_alpha"], methods=["split", "weighted_ad"],
                                        fracs=FR, window="w30", ad_variant=v)
                if meta.get("skipped"):
                    continue
                adr = _get(rows, "weighted_ad"); spl = _get(rows, "split")
                if adr is None or spl is None:
                    continue
                dworst.append(adr["worst_stratum_coverage"]); dmarg.append(adr["marginal_coverage"])
                dwid.append(adr["mean_width"]); dsat.append(adr["saturated_fraction"])
                dess.append(adr.get("eff_sample_size", np.nan))
                sworst.append(spl["worst_stratum_coverage"])
            if not dworst:
                continue
            acc[v]["adr_worst"].append(np.mean(dworst)); acc[v]["adr_marg"].append(np.mean(dmarg))
            acc[v]["adr_width"].append(np.mean(dwid)); acc[v]["adr_sat"].append(np.mean(dsat))
            acc[v]["adr_ess"].append(np.nanmean(dess)); acc[v]["split_worst"].append(np.mean(sworst))
            acc[v]["delta"].append(np.mean(dworst) - np.mean(sworst))
            acc[v]["per_target"][key] = round(float(np.mean(dworst)), 3)
            log.info(f"{key} [{v}]: ADR worst {np.mean(dworst):.3f} vs split {np.mean(sworst):.3f}")

    import csv
    tdir = ensure_dir("tables")
    out = Path(tdir) / "table_ad_representation.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["AD coordinate", "ADR-CP worst-stratum", "ADR-CP marginal", "Mean width",
                    "Saturated frac", "Eff. calib N", "Split worst-stratum", "Δ vs split",
                    "Targets improved"])
        for v in VARIANTS:
            a = acc[v]
            if not a["adr_worst"]:
                continue
            n_imp = sum(1 for d in a["delta"] if d > 0)
            w.writerow([LABEL[v], f"{np.mean(a['adr_worst']):.3f}", f"{np.mean(a['adr_marg']):.3f}",
                        f"{np.mean(a['adr_width']):.2f}", f"{np.mean(a['adr_sat']):.3f}",
                        f"{np.mean(a['adr_ess']):.0f}", f"{np.mean(a['split_worst']):.3f}",
                        f"+{np.mean(a['delta']):.3f}", f"{n_imp}/{len(a['delta'])}"])

    summary = {v: {"adr_worst_mean": float(np.mean(acc[v]["adr_worst"])),
                   "adr_marg_mean": float(np.mean(acc[v]["adr_marg"])),
                   "width_mean": float(np.mean(acc[v]["adr_width"])),
                   "split_worst_mean": float(np.mean(acc[v]["split_worst"])),
                   "delta_mean": float(np.mean(acc[v]["delta"])),
                   "targets_improved": int(sum(1 for d in acc[v]["delta"] if d > 0)),
                   "n_targets": len(acc[v]["delta"]),
                   "per_target": acc[v]["per_target"]}
               for v in VARIANTS if acc[v]["adr_worst"]}
    json.dump(summary, open(Path(rdir) / "ad_representation.json", "w"), indent=1)
    print(json.dumps({v: {k: s[k] for k in ("adr_worst_mean", "split_worst_mean",
                     "delta_mean", "targets_improved", "n_targets")}
                      for v, s in summary.items()}, indent=1))
    print("\nWrote tables/table_ad_representation.csv")


if __name__ == "__main__":
    main()
