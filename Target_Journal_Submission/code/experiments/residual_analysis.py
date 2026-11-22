"""Justification analyses for the AD-aligned correction.

Addresses: (1) is the 1-D applicability-domain coordinate a(x) a sufficient statistic
for the covariate-shift correction? -> within-AD-stratum calib-vs-test discriminator AUC
(if a(x) captured the shift, within-stratum AUC -> 0.5) and incremental variance of the
conformity score explained by extra descriptors beyond a(x); (2) coverage by scaffold
family; (3) coverage by molecular-descriptor bins (MW, logP). All from real runs.

Writes:
  tables/tableS_ad_sufficiency.csv
  tables/tableS_family_coverage.csv
  tables/tableS_coverage_by_descriptor.csv
  results/residual_analysis.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, get_logger, ensure_dir
from src.data.datasets import load_panel_target
from src.pipeline import run_single, get_features
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors

log = get_logger()
WINDOW = ("w30", (0.60, 0.10, 0.30))
SEED = 0
MODEL = "lgbm"
METHODS = ["split", "weighted_ad"]
N_STRATA = 4


def _disc_auc(Xa, Xb, seed=0):
    """Cross-validated discriminator AUC separating two fingerprint sets (0.5 = indistinguishable)."""
    if len(Xa) < 12 or len(Xb) < 12:
        return np.nan
    X = np.vstack([Xa, Xb]); y = np.r_[np.zeros(len(Xa)), np.ones(len(Xb))]
    ncomp = int(min(32, X.shape[1], len(X) - 1))
    Z = PCA(n_components=ncomp, random_state=seed).fit_transform(StandardScaler().fit_transform(X))
    clf = LogisticRegression(max_iter=1000, C=0.1, class_weight="balanced")
    k = min(3, int(min(len(Xa), len(Xb))))
    if k < 2:
        return np.nan
    try:
        aucs = cross_val_score(clf, Z, y, cv=StratifiedKFold(k, shuffle=True, random_state=seed),
                               scoring="roc_auc")
        return float(np.mean(aucs))
    except Exception:
        return np.nan


def _descriptors(smiles):
    mw = np.full(len(smiles), np.nan); lp = np.full(len(smiles), np.nan)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        if m is None:
            continue
        mw[i] = Descriptors.MolWt(m); lp[i] = Crippen.MolLogP(m)
    return mw, lp


def main():
    cfg = load_config("config/default.yaml")
    rdir = ensure_dir(cfg["paths"]["results_dir"])
    panel = cfg["chembl_panel"]
    wlabel, fr = WINDOW

    # accumulators
    per_target = {}
    strat_auc = {k: [] for k in range(N_STRATA)}   # within-stratum calib-vs-test AUC
    global_auc = []
    r2_a, r2_full = [], []
    fam_rows = {}         # family -> {method -> [covered bools], widths}
    desc_cov = {"MW": {}, "logP": {}}   # quartile -> method -> [covered]

    for key, meta in panel.items():
        family = meta["family"]
        try:
            df = load_panel_target(key, cfg)
        except Exception as e:
            log.warning(f"{key}: {e}"); continue
        if len(df) < 800:
            continue
        m, rows = run_single(df, cfg, f"panel_{key}", MODEL, SEED, "temporal",
                             cfg["primary_alpha"], methods=METHODS, fracs=fr,
                             window=wlabel, return_arrays=True)
        if m.get("skipped"):
            continue
        yte = np.asarray(m["y_test"]); yhat = np.asarray(m["yhat_test"])
        ad = np.asarray(m["ad_test"]); tb = np.asarray(m["test_bin"])
        resid = np.abs(yte - yhat)
        arr = m["arrays"]
        lo_s, hi_s = arr["split"]["lo"], arr["split"]["hi"]
        lo_a, hi_a = arr["weighted_ad"]["lo"], arr["weighted_ad"]["hi"]
        cov_s = (yte >= lo_s) & (yte <= hi_s)
        cov_a = (yte >= lo_a) & (yte <= hi_a)
        w_a = hi_a - lo_a

        # --- per-compound descriptors
        smi = df["smiles"].to_numpy()
        # need test SMILES: recompute split indices is awkward; instead map by re-featurizing.
        # run_single used temporal_split; we reconstruct test smiles via the same featurize order.
        # Simpler: compute descriptors for all, then we need test subset. We approximate using
        # the stored yhat length == n_test; get test indices by re-running the split:
        from src.preprocessing.splits import temporal_split
        X = get_features(f"panel_{key}", smi, cfg["features"]["fp_radius"], cfg["features"]["fp_bits"])
        tr, ca, te = temporal_split(df, fr, SEED)
        smi_te = smi[te]
        mw, lp = _descriptors(smi_te)

        # (1a) within-stratum calib-vs-test discriminator AUC (full fingerprint)
        Xca, Xte = X[ca], X[te]
        ad_ca = np.asarray([])  # recompute calib strata
        from src.preprocessing.features import max_sim_to_ref_matrix
        from src.preprocessing.splits import ad_strata
        ad_ca = max_sim_to_ref_matrix(Xca, X[tr])
        cb, tb2 = ad_strata(ad_ca, ad, N_STRATA)
        gauc = _disc_auc(Xca, Xte, SEED)
        if not np.isnan(gauc):
            global_auc.append(gauc)
        tgt_strat = {}
        for k in range(N_STRATA):
            a_idx = np.where(cb == k)[0]; b_idx = np.where(tb2 == k)[0]
            au = _disc_auc(Xca[a_idx], Xte[b_idx], SEED) if len(a_idx) and len(b_idx) else np.nan
            if not np.isnan(au):
                strat_auc[k].append(au); tgt_strat[k] = au

        # (1b) incremental variance of conformity score |resid| explained beyond a(x)
        feat = np.column_stack([ad, mw, lp]).astype(float)
        ok = ~np.isnan(feat).any(axis=1)
        if ok.sum() > 30:
            Z = StandardScaler().fit_transform(feat[ok]); yv = resid[ok]
            ra = LinearRegression().fit(Z[:, :1], yv).score(Z[:, :1], yv)
            rf = LinearRegression().fit(Z, yv).score(Z, yv)
            r2_a.append(ra); r2_full.append(rf)

        # (2) family coverage
        fam_rows.setdefault(family, {"split": [], "adr": [], "w_adr": []})
        fam_rows[family]["split"].extend(cov_s.tolist())
        fam_rows[family]["adr"].extend(cov_a.tolist())
        fam_rows[family]["w_adr"].extend(w_a.tolist())

        # (3) coverage by descriptor quartile
        for name, vals in (("MW", mw), ("logP", lp)):
            ok2 = ~np.isnan(vals)
            if ok2.sum() < 20:
                continue
            q = np.quantile(vals[ok2], [0.25, 0.5, 0.75])
            qb = np.digitize(vals, q)
            for b in range(4):
                sel = (qb == b) & ok2
                if sel.sum() == 0:
                    continue
                d = desc_cov[name].setdefault(b, {"split": [], "adr": []})
                d["split"].extend(cov_s[sel].tolist())
                d["adr"].extend(cov_a[sel].tolist())

        per_target[key] = {
            "family": family, "n_test": int(len(te)),
            "cov_split": float(cov_s.mean()), "cov_adr": float(cov_a.mean()),
            "global_disc_auc": gauc, "within_stratum_auc": tgt_strat,
        }
        log.info(f"{key}: cov split {cov_s.mean():.3f} adr {cov_a.mean():.3f} gauc {gauc:.3f}")

    # ---- write ad-sufficiency table
    import csv
    tdir = ensure_dir("tables")
    with open(Path(tdir) / "tableS_ad_sufficiency.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["AD stratum", "Mean calib-vs-test discriminator AUC", "n targets"])
        w.writerow(["All (global, full fingerprint)", f"{np.mean(global_auc):.3f}", len(global_auc)])
        labels = {0: "S0 (most out-of-domain)", 1: "S1", 2: "S2", 3: "S3 (in-domain)"}
        for k in range(N_STRATA):
            if strat_auc[k]:
                w.writerow([f"within {labels[k]}", f"{np.mean(strat_auc[k]):.3f}", len(strat_auc[k])])

    # ---- family coverage table
    with open(Path(tdir) / "tableS_family_coverage.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Family", "n", "Split CP marginal cov", "ADR-CP marginal cov", "ADR-CP mean width"])
        for fam in sorted(fam_rows):
            d = fam_rows[fam]
            w.writerow([fam, len(d["split"]), f"{np.mean(d['split']):.3f}",
                        f"{np.mean(d['adr']):.3f}", f"{np.mean(d['w_adr']):.2f}"])

    # ---- coverage by descriptor table
    with open(Path(tdir) / "tableS_coverage_by_descriptor.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Descriptor", "Quartile", "Split CP cov", "ADR-CP cov", "n"])
        for name in ("MW", "logP"):
            for b in sorted(desc_cov[name]):
                d = desc_cov[name][b]
                w.writerow([name, f"Q{b+1}", f"{np.mean(d['split']):.3f}",
                            f"{np.mean(d['adr']):.3f}", len(d["split"])])

    summary = {
        "window": wlabel, "model": MODEL, "seed": SEED,
        "global_disc_auc_mean": float(np.mean(global_auc)) if global_auc else None,
        "within_stratum_auc_mean": {str(k): (float(np.mean(v)) if v else None)
                                    for k, v in strat_auc.items()},
        "conformity_score_R2_a_only_mean": float(np.mean(r2_a)) if r2_a else None,
        "conformity_score_R2_a_plus_descriptors_mean": float(np.mean(r2_full)) if r2_full else None,
        "per_target": per_target,
    }
    json.dump(summary, open(Path(rdir) / "residual_analysis.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "per_target"}, indent=1))
    print("\nWrote tableS_ad_sufficiency.csv, tableS_family_coverage.csv, tableS_coverage_by_descriptor.csv")


if __name__ == "__main__":
    main()
