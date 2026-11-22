"""Core per-run pipeline: train one model on one covariate-shift split and
evaluate every conformal method. Returns machine-readable metric rows.

A 'run' = (dataset, model, seed, split_type, alpha).
"""
from __future__ import annotations
import time
import numpy as np

from .utils import set_global_seed
from .preprocessing.features import ecfp_matrix, max_sim_to_ref_matrix, tanimoto_matrix
from .preprocessing.splits import scaffold_split, temporal_split, similarity_shift_split, ad_strata
from .models.regressors import make_regressor
from .conformal.base import knn_local_sigma
from .conformal.methods import CPContext, run_method
from .conformal.weighting import DensityRatioWeights
from .evaluation.metrics import summarize, value_quartile_bins, decision_utility

_FEATURE_CACHE = {}
_AD_AUX_CACHE = {}   # dataset_key -> {"fcfp": matrix, "physchem": matrix}


def get_features(dataset_key, smiles, radius, nbits):
    """Cache the dense fingerprint matrix per dataset (featurization is the same across
    all runs on a dataset, so compute it once)."""
    key = (dataset_key, radius, nbits)
    if key not in _FEATURE_CACHE:
        _FEATURE_CACHE[key] = ecfp_matrix(smiles, radius, nbits)
    return _FEATURE_CACHE[key]


