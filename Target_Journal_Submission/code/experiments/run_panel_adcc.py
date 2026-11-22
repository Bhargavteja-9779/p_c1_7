"""Held-out evaluation of ADCC-CP on the 13-target ChEMBL temporal panel.
13 targets x 3 chronological windows x {lgbm, rf} x 3 seeds, all methods paired on identical
splits/models. Parallel over runs; resumable. Writes results/panel_adcc_rows.jsonl
(one row per run x method, incl. per-stratum coverage/width and most-novel-decile coverage)."""
from __future__ import annotations
import sys, json, itertools, os
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["CP_NJOBS"] = "1"
import numpy as np
from src.utils import load_config
from src.data.datasets import load_panel_target
from src.pipeline import run_single

WINDOWS = {"w40": (0.50, 0.10, 0.40), "w30": (0.60, 0.10, 0.30), "w20": (0.70, 0.10, 0.20)}
METHODS = ["split", "normalized", "mondrian", "weighted_ad", "weighted_kmm", "mwcp",
           "adcc", "adcc_grp", "adcc_pl", "adcc_norm"]
OUT = Path("results/panel_adcc_rows.jsonl")
_CFG = None; _DF = {}


def _job(args):
    key, model, seed, wl = args
    global _CFG
    if _CFG is None:
        _CFG = load_config("config/default.yaml")
    if key not in _DF:
        _DF[key] = load_panel_target(key, _CFG)
    df = _DF[key]
    if len(df) < 800:
        return []
    meta, rows = run_single(df, _CFG, f"panel_{key}", model, seed, "temporal", 0.1,
                            methods=METHODS, fracs=WINDOWS[wl], window=wl, return_arrays=True,
                            decision_fracs=[0.05, 0.10, 0.20])
    if not rows:
        return []
    y = meta["y_test"]; a = meta["ad_test"]; tb = meta["test_bin"]
    tail = a <= np.quantile(a, 0.10)
    out = []
    for r in rows:
        lo, hi = meta["arrays"][r["method"]]["lo"], meta["arrays"][r["method"]]["hi"]
        cov = (y >= lo) & (y <= hi); w = hi - lo
        rec = {k: r.get(k) for k in ["method", "marginal_coverage", "worst_stratum_coverage",
                                     "max_stratum_gap", "mean_width", "median_width",
                                     "saturated_fraction", "value_worst_coverage",
                                     "ad_per_bin_coverage", "ad_n_per_bin", "n_train", "n_calib",
                                     "n_test", "shift_auc"]}
        rec.update({"dataset": f"panel_{key}", "target": key, "model": model, "seed": seed,
                    "window": wl, "tail10_coverage": float(cov[tail].mean()),
                    "tail10_width": float(w[tail].mean()),
                    "width_per_bin": [float(w[tb == b].mean()) if np.any(tb == b) else None
                                      for b in range(int(tb.max()) + 1)],
                    "decision": r.get("decision")})
        out.append(rec)
    return out


def main():
    cfg = load_config("config/default.yaml")
    targets = list(cfg["chembl_panel"].keys())
    done = set()
    if OUT.exists():
        for l in open(OUT):
            r = json.loads(l); done.add((r["target"], r["model"], r["seed"], r["window"]))
    combos = [c for c in itertools.product(targets, ["lgbm", "rf"], [0, 1, 2], WINDOWS)
              if c not in done]
    print(f"{len(combos)} runs to do", flush=True)
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    import multiprocessing as mp
    with mp.get_context("spawn").Pool(nproc, maxtasksperchild=6) as pool:
        for rows in pool.imap_unordered(_job, combos):
            if rows:
                with open(OUT, "a") as fh:
                    for r in rows:
                        fh.write(json.dumps(r, default=float) + "\n")
                print(rows[0]["target"], rows[0]["model"], rows[0]["seed"], rows[0]["window"], flush=True)


if __name__ == "__main__":
    main()
