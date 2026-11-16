"""Covariate-shift splits (scaffold, temporal, controlled-similarity) and
applicability-domain stratification. Returns integer index arrays into the
dataset DataFrame; guarantees scaffold-disjointness / temporal monotonicity.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from rdkit import DataStructs


def _scaffold_groups(df: pd.DataFrame) -> dict:
    """Map scaffold -> list of row indices. Acyclic molecules (empty scaffold) are
    treated as singleton groups so they distribute across splits."""
    groups = {}
    for idx, scaf in zip(df.index, df["scaffold"].values):
        key = scaf if scaf else f"__acyclic__{idx}"
        groups.setdefault(key, []).append(idx)
    return groups


def scaffold_split(df: pd.DataFrame, fracs=(0.6, 0.2, 0.2), seed: int = 0):
    """Randomized scaffold-disjoint split -> (train_idx, calib_idx, test_idx).
    Whole scaffolds are assigned to a single split; order randomized by seed."""
    rng = np.random.default_rng(seed)
    groups = _scaffold_groups(df)
    keys = list(groups.keys())
    rng.shuffle(keys)
    n = len(df)
    targets = [fracs[0] * n, fracs[1] * n, fracs[2] * n]
    buckets = [[], [], []]
    counts = [0.0, 0.0, 0.0]
    # Assign each scaffold group to the split currently most under its target
    # (keeps all three near the target proportions while order is seed-randomized).
    for k in keys:
        members = groups[k]
        deficit = [(targets[i] - counts[i]) / max(1.0, targets[i]) for i in range(3)]
        j = int(np.argmax(deficit))
        buckets[j] += members
        counts[j] += len(members)
    return (np.array(sorted(buckets[0])), np.array(sorted(buckets[1])), np.array(sorted(buckets[2])))


def temporal_split(df: pd.DataFrame, fracs=(0.6, 0.2, 0.2), seed: int = 0):
    """Chronological split by document year. test = latest ~(1-train-calib) by year;
    train/calib = earlier pool, calib a random subset of it (exchangeable with train).
    Guarantees max(train/calib year) <= min(test year) at the compound level up to
    ties on the boundary year (reported by audit)."""
    assert "year" in df.columns, "temporal_split requires a 'year' column"
    order = df.sort_values(["year", "source_id"]).index.to_numpy()
    n = len(order)
    n_test = int(fracs[2] * n)
    pool = order[: n - n_test]           # earliest (train+calib)
    test = order[n - n_test:]            # latest
    rng = np.random.default_rng(seed)
    pool_sh = pool.copy()
    rng.shuffle(pool_sh)
    n_calib = int(fracs[1] * n)
    calib = pool_sh[:n_calib]
    train = pool_sh[n_calib:]
    return (np.array(sorted(train)), np.array(sorted(calib)), np.array(sorted(test)))


def similarity_shift_split(df, X, q: float, fracs=(0.6, 0.2, 0.2), seed: int = 0):
    """Controlled covariate-shift split with a monotone shift knob q in [0,1], along a
    genuine chemical-space axis (the first principal component of the fingerprints).

    Compounds are ranked by PC1. The test set is a mixture: a fraction q of it is taken
    from the high-PC1 tail (a displaced region of chemical space) and the remaining
    (1-q) at random; train/calibration are drawn from the rest. Shifting along a global
    variance direction makes the magnitude of covariate shift increase monotonically
    with q (verified by the train-vs-pool discriminator AUC). q=0 -> ~no shift;
    q=1 -> maximal shift. `X` is the dense fingerprint matrix aligned with df rows."""
    from sklearn.decomposition import PCA
    rng = np.random.default_rng(seed)
    idx = df.index.to_numpy()
    n = len(idx)
    n_test = int(fracs[2] * n)
    pc1 = PCA(n_components=1, random_state=seed).fit_transform(X).ravel()
    order_hi = np.argsort(-pc1)                       # highest PC1 first (the shifted tail)
    n_tail = int(round(q * n_test))
    tail = order_hi[:n_tail]
    tail_set = set(tail.tolist())
    rest = np.array([i for i in range(n) if i not in tail_set])
    rng.shuffle(rest)
    test_pos = np.concatenate([tail, rest[:max(0, n_test - n_tail)]]).astype(int)
    remaining = np.array([i for i in range(n) if i not in set(test_pos.tolist())])
    rng.shuffle(remaining)
    n_train = int(fracs[0] * n)
    train_pos = remaining[:n_train]
    calib_pos = remaining[n_train:]
    return (np.array(sorted(idx[train_pos])), np.array(sorted(idx[calib_pos])),
            np.array(sorted(idx[test_pos])))


def ad_strata(ad_calib: np.ndarray, ad_test: np.ndarray, n_strata: int = 4):
    """Assign calibration and test points to applicability-domain similarity bins.
    Bin edges = quantiles of calibration AD scores (so test is assigned by the same
    edges). Returns (calib_bin, test_bin) integer arrays in [0, n_strata-1],
    where bin 0 = least similar to training (most out-of-domain)."""
    qs = np.linspace(0, 1, n_strata + 1)[1:-1]
    edges = np.quantile(ad_calib, qs) if len(ad_calib) else np.array([])
    edges = np.unique(edges)
    calib_bin = np.digitize(ad_calib, edges)
    test_bin = np.digitize(ad_test, edges)
    return calib_bin.astype(int), test_bin.astype(int)