def _physchem_matrix(smiles):
    """Standardizable physicochemical descriptor matrix (MW, logP, TPSA, HBD, HBA, RotB)."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors
    rows = []
    for s in smiles:
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        if m is None:
            rows.append([np.nan] * 6)
        else:
            rows.append([Descriptors.MolWt(m), Crippen.MolLogP(m),
                         rdMolDescriptors.CalcTPSA(m),
                         rdMolDescriptors.CalcNumHBD(m), rdMolDescriptors.CalcNumHBA(m),
                         rdMolDescriptors.CalcNumRotatableBonds(m)])
    A = np.array(rows, dtype=float)
    col_med = np.nanmedian(A, axis=0)
    inds = np.where(np.isnan(A))
    A[inds] = np.take(col_med, inds[1])
    return A


def _ad_coordinate(variant, dataset_key, smiles, X, tr, ca, te, radius, nbits):
    """Applicability-domain coordinate a(x) (higher = more in-domain) for calib and test,
    under four reasonable definitions of chemical novelty. Model features stay ECFP; only the
    AD axis changes, isolating the effect of the AD definition."""
    from .preprocessing.features import (max_sim_to_ref_matrix, tanimoto_matrix,
                                         set_fp_variant, ecfp_matrix)
    if variant == "max_ecfp":
        return max_sim_to_ref_matrix(X[ca], X[tr]), max_sim_to_ref_matrix(X[te], X[tr])
    if variant == "meantop5_ecfp":
        def _mtop(Xq):
            out = np.zeros(len(Xq), dtype=np.float32)
            for i in range(0, len(Xq), 256):
                T = tanimoto_matrix(Xq[i:i+256], X[tr])
                T.sort(axis=1)
                out[i:i+256] = T[:, -5:].mean(axis=1)
            return out
        return _mtop(X[ca]), _mtop(X[te])
    if variant == "max_fcfp":
        aux = _AD_AUX_CACHE.setdefault(dataset_key, {})
        if "fcfp" not in aux:
            set_fp_variant(True)
            aux["fcfp"] = ecfp_matrix(smiles, radius, nbits)
            set_fp_variant(False)
        Xf = aux["fcfp"]
        return max_sim_to_ref_matrix(Xf[ca], Xf[tr]), max_sim_to_ref_matrix(Xf[te], Xf[tr])
    if variant == "physchem":
        aux = _AD_AUX_CACHE.setdefault(dataset_key, {})
        if "physchem" not in aux:
            aux["physchem"] = _physchem_matrix(smiles)
        P = aux["physchem"]
        mu, sd = P[tr].mean(axis=0), P[tr].std(axis=0) + 1e-9
        Ptr = (P[tr] - mu) / sd
        def _nn_sim(idx):
            Q = (P[idx] - mu) / sd
            out = np.zeros(len(Q), dtype=np.float32)
            for i in range(0, len(Q), 256):
                d = np.sqrt(((Q[i:i+256, None, :] - Ptr[None, :, :]) ** 2).sum(axis=2))
                out[i:i+256] = 1.0 / (1.0 + d.min(axis=1))   # higher = closer = in-domain
            return out
        return _nn_sim(ca), _nn_sim(te)
    raise KeyError(variant)


def _make_split(df, X, split_type, fracs, seed, sweep_q=None):
    if split_type == "scaffold":
        return scaffold_split(df, fracs, seed)
    if split_type == "temporal":
        return temporal_split(df, fracs, seed)
    if split_type == "random":
        from .preprocessing.splits import random_split
        return random_split(df, fracs, seed)
    if split_type.startswith("adtilt"):
        # adtilt_exp / adtilt_pl ; sweep_q carries the tilt strength lambda
        from .preprocessing.splits import ad_tilt_split
        return ad_tilt_split(df, X, sweep_q, fracs, seed, kind=split_type.split("_")[1])
    if split_type == "similarity":
        return similarity_shift_split(df, X, sweep_q, fracs, seed)
    raise KeyError(split_type)


def run_single(df, cfg, dataset_key, model_name, seed, split_type, alpha,
               methods=None, sweep_q=None, decision_fracs=None, return_arrays=False,
               fracs=None, window=None, ad_variant="max_ecfp"):
    """Execute one run. df must have columns smiles,y (and year for temporal).
    `fracs` overrides the (train,calib,test) proportions (used for multiple temporal
    windows). `window` is a label recorded in the output rows."""
    t0 = time.time()
    set_global_seed(seed)
    level = 1.0 - alpha
    methods = methods or cfg["conformal_methods"]
    fr = cfg["split"]
    if fracs is None:
        fracs = (fr["train_frac"], fr["calib_frac"], fr["test_frac"])
    n_strata = fr["n_ad_strata"]

    smiles = df["smiles"].to_numpy()
    y = df["y"].to_numpy().astype(float)
    radius, nbits = cfg["features"]["fp_radius"], cfg["features"]["fp_bits"]

    # Featurize once per dataset (cached)
    X = get_features(dataset_key, smiles, radius, nbits)

    tr, ca, te = _make_split(df, X, split_type, fracs, seed, sweep_q)
    if len(tr) < 20 or len(ca) < 10 or len(te) < 10:
        return {"skipped": True, "reason": "split too small",
                "n": [len(tr), len(ca), len(te)]}, []

    Xtr, Xca, Xte = X[tr], X[ca], X[te]
    ytr, yca, yte = y[tr], y[ca], y[te]

    # Model. The GNN consumes SMILES graphs; all other models consume fingerprints.
    # The conformal layer is model-agnostic and uses only the resulting predictions.
    if model_name == "gnn":
        from .models.gnn import GNNRegressor
        smi_tr, smi_ca, smi_te = smiles[tr], smiles[ca], smiles[te]
        reg = GNNRegressor(seed=seed).fit(smi_tr, ytr)
        yhat_tr = reg.predict(smi_tr); yhat_ca = reg.predict(smi_ca); yhat_te = reg.predict(smi_te)
        raw_std_te = None
    else:
        reg = make_regressor(model_name, seed=seed).fit(Xtr, ytr)
        yhat_tr = reg.predict(Xtr); yhat_ca, yhat_te = reg.predict(Xca), reg.predict(Xte)
        raw_std_te = reg.ensemble_std(Xte)
    resid_ca = np.abs(yca - yhat_ca)
    resid_tr = np.abs(ytr - yhat_tr)

    # Normalized-CP sigma (model-agnostic local residual scale)
    sigma_ca = knn_local_sigma(Xtr, resid_tr, Xca, k=10)
    sigma_te = knn_local_sigma(Xtr, resid_tr, Xte, k=10)

    # Applicability-domain coordinate a(x) (higher = more in-domain) + strata.
    # Default is max Tanimoto to TRAIN on ECFP; `ad_variant` selects alternative definitions
    # (mean-top5 ECFP, max FCFP, physicochemical-distance) for the AD-robustness experiment.
    ad_ca, ad_te = _ad_coordinate(ad_variant, dataset_key, smiles, X, tr, ca, te, radius, nbits)
    calib_bin, test_bin = ad_strata(ad_ca, ad_te, n_strata)
    sim_te_ca = tanimoto_matrix(Xte, Xca) if "localized" in methods else None
    value_bins = value_quartile_bins(yhat_te, n=min(4, n_strata if n_strata > 1 else 2))

    # Covariate-shift weights (only estimators needed by requested methods)
    clipp = tuple(cfg["weighting"]["clip_prob"]); cap = cfg["weighting"]["weight_cap"]
    disc_kind = cfg["weighting"]["discriminator"]
    weights = {}
    shift_auc = float("nan")
    if "weighted_disc" in methods or "adwcp" in methods:
        dr = DensityRatioWeights(kind=disc_kind, clip_prob=clipp, cap=cap, seed=seed).fit(Xtr, Xte)
        weights["ours"] = (dr.weights(Xca), dr.weights(Xte))
        shift_auc = dr.discriminator_auc(Xtr, Xte)
    if "weighted_logistic" in methods:
        dl = DensityRatioWeights(kind="logistic", clip_prob=clipp, cap=cap, seed=seed).fit(Xca, Xte)
        weights["codrug_logistic"] = (dl.weights(Xca), dl.weights(Xte))
    if "weighted_kde" in methods:
        dk = DensityRatioWeights(kind="kde", clip_prob=clipp, cap=cap, seed=seed).fit(Xca, Xte)
        weights["codrug_kde"] = (dk.weights(Xca), dk.weights(Xte))
    if "weighted_ad" in methods or "mwcp" in methods:
        # Robust 1-D density ratio along the applicability-domain coordinate
        # (similarity-to-training). Non-degenerate by construction; targets the exact
        # axis along which chemical covariate shift occurs. Estimated from the
        # unlabeled pool: calib AD scores (train dist) vs test AD scores (pool).
        from sklearn.linear_model import LogisticRegression
        a = np.concatenate([ad_ca, ad_te]).reshape(-1, 1)
        lab = np.concatenate([np.zeros(len(ad_ca)), np.ones(len(ad_te))])
        lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced").fit(a, lab)
        def _adw(advals):
            p = lr.predict_proba(advals.reshape(-1, 1))[:, 1]
            p = np.clip(p, clipp[0], clipp[1])
            w = (p / (1 - p)) * (len(ad_ca) / max(1, len(ad_te)))
            return np.clip(w, 1.0 / cap, cap)
        weights["ad1d"] = (_adw(ad_ca), _adw(ad_te))
    if "weighted_kmm" in methods:
        from .conformal.weighting import kmm_weights
        wk = kmm_weights(Xca, Xte, seed=seed)
        weights["kmm"] = (wk, np.zeros(len(yhat_te)))

    ad2_ca = ad2_te = None
    if "adcc_2d" in methods:
        # second applicability-domain coordinate: physicochemical nearest-training similarity
        ad2_ca, ad2_te = _ad_coordinate("physchem", dataset_key, smiles, X, tr, ca, te, radius, nbits)

    shift_calib = shift_test = test_fold = None
    if any(m.startswith("adcc_plus") for m in methods):
        # cross-fitted label-free shift score p(x)=P(pool|x): PCA-32 + logistic, train vs pool
        from sklearn.decomposition import PCA
        from sklearn.linear_model import LogisticRegression
        n_folds = 5
        rng_f = np.random.default_rng(seed + 7919)
        test_fold = rng_f.permutation(np.arange(len(te)) % n_folds)
        shift_calib = np.zeros((n_folds, len(ca))); shift_test = np.zeros(len(te))
        for k in range(n_folds):
            pool_k = Xte[test_fold != k]
            pca = PCA(n_components=min(32, Xtr.shape[1]), random_state=seed).fit(np.vstack([Xtr, pool_k]))
            Z = pca.transform(np.vstack([Xtr, pool_k]))
            lab = np.concatenate([np.zeros(len(Xtr)), np.ones(len(pool_k))])
            clf = LogisticRegression(max_iter=2000, C=0.1, class_weight="balanced").fit(Z, lab)
            shift_calib[k] = clf.predict_proba(pca.transform(Xca))[:, 1]
            shift_test[test_fold == k] = clf.predict_proba(pca.transform(Xte[test_fold == k]))[:, 1]

    def ctx_for(method):
        if method == "weighted_disc" or method == "adwcp":
            wc, wt = weights["ours"]
        elif method == "weighted_logistic":
            wc, wt = weights["codrug_logistic"]
        elif method == "weighted_kde":
            wc, wt = weights["codrug_kde"]
        elif method == "weighted_ad" or method == "mwcp":
            wc, wt = weights["ad1d"]
        elif method == "weighted_kmm":
            wc, wt = weights["kmm"]
        else:
            wc = np.ones(len(resid_ca)); wt = np.ones(len(yhat_te))
        return CPContext(level=level, yhat_calib=yhat_ca, y_calib=yca, yhat_test=yhat_te,
                         resid_calib=resid_ca, sigma_calib=sigma_ca, sigma_test=sigma_te,
                         ad_calib=ad_ca, ad_test=ad_te, calib_bin=calib_bin, test_bin=test_bin,
                         w_calib=wc, w_test=wt, raw_std_test=raw_std_te,
                         sim_te_ca=sim_te_ca, bandwidth=cfg["localized"]["bandwidth"],
                         shift_calib=shift_calib, shift_test=shift_test, test_fold=test_fold,
                         ad2_calib=ad2_ca, ad2_test=ad2_te)

    # Trivial full-range interval used to clip unbounded/degenerate conformal
    # intervals (an interval wider than the plausible property range is replaced by
    # the range itself). This keeps coverage meaningful and width comparable; the
    # fraction that saturates is reported as an efficiency penalty.
    y_lo_tr, y_hi_tr = float(ytr.min()), float(ytr.max())
    span = y_hi_tr - y_lo_tr

    rows = []
    arrays = {}
    for m in methods:
        lo, hi = run_method(m, ctx_for(m))
        hw_raw = (np.asarray(hi, float) - np.asarray(lo, float)) / 2  # unclipped half-width
        lo = np.maximum(lo, y_lo_tr)
        hi = np.minimum(hi, y_hi_tr)
        extra = {"dataset": dataset_key, "model": model_name, "seed": seed,
                 "split_type": split_type, "alpha": alpha, "sweep_q": sweep_q, "window": window,
                 "n_train": len(tr), "n_calib": len(ca), "n_test": len(te),
                 "shift_auc": shift_auc, "ad_test_median": float(np.median(ad_te))}
        wt_for_neff = ctx_for(m).w_test if m in ("weighted_disc", "adwcp", "weighted_ad", "mwcp",
                                                  "weighted_logistic", "weighted_kde") else None
        if m == "weighted_kmm":
            wt_for_neff = ctx_for(m).w_calib
        row = summarize(m, yte, lo, hi, test_bin, level, yhat=yhat_te,
                        value_bins=value_bins, w_test=wt_for_neff, extra=extra, span=span)
        # decision utility across requested selection fractions
        if decision_fracs:
            du = {}
            for f in decision_fracs:
                d = decision_utility(yte, yhat_te, lo, hi, select_frac=f, maximize=True)
                du[str(f)] = d
            row["decision"] = du
        rows.append(row)
        if return_arrays:
            arrays[m] = {"lo": lo, "hi": hi, "hw_raw": hw_raw}

    meta = {"dataset": dataset_key, "model": model_name, "seed": seed, "alpha": alpha,
            "split_type": split_type, "sweep_q": sweep_q, "shift_auc": shift_auc,
            "n": [len(tr), len(ca), len(te)], "runtime_s": round(time.time() - t0, 2)}
    if return_arrays:
        meta["arrays"] = arrays
        meta["y_test"] = yte; meta["yhat_test"] = yhat_te; meta["test_bin"] = test_bin
        meta["ad_test"] = ad_te
    return meta, rows
