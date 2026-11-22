"""Target-level validation of the shift-magnitude diagnostic.

Validates whether the train-vs-pool discriminator AUC predicts achievable conditional
coverage, using TARGET-level (not split-level) analysis and leave-one-target-out
evaluation of a decision threshold, with bootstrap CIs and false-safe/false-alarm rates.
Operates on panel_results.csv (per target x window x seed x method).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as sps

from ..utils import save_json, get_logger
from .tests import bootstrap_ci

log = get_logger()


def _target_table(panel_csv, method="mwcp", alpha=0.1, cov_tol=0.05):
    """Aggregate to one row per (target, window): mean shift AUC and mean worst-stratum
    coverage of the given method; 'safe' = coverage >= (1-alpha) - cov_tol."""
    d = pd.read_csv(panel_csv)
    d = d[d.model == "lgbm"]
    g = (d[d.method == method].groupby(["dataset", "window"])
         .agg(auc=("shift_auc", "mean"), worst=("worst_stratum_coverage", "mean"))
         .reset_index())
    g["target"] = g["dataset"]
    g["safe"] = (g["worst"] >= (1 - alpha) - cov_tol).astype(int)
    return g


def validate_diagnostic(cfg, method="mwcp", alpha=0.1):
    rdir = Path(cfg["paths"]["results_dir"])
    panel_csv = rdir / "panel_results.csv"
    if not panel_csv.exists():
        log.warning("panel_results.csv not found; skipping diagnostic validation")
        return None
    g = _target_table(panel_csv, method=method, alpha=alpha)
    out = {"method": method, "alpha": alpha, "n_target_windows": int(len(g)),
           "n_targets": int(g["target"].nunique())}

    # Target-level correlation (aggregate per target to respect independence)
    gt = g.groupby("target").agg(auc=("auc", "mean"), worst=("worst", "mean")).reset_index()
    if len(gt) >= 4:
        rho, p = sps.spearmanr(gt["auc"], gt["worst"])
        out["target_level_spearman"] = {"rho": round(float(rho), 3), "p": float(p), "n": int(len(gt))}

    # Leave-one-target-out threshold validation.
    # Threshold rule: predict "unsafe" if AUC > tau*, where tau* is the midpoint between
    # the safe and unsafe AUC clusters learned on training targets (Youden-style on the
    # training fold). Evaluate false-safe / false-alarm on the held-out target.
    targets = gt["target"].tolist()
    fs, fa, n_eval = 0, 0, 0
    thresholds = []
    for held in targets:
        tr = g[g.target != held]
        te = g[g.target == held]
        if tr["safe"].nunique() < 2:
            continue
        # choose tau* maximizing Youden's J (sensitivity for detecting unsafe) on train
        cand = np.quantile(tr["auc"], np.linspace(0.1, 0.9, 17))
        best_tau, best_j = None, -1
        for tau in cand:
            pred_unsafe = tr["auc"] > tau
            tp = ((pred_unsafe) & (tr["safe"] == 0)).sum()
            fn = ((~pred_unsafe) & (tr["safe"] == 0)).sum()
            tn = ((~pred_unsafe) & (tr["safe"] == 1)).sum()
            fp = ((pred_unsafe) & (tr["safe"] == 1)).sum()
            sens = tp / max(1, tp + fn); spec = tn / max(1, tn + fp)
            j = sens + spec - 1
            if j > best_j:
                best_j, best_tau = j, tau
        thresholds.append(float(best_tau))
        for _, r in te.iterrows():
            pred_safe = r["auc"] <= best_tau
            n_eval += 1
            if pred_safe and r["safe"] == 0:
                fs += 1   # false-safe: predicted deployable but coverage failed
            if (not pred_safe) and r["safe"] == 1:
                fa += 1   # false-alarm: predicted unsafe but coverage was fine
    if n_eval:
        out["loto"] = {"n_eval": n_eval, "false_safe_rate": round(fs / n_eval, 3),
                       "false_alarm_rate": round(fa / n_eval, 3)}
    if thresholds:
        m, lo, hi = bootstrap_ci(np.array(thresholds), n_boot=2000, seed=0)
        out["threshold_auc"] = {"mean": round(m, 3), "ci95": [round(lo, 3), round(hi, 3)],
                                "note": "leave-one-target-out Youden thresholds; AUC above this predicts unrecoverable conditional coverage"}
    out["per_target"] = gt.round(3).to_dict(orient="records")
    save_json(out, rdir / "diagnostic_validation.json")
    log.info(f"diagnostic validation: {out.get('loto')}, threshold {out.get('threshold_auc')}")
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils import load_config
    validate_diagnostic(load_config("config/default.yaml"))
