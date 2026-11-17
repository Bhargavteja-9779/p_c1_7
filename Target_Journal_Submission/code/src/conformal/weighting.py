"""Covariate-shift weight estimation and weighted conformal quantiles.

Implements the weighted split-conformal threshold of Tibshirani et al. (2019):
for a test point with weight w_t and calibration points with weights w_i and
nonconformity scores s_i, the (1-alpha) threshold is the smallest s_(k) whose
cumulative normalized weight p_i = w_i / (sum_j w_j + w_t) reaches 1-alpha; if the
total calibration mass is below 1-alpha the interval is unbounded (+inf).
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import PCA
from sklearn.neighbors import KernelDensity


def weighted_quantile_threshold(scores, w_calib, w_test_scalar, level):
    """Smallest calibration score whose cumulative normalized weight >= level,
    including the test-point atom. Returns +inf if unattainable. O(n log n)."""
    scores = np.asarray(scores, float)
    w_calib = np.asarray(w_calib, float)
    order = np.argsort(scores)
    s = scores[order]
    w = w_calib[order]
    total = w.sum() + float(w_test_scalar)
    if total <= 0:
        return np.inf
    cum = np.cumsum(w) / total
    idx = np.searchsorted(cum, level, side="left")
    if idx >= len(s):
        return np.inf
    return float(s[idx])


def unweighted_quantile_threshold(scores, level):
    """Standard split-conformal threshold with finite-sample (n+1) correction."""
    scores = np.asarray(scores, float)
    n = len(scores)
    if n == 0:
        return np.inf
    k = int(np.ceil((n + 1) * level))
    if k > n:
        return np.inf
    return float(np.sort(scores)[k - 1])


def kmm_weights(X_calib, X_pool, pca_dim=32, B=30.0, eps=None, seed=0, max_src=900):
    """Kernel Mean Matching importance weights (Huang et al. 2007), as used by
    KMM-CP (Laghuvarapu et al. 2026). Returns per-calibration-point weights w_i that
    match the calibration (source) mean embedding to the pool (target) mean embedding
    in an RBF RKHS: min_w 1/2 wᵀKw − κᵀw s.t. 0≤w_i≤B, |mean(w)−1|≤eps.
    Computed on PCA-reduced fingerprints for tractability; capped source size for the QP."""
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import rbf_kernel
    from cvxopt import matrix, solvers
    solvers.options["show_progress"] = False
    rng = np.random.default_rng(seed)
    d = min(pca_dim, X_calib.shape[1], max(2, len(X_calib) + len(X_pool) - 1))
    pca = PCA(n_components=d, random_state=seed).fit(np.vstack([X_calib, X_pool]))
    Zc_full = pca.transform(X_calib); Zp = pca.transform(X_pool)
    # subsample source points for the QP if very large; weights for the rest via NN copy
    if len(Zc_full) > max_src:
        idx = rng.choice(len(Zc_full), max_src, replace=False)
    else:
        idx = np.arange(len(Zc_full))
    Zc = Zc_full[idx]
    n, m = len(Zc), len(Zp)
    # RBF bandwidth: median heuristic on source
    from scipy.spatial.distance import pdist
    med = np.median(pdist(Zc)) if n > 1 else 1.0
    gamma = 1.0 / (2.0 * (med ** 2) + 1e-9)
    K = rbf_kernel(Zc, Zc, gamma=gamma).astype(np.double)
    K += 1e-6 * np.eye(n)
    kappa = (float(n) / m) * rbf_kernel(Zc, Zp, gamma=gamma).sum(axis=1).astype(np.double)
    if eps is None:
        eps = B / np.sqrt(n)
    P = matrix(K); q = matrix(-kappa)
    # constraints: 0<=w<=B  and  |sum(w)-n|<=n*eps
    G = np.vstack([np.eye(n), -np.eye(n), np.ones((1, n)), -np.ones((1, n))])
    h = np.concatenate([B * np.ones(n), np.zeros(n), [n * (1 + eps)], [-n * (1 - eps)]])
    try:
        sol = solvers.qp(P, q, matrix(G), matrix(h))
        w_sub = np.array(sol["x"]).ravel()
        w_sub = np.clip(w_sub, 0, B)
    except Exception:
        w_sub = np.ones(n)
    # map back to all calibration points (NN in Z space for the held-out source rows)
    w_full = np.ones(len(Zc_full))
    w_full[idx] = w_sub
    if len(idx) < len(Zc_full):
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=1).fit(Zc)
        miss = np.setdiff1d(np.arange(len(Zc_full)), idx)
        _, j = nn.kneighbors(Zc_full[miss])
        w_full[miss] = w_sub[j.ravel()]
    w_full = np.maximum(w_full, 1e-6)
    return w_full


class DensityRatioWeights:
    """Estimate w(x) = p_pool(x)/p_train(x) from the UNLABELED deployment pool.

    kind='logistic' / 'gbm': train a probabilistic classifier to distinguish
      train (0) from pool (1); w = (p/(1-p)) * (n_train/n_pool), with p clipped.
    kind='kde': PCA-reduce, fit Gaussian KDE on train and pool, w = p_pool/p_train.
    All weights are capped to [1/cap, cap]. Uses only covariates X (no labels)."""

    def __init__(self, kind="logistic", clip_prob=(0.01, 0.99), cap=50.0, seed=0,
                 pca_dim=32, C=0.1):
        self.kind = kind
        self.clip_prob = clip_prob
        self.cap = float(cap)
        self.seed = seed
        self.pca_dim = pca_dim
        self.C = C                   # strong regularization: high-dim fingerprints are
        self._fitted = False         # trivially separable, which would make weights degenerate

    def _reduce_fit(self, X_train, X_pool):
        """PCA-reduce before the discriminator. Raw 2048-bit fingerprints are almost
        perfectly separable between any two finite samples, so a classifier on them
        yields degenerate (exploding) density ratios. Reducing dimensionality makes
        the estimated ratio smooth and the weighted intervals finite."""
        d = min(self.pca_dim, X_train.shape[1], max(2, len(X_train) + len(X_pool) - 1))
        self.pca = PCA(n_components=d, random_state=self.seed).fit(np.vstack([X_train, X_pool]))
        return self.pca.transform(X_train), self.pca.transform(X_pool)

    def fit(self, X_train, X_pool):
        self.n_train = len(X_train)
        self.n_pool = len(X_pool)
        if self.kind in ("logistic", "gbm"):
            Zt, Zp = self._reduce_fit(X_train, X_pool)
            X = np.vstack([Zt, Zp])
            y = np.concatenate([np.zeros(len(Zt)), np.ones(len(Zp))])
            if self.kind == "logistic":
                base = LogisticRegression(max_iter=2000, C=self.C, class_weight="balanced")
            else:
                base = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05,
                                                      max_iter=150, l2_regularization=1.0,
                                                      random_state=self.seed, class_weight="balanced")
            # probability calibration via internal CV (guards against over-confident p)
            n_min = int(min((y == 0).sum(), (y == 1).sum()))
            cv = max(2, min(3, n_min))
            try:
                self.clf = CalibratedClassifierCV(base, method="isotonic", cv=cv)
                self.clf.fit(X, y)
            except Exception:
                self.clf = base.fit(X, y)
            self._prior = len(X_train) / max(1, len(X_pool))
        elif self.kind == "kde":
            d = min(self.pca_dim, X_train.shape[1], max(2, len(X_train) - 1))
            self.pca = PCA(n_components=d, random_state=self.seed).fit(np.vstack([X_train, X_pool]))
            Zt, Zp = self.pca.transform(X_train), self.pca.transform(X_pool)
            bw = np.std(np.vstack([Zt, Zp])) * (len(Zt) ** (-1.0 / (d + 4))) + 1e-6
            self.kde_tr = KernelDensity(bandwidth=bw).fit(Zt)
            self.kde_po = KernelDensity(bandwidth=bw).fit(Zp)
        else:
            raise KeyError(self.kind)
        self._fitted = True
        return self

    def weights(self, X):
        assert self._fitted
        if self.kind in ("logistic", "gbm"):
            p = self.clf.predict_proba(self.pca.transform(X))[:, 1]
            lo, hi = self.clip_prob
            p = np.clip(p, lo, hi)
            w = (p / (1.0 - p)) * self._prior
        else:  # kde
            Z = self.pca.transform(X)
            lp_tr = self.kde_tr.score_samples(Z)
            lp_po = self.kde_po.score_samples(Z)
            w = np.exp(np.clip(lp_po - lp_tr, -10, 10))
        w = np.clip(w, 1.0 / self.cap, self.cap)
        return w.astype(float)

    def discriminator_auc(self, X_train, X_pool):
        """Empirical shift strength: AUC of train-vs-pool separation (0.5 = no shift)."""
        from sklearn.metrics import roc_auc_score
        if self.kind == "kde":
            return float("nan")
        Z = np.vstack([self.pca.transform(X_train), self.pca.transform(X_pool)])
        y = np.concatenate([np.zeros(len(X_train)), np.ones(len(X_pool))])
        p = self.clf.predict_proba(Z)[:, 1]
        try:
            return float(roc_auc_score(y, p))
        except Exception:
            return float("nan")
