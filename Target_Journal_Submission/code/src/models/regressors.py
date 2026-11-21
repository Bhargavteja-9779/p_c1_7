"""Base regressors (model-agnostic conformal wraps any of these).
Classical: Ridge. ML: RandomForest, LightGBM. DL (CPU): fingerprint MLP."""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor

try:
    from lightgbm import LGBMRegressor
    _HAS_LGBM = True
except Exception:  # pragma: no cover
    _HAS_LGBM = False


class RegressorWrapper:
    """Uniform interface: fit / predict / ensemble_std (None if unavailable)."""
    def __init__(self, name: str, seed: int = 0, n_jobs: int = -1):
        self.name = name
        self.seed = seed
        self.n_jobs = n_jobs
        self.model = self._build()

    def _build(self):
        if self.name == "ridge":
            return Ridge(alpha=1.0, random_state=self.seed)
        if self.name == "rf":
            return RandomForestRegressor(n_estimators=200, max_depth=None,
                                         n_jobs=self.n_jobs, random_state=self.seed)
        if self.name == "lgbm":
            if not _HAS_LGBM:
                raise RuntimeError("lightgbm not installed")
            return LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=63,
                                 subsample=0.8, colsample_bytree=0.8, n_jobs=self.n_jobs,
                                 random_state=self.seed, verbose=-1)
        if self.name == "mlp":
            return MLPRegressor(hidden_layer_sizes=(512, 128), activation="relu",
                                alpha=1e-4, batch_size=64, learning_rate_init=1e-3,
                                max_iter=200, early_stopping=True, n_iter_no_change=15,
                                random_state=self.seed)
        raise KeyError(self.name)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return np.asarray(self.model.predict(X), dtype=float)

    def ensemble_std(self, X):
        """Per-tree std for RF; None otherwise (normalized CP then falls back to
        a model-agnostic kNN-local-residual sigma)."""
        if self.name == "rf":
            preds = np.stack([t.predict(X) for t in self.model.estimators_], axis=0)
            return preds.std(axis=0)
        return None


def make_regressor(name: str, seed: int = 0, n_jobs: int | None = None) -> RegressorWrapper:
    # CP_NJOBS lets parallel drivers pin one thread per worker (avoids OpenMP oversubscription)
    import os
    if n_jobs is None:
        n_jobs = int(os.environ.get("CP_NJOBS", "-1"))
    return RegressorWrapper(name, seed=seed, n_jobs=n_jobs)
