"""Round-6 validity controls for ADCC-CP.
(A) exchangeable random splits (no shift): every method should be ~nominal marginally;
    ADCC-CP should additionally be ~nominal within every AD stratum.
(B) controlled AD-tilt shift with a KNOWN density ratio that is a function of a(x):
    'pl' tilt lies inside the ADCC function class (theorem applies exactly); 'exp' tilt lies
    outside (tests robustness). Compare ADCC-CP vs split / ADR-CP (estimated 1-D ratio).
Datasets: 4 MoleculeNet + 4 ChEMBL panel targets; LightGBM; 10 seeds. -> results/validity_adcc_rows.jsonl"""
from __future__ import annotations
import sys, json, os, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["CP_NJOBS"] = "1"
import numpy as np
from src.utils import load_config
from src.data.datasets import load_dataset, load_panel_target
from src.pipeline import run_single

METHODS = ["split", "mondrian", "weighted_ad", "mwcp", "adcc", "adcc_pl"]
OUT = Path("results/validity_adcc_rows.jsonl")
SETTINGS = [("random", None), ("adtilt_pl", 0.9), ("adtilt_exp", 8.0)]
DATA = ["lipophilicity", "bace", "esol", "freesolv", "egfr", "herg", "mor", "dpp4"]


def _load(k, cfg):
    return load_dataset(k, cfg) if k in cfg["scaffold_datasets"] else load_panel_target(k, cfg)


def _job(args):
    k, (st, lam), seed = args
    cfg = load_config("config/default.yaml")
    df = _load(k, cfg)
    meta, rows = run_single(df, cfg, k, "lgbm", seed, st, 0.1, methods=METHODS, sweep_q=lam,
                            fracs=(0.6, 0.2, 0.2), return_arrays=True)
    out = []
    a = meta["ad_test"]; y = meta["y_test"]
    tail = a <= np.quantile(a, 0.10)
    for r in rows:
        lo, hi = meta["arrays"][r["method"]]["lo"], meta["arrays"][r["method"]]["hi"]
        cov = (y >= lo) & (y <= hi)
        out.append({"dataset": k, "setting": st, "lam": lam, "seed": seed, "method": r["method"],
                    "marginal_coverage": r["marginal_coverage"],
                    "worst_stratum_coverage": r["worst_stratum_coverage"],
                    "ad_per_bin_coverage": r["ad_per_bin_coverage"],
                    "mean_width": r["mean_width"], "saturated_fraction": r.get("saturated_fraction"),
                    "tail10_coverage": float(cov[tail].mean())})
    return out


def main():
    import multiprocessing as mp
    done = set()
    if OUT.exists():
        for l in open(OUT):
            r = json.loads(l); done.add((r["dataset"], r["setting"], r["seed"]))
    combos = [c for c in itertools.product(DATA, SETTINGS, range(10)) if (c[0], c[1][0], c[2]) not in done]
    print(len(combos), "runs", flush=True)
    with mp.get_context("spawn").Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        for rows in pool.imap_unordered(_job, combos):
            with open(OUT, "a") as fh:
                for r in rows:
                    fh.write(json.dumps(r, default=float) + "\n")
            print(rows[0]["dataset"], rows[0]["setting"], rows[0]["seed"], flush=True)


if __name__ == "__main__":
    main()
