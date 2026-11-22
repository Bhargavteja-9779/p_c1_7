"""Expanded prospective-screening decision analysis and
chemical-space interpretation. Retrospective temporal screening simulation (NOT a prospective
experimental validation).

B. Screening budgets 5/10/20/30%: surprise rate, hit rate, enrichment, and mean interval
   width AMONG SELECTED compounds (the width-vs-surprise trade-off) for split vs ADR-CP.
B'. Uncertainty-aware decision rule: tier test compounds by the AD coordinate using
   thresholds set on CALIBRATION (tertiles of calib a(x)) -> low/moderate/high uncertainty;
   report mean |error|, split coverage, ADR-CP coverage and width per tier (thresholds never
   use test outcomes).
E. Coverage by molecular-descriptor quartile (MW, logP, TPSA, HBD, HBA, rotatable bonds):
   split vs ADR-CP, to show the correction is not confined to one chemical subset.

Writes: tables/tableS_screening_decision.csv, tables/tableS_decision_rule.csv,
        tables/tableS_coverage_by_descriptor.csv (extended), results/screening_chem.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from collections import defaultdict
import numpy as np, csv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger, ensure_dir
from src.data.datasets import load_panel_target
from src.pipeline import run_single, get_features
from src.preprocessing.splits import temporal_split
from src.preprocessing.features import max_sim_to_ref_matrix
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors

log = get_logger()
FR = (0.60, 0.10, 0.30)
SEEDS = [0, 1, 2]
BUDGETS = [0.05, 0.10, 0.20, 0.30]
DESCS = ["MW", "logP", "TPSA", "HBD", "HBA", "RotB"]


def _descriptors(smiles):
    out = {d: np.full(len(smiles), np.nan) for d in DESCS}
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        if m is None:
            continue
        out["MW"][i] = Descriptors.MolWt(m); out["logP"][i] = Crippen.MolLogP(m)
        out["TPSA"][i] = rdMolDescriptors.CalcTPSA(m); out["HBD"][i] = rdMolDescriptors.CalcNumHBD(m)
        out["HBA"][i] = rdMolDescriptors.CalcNumHBA(m)
        out["RotB"][i] = rdMolDescriptors.CalcNumRotatableBonds(m)
    return out


def main():
    cfg = load_config("config/default.yaml")
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    panel = cfg["chembl_panel"]

    budg = {b: {"split": defaultdict(list), "adr": defaultdict(list)} for b in BUDGETS}
    tiers = {t: {"err": [], "cov_s": [], "cov_a": [], "w_a": [], "n": 0} for t in ("high", "moderate", "low")}
    desc_cov = {d: defaultdict(lambda: {"split": [], "adr": []}) for d in DESCS}
    total = 0

    for key in panel:
        try:
            df = load_panel_target(key, cfg)
        except Exception as e:
            log.warning(f"{key}: {e}"); continue
        if len(df) < 800:
            continue
        smi = df["smiles"].to_numpy()
        X = get_features(f"panel_{key}", smi, cfg["features"]["fp_radius"], cfg["features"]["fp_bits"])
        for seed in SEEDS:
            meta, rows = run_single(df, cfg, f"panel_{key}", "lgbm", seed, "temporal",
                                    cfg["primary_alpha"], methods=["split", "weighted_ad"],
                                    decision_fracs=BUDGETS, return_arrays=True, fracs=FR, window="w30")
            if meta.get("skipped"):
                continue
            yte = np.asarray(meta["y_test"]); yhat = np.asarray(meta["yhat_test"])
            ad = np.asarray(meta["ad_test"]); resid = np.abs(yte - yhat)
            lo_s, hi_s = meta["arrays"]["split"]["lo"], meta["arrays"]["split"]["hi"]
            lo_a, hi_a = meta["arrays"]["weighted_ad"]["lo"], meta["arrays"]["weighted_ad"]["hi"]
            cov_s = (yte >= lo_s) & (yte <= hi_s); cov_a = (yte >= lo_a) & (yte <= hi_a)
            w_a = hi_a - lo_a
            drow = {r["method"]: r["decision"] for r in rows if "decision" in r}

            # B: budgets (surprise/hit from decision_utility) + width among selected (from arrays)
            for b in BUDGETS:
                k = max(1, int(round(b * len(yhat))))
                sel = np.argsort(-yhat)[:k]
                for mth, key2, lo, hi in (("split", "split", lo_s, hi_s), ("weighted_ad", "adr", lo_a, hi_a)):
                    d = drow[mth][str(b)]
                    budg[b][key2]["surprise"].append(d["surprise_rate"])
                    budg[b][key2]["hit"].append(d["hit_rate"])
                    budg[b][key2]["enrich"].append(d["hit_rate"] / d["base_rate"] if d["base_rate"] else np.nan)
                    budg[b][key2]["width"].append(float(np.mean((hi - lo)[sel])))

            # B': decision rule, thresholds from CALIBRATION a(x) tertiles
            tr, ca, te = temporal_split(df, FR, seed)
            ad_ca = max_sim_to_ref_matrix(X[ca], X[tr])
            t33, t66 = np.quantile(ad_ca, [1/3, 2/3])
            tier_of = np.where(ad < t33, "high", np.where(ad < t66, "moderate", "low"))
            for t in ("high", "moderate", "low"):
                m = tier_of == t
                if m.sum() == 0:
                    continue
                tiers[t]["err"].extend(resid[m].tolist())
                tiers[t]["cov_s"].extend(cov_s[m].tolist()); tiers[t]["cov_a"].extend(cov_a[m].tolist())
                tiers[t]["w_a"].extend(w_a[m].tolist()); tiers[t]["n"] += int(m.sum())

            # E: coverage by descriptor quartile
            dvals = _descriptors(smi[te])
            for d in DESCS:
                v = dvals[d]; ok = ~np.isnan(v)
                if ok.sum() < 20:
                    continue
                q = np.quantile(v[ok], [0.25, 0.5, 0.75]); qb = np.digitize(v, q)
                for b in range(4):
                    sel = (qb == b) & ok
                    if sel.sum() == 0:
                        continue
                    desc_cov[d][b]["split"].extend(cov_s[sel].tolist())
                    desc_cov[d][b]["adr"].extend(cov_a[sel].tolist())
            total += 1
        log.info(f"{key} done")

    tdir = ensure_dir("tables")
    # B table
    with open(Path(tdir) / "tableS_screening_decision.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Budget", "Method", "Surprise rate", "Hit rate", "Enrichment",
                    "Mean width (selected)"])
        for b in BUDGETS:
            for mth, lab in (("split", "Split CP"), ("adr", "ADR-CP")):
                d = budg[b][mth]
                w.writerow([f"{int(b*100)}%", lab, f"{np.mean(d['surprise']):.3f}",
                            f"{np.mean(d['hit']):.3f}", f"{np.nanmean(d['enrich']):.2f}",
                            f"{np.mean(d['width']):.2f}"])
    # B' decision-rule table
    with open(Path(tdir) / "tableS_decision_rule.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Uncertainty tier (calib-defined)", "Fraction of test", "Mean |error|",
                    "Split CP coverage", "ADR-CP coverage", "ADR-CP mean width"])
        ntot = sum(tiers[t]["n"] for t in tiers)
        for t, lab in (("low", "Low (reliable)"), ("moderate", "Moderate"), ("high", "High (test first)")):
            d = tiers[t]
            w.writerow([lab, f"{d['n']/ntot:.2f}", f"{np.mean(d['err']):.3f}",
                        f"{np.mean(d['cov_s']):.3f}", f"{np.mean(d['cov_a']):.3f}",
                        f"{np.mean(d['w_a']):.2f}"])
    # E descriptor table
    with open(Path(tdir) / "tableS_coverage_by_descriptor.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Descriptor", "Quartile", "Split CP cov", "ADR-CP cov", "n"])
        for d in DESCS:
            for b in sorted(desc_cov[d]):
                dd = desc_cov[d][b]
                w.writerow([d, f"Q{b+1}", f"{np.mean(dd['split']):.3f}",
                            f"{np.mean(dd['adr']):.3f}", len(dd["split"])])

    summary = {"n_runs": total, "budgets": {str(b): {
        "split_surprise": float(np.mean(budg[b]["split"]["surprise"])),
        "adr_surprise": float(np.mean(budg[b]["adr"]["surprise"])),
        "split_width_sel": float(np.mean(budg[b]["split"]["width"])),
        "adr_width_sel": float(np.mean(budg[b]["adr"]["width"]))} for b in BUDGETS},
        "decision_rule": {t: {"frac": tiers[t]["n"], "mean_abs_err": float(np.mean(tiers[t]["err"])),
                              "split_cov": float(np.mean(tiers[t]["cov_s"])),
                              "adr_cov": float(np.mean(tiers[t]["cov_a"]))} for t in tiers}}
    json.dump(summary, open(Path(rdir) / "screening_chem.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("\nWrote tableS_screening_decision.csv, tableS_decision_rule.csv, tableS_coverage_by_descriptor.csv")


if __name__ == "__main__":
    main()
