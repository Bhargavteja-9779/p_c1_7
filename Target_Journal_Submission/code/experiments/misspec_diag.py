"""Round-6: label-free misspecification statistic suggested by Proposition 2.
For each panel run (same splits as run_panel_adcc), estimate the covariate-shift ratio
w(x)=dP_pool/dP_cal with a cross-fitted fingerprint discriminator (calibration vs pool; PCA-32
logistic), then compute
   delta_F  = min_beta  E_cal | w_hat - phi(a)^T beta |    (distance of w to the ADCC class)
   delta_0  = E_cal | w_hat - 1 |                          (distance to 'no shift')
Proposition 2 bounds the marginal under-coverage of ADCC-CP by delta_F (and of an
uncorrected method by delta_0). No labels are used. -> results/misspec_diag.jsonl"""
from __future__ import annotations
import sys, json, os, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np
from scipy.optimize import linprog
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from src.utils import load_config
from src.data.datasets import load_panel_target
from src.pipeline import get_features, _make_split
from src.preprocessing.features import max_sim_to_ref_matrix
from src.conformal.methods import _ad_edges, ad_basis

WINDOWS = {"w40": (0.50, 0.10, 0.40), "w30": (0.60, 0.10, 0.30), "w20": (0.70, 0.10, 0.20)}


def lad(y, P):
    n, d = P.shape
    c = np.concatenate([np.zeros(d), np.ones(n), np.ones(n)]) / n
    A = np.hstack([P, np.eye(n), -np.eye(n)])
    r = linprog(c, A_eq=A, b_eq=y, bounds=[(None, None)] * d + [(0, None)] * (2 * n), method="highs")
    return float(r.fun)


def one(key, seed, wl, cfg, df):
    X = get_features(f"panel_{key}", df["smiles"].to_numpy(), cfg["features"]["fp_radius"], cfg["features"]["fp_bits"])
    tr, ca, te = _make_split(df, X, "temporal", WINDOWS[wl], seed)
    Z = PCA(n_components=32, random_state=seed).fit_transform(np.vstack([X[ca], X[te]]).astype(float))
    lab = np.r_[np.zeros(len(ca)), np.ones(len(te))]
    p = np.zeros(len(lab))
    for a, b in StratifiedKFold(5, shuffle=True, random_state=seed).split(Z, lab):
        clf = LogisticRegression(max_iter=2000, C=0.1).fit(Z[a], lab[a])
        p[b] = clf.predict_proba(Z[b])[:, 1]
    p = np.clip(p[: len(ca)], 0.01, 0.99)
    w = p / (1 - p) * len(ca) / len(te); w = np.clip(w, 0.02, 50); w = w / w.mean()
    a_ca = max_sim_to_ref_matrix(X[ca], X[tr]).astype(float)
    edges = _ad_edges(a_ca, 4)
    P = ad_basis(np.round(a_ca, 2), edges, "spline")
    return {"target": key, "seed": seed, "window": wl, "delta_F": lad(w, P),
            "delta_0": float(np.mean(np.abs(w - 1))),
            "delta_grp": lad(w, ad_basis(np.round(a_ca, 2), edges, "grp"))}


def main():
    cfg = load_config("config/default.yaml")
    out = Path("results/misspec_diag.jsonl")
    with open(out, "w") as fh:
        for key in cfg["chembl_panel"]:
            df = load_panel_target(key, cfg)
            for seed, wl in itertools.product([0, 1, 2], WINDOWS):
                r = one(key, seed, wl, cfg, df)
                fh.write(json.dumps(r) + "\n"); fh.flush()
                print(r, flush=True)


if __name__ == "__main__":
    main()
