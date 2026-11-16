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


def get_features(dataset_key, smiles, radius, nbits):
    """Cache the dense fingerprint matrix per dataset (featurization is the same across
    all runs on a dataset, so compute it once)."""
    key = (dataset_key, radius, nbits)
    if key not in _FEATURE_CACHE:
        _FEATURE_CACHE[key] = ecfp_matrix(smiles, radius, nbits)
    return _FEATURE_CACHE[key]


def _make_split(df, X, split_type, fracs, seed, sweep_q=None):
    if split_type == "scaffold":
        return scaffold_split(df, fracs, seed)
    if split_type == "temporal":
        return temporal_split(df, fracs, seed)
    if split_type == "similarity":
        return similarity_shift_split(df, X, sweep_q, fracs, seed)
    raise KeyError(split_type)


def run_single(df, cfg, dataset_key, model_name, seed, split_type, alpha,
               methods=None, sweep_q=None, decision_fracs=None, return_arrays=False):
    """Execute one run. df must have columns smiles,y (and year for temporal)."""
    t0 = time.time()
    set_global_seed(seed)
    level = 1.0 - alpha
    methods = methods or cfg["conformal_methods"]
    fr = cfg["split"]
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

    # Model
    reg = make_regressor(model_name, seed=seed).fit(Xtr, ytr)
    yhat_ca, yhat_te = reg.predict(Xca), reg.predict(Xte)
    resid_ca = np.abs(yca - yhat_ca)
    resid_tr = np.abs(ytr - reg.predict(Xtr))

    # Normalized-CP sigma (model-agnostic local residual scale)
    sigma_ca = knn_local_sigma(Xtr, resid_tr, Xca, k=10)
    sigma_te = knn_local_sigma(Xtr, resid_tr, Xte, k=10)
    raw_std_te = reg.ensemble_std(Xte)

    # Applicability-domain similarity (max Tanimoto to TRAIN only) + strata
    ad_ca = max_sim_to_ref_matrix(Xca, Xtr)
    ad_te = max_sim_to_ref_matrix(Xte, Xtr)
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
    if "weighted_ad" in methods:
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

    def ctx_for(method):
        if method == "weighted_disc" or method == "adwcp":
            wc, wt = weights["ours"]
        elif method == "weighted_logistic":
            wc, wt = weights["codrug_logistic"]
        elif method == "weighted_kde":
            wc, wt = weights["codrug_kde"]
        elif method == "weighted_ad":
            wc, wt = weights["ad1d"]
        else:
            wc = np.ones(len(resid_ca)); wt = np.ones(len(yhat_te))
        return CPContext(level=level, yhat_calib=yhat_ca, y_calib=yca, yhat_test=yhat_te,
                         resid_calib=resid_ca, sigma_calib=sigma_ca, sigma_test=sigma_te,
                         ad_calib=ad_ca, ad_test=ad_te, calib_bin=calib_bin, test_bin=test_bin,
                         w_calib=wc, w_test=wt, raw_std_test=raw_std_te,
                         sim_te_ca=sim_te_ca, bandwidth=cfg["localized"]["bandwidth"])

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
        lo = np.maximum(lo, y_lo_tr)
        hi = np.minimum(hi, y_hi_tr)
        extra = {"dataset": dataset_key, "model": model_name, "seed": seed,
                 "split_type": split_type, "alpha": alpha, "sweep_q": sweep_q,
                 "n_train": len(tr), "n_calib": len(ca), "n_test": len(te),
                 "shift_auc": shift_auc, "ad_test_median": float(np.median(ad_te))}
        wt_for_neff = ctx_for(m).w_test if m in ("weighted_disc", "adwcp", "weighted_ad",
                                                  "weighted_logistic", "weighted_kde") else None
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
            arrays[m] = {"lo": lo, "hi": hi}

    meta = {"dataset": dataset_key, "model": model_name, "seed": seed, "alpha": alpha,
            "split_type": split_type, "sweep_q": sweep_q, "shift_auc": shift_auc,
            "n": [len(tr), len(ca), len(te)], "runtime_s": round(time.time() - t0, 2)}
    if return_arrays:
        meta["arrays"] = arrays
        meta["y_test"] = yte; meta["yhat_test"] = yhat_te; meta["test_bin"] = test_bin
        meta["ad_test"] = ad_te
    return meta, rows
