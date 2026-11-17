"""Graph-model (GNN / D-MPNN-style) demonstration of model-agnosticism (N7).
Runs the full conformal method set with the GNN as the base model on a few representative
panel targets (one per family, temporal w30 split), to show MW-CP and the diagnostic hold
with a modern graph-based representation. Writes results/gnn_rows.jsonl.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger
from src.data.datasets import load_panel_target
from src.pipeline import run_single

log = get_logger()
TARGETS = ["egfr", "mor", "cox2", "herg"]   # kinase, GPCR, enzyme, ion channel
WINDOW = (0.60, 0.10, 0.30)
METHODS = ["split", "mondrian", "weighted_ad", "weighted_kmm", "mwcp", "adecp"]
SCALARS = ["method", "dataset", "model", "seed", "window", "marginal_coverage",
           "worst_stratum_coverage", "mean_width", "saturated_fraction", "shift_auc",
           "n_train", "n_calib", "n_test"]


def main():
    cfg = load_config("config/default.yaml")
    cfg["conformal_methods"] = METHODS
    out = Path(cfg["paths"]["results_dir"]) / "gnn_rows.jsonl"
    done = set()
    if out.exists():
        for l in open(out):
            r = json.loads(l); done.add((r["dataset"], r["seed"]))
    for key in TARGETS:
        if (f"panel_{key}", 0) in done:
            continue
        df = load_panel_target(key, cfg)
        meta, rows = run_single(df, cfg, f"panel_{key}", "gnn", 0, "temporal",
                                cfg["primary_alpha"], fracs=WINDOW, window="w30")
        if not rows:
            continue
        with open(out, "a") as f:
            for r in rows:
                f.write(json.dumps({k: r.get(k) for k in SCALARS}, default=float) + "\n")
        log.info(f"[gnn] {key} auc={meta.get('shift_auc', float('nan')):.2f} "
                 f"mwcp_worst={[r['worst_stratum_coverage'] for r in rows if r['method']=='mwcp']}")
    # compile small table
    import pandas as pd
    if out.exists():
        pd.DataFrame([json.loads(l) for l in open(out)]).to_csv(
            Path(cfg["paths"]["results_dir"]) / "gnn_results.csv", index=False)
        log.info("compiled gnn_results.csv")


if __name__ == "__main__":
    main()
