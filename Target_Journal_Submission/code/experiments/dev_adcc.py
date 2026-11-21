"""Round-6 DEVELOPMENT run (method selection) on the MoleculeNet scaffold datasets ONLY.
The ChEMBL temporal panel is held out and never used for choosing the ADCC variant.
Writes results/dev_adcc_rows.jsonl."""
from __future__ import annotations
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config
from src.data.datasets import load_dataset
from src.pipeline import run_single

METHODS = ["split", "mondrian", "weighted_ad", "mwcp",
           "adcc", "adcc_grp", "adcc_spline", "adcc_sig", "adcc_norm"]
KEEP = ["method", "dataset", "seed", "marginal_coverage", "worst_stratum_coverage",
        "max_stratum_gap", "mean_width", "saturated_fraction"]

def main():
    cfg = load_config("config/default.yaml")
    out = Path("results/dev_adcc_rows.jsonl")
    seeds = list(range(int(sys.argv[1]) if len(sys.argv) > 1 else 5))
    with open(out, "a") as fh:
        for ds in cfg["scaffold_datasets"]:
            df = load_dataset(ds, cfg)
            for s in seeds:
                t = time.time()
                meta, rows = run_single(df, cfg, ds, "lgbm", s, "scaffold", 0.1, methods=METHODS)
                for r in rows:
                    rr = {k: r.get(k) for k in KEEP}
                    rr["strata_cov"] = r.get("ad_per_bin_coverage")
                    fh.write(json.dumps(rr) + "\n")
                fh.flush()
                print(ds, s, round(time.time() - t, 1), flush=True)

if __name__ == "__main__":
    main()
