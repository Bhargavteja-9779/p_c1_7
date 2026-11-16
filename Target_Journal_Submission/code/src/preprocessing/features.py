"""Molecular featurization: ECFP4 bit vectors + Tanimoto utilities."""
from __future__ import annotations
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

_GEN_CACHE = {}


def _gen(radius: int, nbits: int):
    key = (radius, nbits)
    if key not in _GEN_CACHE:
        _GEN_CACHE[key] = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=nbits)
    return _GEN_CACHE[key]


def ecfp_bitvects(smiles_list, radius: int = 2, nbits: int = 2048):
    """Return list of RDKit ExplicitBitVect (for fast Tanimoto)."""
    gen = _gen(radius, nbits)
    out = []
    for s in smiles_list:
        m = Chem.MolFromSmiles(s)
        if m is None:
            out.append(None)
        else:
            out.append(gen.GetFingerprint(m))
    return out


def ecfp_matrix(smiles_list, radius: int = 2, nbits: int = 2048) -> np.ndarray:
    """Dense 0/1 numpy matrix (n, nbits)."""
    bvs = ecfp_bitvects(smiles_list, radius, nbits)
    X = np.zeros((len(bvs), nbits), dtype=np.float32)
    for i, bv in enumerate(bvs):
        if bv is not None:
            arr = np.zeros((nbits,), dtype=np.int8)
            DataStructs.ConvertToNumpyArray(bv, arr)
            X[i] = arr
    return X


def max_tanimoto_to_ref(query_bvs, ref_bvs) -> np.ndarray:
    """For each query fingerprint, max Tanimoto similarity to the reference set.
    Used as the applicability-domain (similarity-to-training) score."""
    ref = [b for b in ref_bvs if b is not None]
    out = np.zeros(len(query_bvs), dtype=np.float32)
    for i, q in enumerate(query_bvs):
        if q is None or not ref:
            out[i] = 0.0
        else:
            sims = DataStructs.BulkTanimotoSimilarity(q, ref)
            out[i] = max(sims) if sims else 0.0
    return out


def tanimoto_matrix(Xq: np.ndarray, Xr: np.ndarray) -> np.ndarray:
    """Vectorized Tanimoto similarity between two sets of binary fingerprints
    (dense 0/1 matrices). Returns (n_q, n_r). Uses BLAS matmul -> fast."""
    Xq = Xq.astype(np.float32); Xr = Xr.astype(np.float32)
    inter = Xq @ Xr.T
    aq = Xq.sum(axis=1)[:, None]
    ar = Xr.sum(axis=1)[None, :]
    union = aq + ar - inter
    with np.errstate(divide="ignore", invalid="ignore"):
        sim = np.where(union > 0, inter / union, 0.0)
    return sim.astype(np.float32)


def max_sim_to_ref_matrix(Xq: np.ndarray, Xr: np.ndarray, chunk: int = 512) -> np.ndarray:
    """Max Tanimoto of each query to the reference set, computed in chunks to bound
    memory. Equivalent to max_tanimoto_to_ref but vectorized."""
    out = np.zeros(len(Xq), dtype=np.float32)
    for i in range(0, len(Xq), chunk):
        out[i:i+chunk] = tanimoto_matrix(Xq[i:i+chunk], Xr).max(axis=1)
    return out


def mean_topk_tanimoto_to_ref(query_bvs, ref_bvs, k: int = 5) -> np.ndarray:
    """Mean of top-k Tanimoto similarities to the reference set (smoother AD score)."""
    ref = [b for b in ref_bvs if b is not None]
    out = np.zeros(len(query_bvs), dtype=np.float32)
    for i, q in enumerate(query_bvs):
        if q is None or not ref:
            out[i] = 0.0
            continue
        sims = np.array(DataStructs.BulkTanimotoSimilarity(q, ref))
        kk = min(k, len(sims))
        out[i] = float(np.sort(sims)[::-1][:kk].mean())
    return out
