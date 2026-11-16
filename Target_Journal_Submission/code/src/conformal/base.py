"""Helpers shared by conformal methods: model-agnostic local sigma; z-scores."""
from __future__ import annotations
import numpy as np
from sklearn.neighbors import NearestNeighbors
from scipy.stats import norm


def knn_local_sigma(X_train, resid_train, X_eval, k=10, floor=1e-3):
    """Model-agnostic heteroscedastic scale for normalized conformal:
    sigma(x) = mean |residual| over the k nearest TRAINING neighbours of x.
    Fitted on training residuals; evaluated for arbitrary points."""
    k = max(1, min(k, len(X_train)))
    nn = NearestNeighbors(n_neighbors=k).fit(X_train)
    _, idx = nn.kneighbors(X_eval)
    s = np.abs(resid_train)[idx].mean(axis=1)
    return np.maximum(s, floor)


def z_half_width(std, level):
    """Two-sided Gaussian half-width for a non-conformal reference interval."""
    alpha = 1.0 - level
    z = norm.ppf(1.0 - alpha / 2.0)
    return z * np.asarray(std, float)
