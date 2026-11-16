"""Load + preprocess each dataset into a canonical DataFrame:
columns = [smiles, y, inchikey, scaffold, year(optional), source_id].
Deduplicates by InChIKey (median y; earliest year for temporal sets).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ..utils import get_logger
from .download import download_molnet, download_chembl_target
from ..preprocessing.standardize import standardize_smiles, bemis_murcko_scaffold

log = get_logger()

# MoleculeNet column maps: (smiles_col, y_col)
MOLNET_COLS = {
    "esol": ("smiles", "measured log solubility in mols per litre"),
    "freesolv": ("smiles", "expt"),
    "lipophilicity": ("smiles", "exp"),
    "bace": ("mol", "pIC50"),
}
DATASET_META = {
    "esol": {"name": "ESOL (aqueous solubility)", "unit": "log mol/L", "shift": "scaffold"},
    "freesolv": {"name": "FreeSolv (hydration free energy)", "unit": "kcal/mol", "shift": "scaffold"},
    "lipophilicity": {"name": "Lipophilicity (logD 7.4)", "unit": "log D", "shift": "scaffold"},
    "bace": {"name": "BACE-1 inhibition", "unit": "pIC50", "shift": "scaffold"},
    "chembl_vegfr2": {"name": "VEGFR2/KDR (CHEMBL279)", "unit": "pChEMBL", "shift": "temporal"},
    "chembl_cox2": {"name": "COX-2 (CHEMBL230)", "unit": "pChEMBL", "shift": "temporal"},
}


def _finalize(df: pd.DataFrame, temporal: bool) -> pd.DataFrame:
    """Standardize SMILES, compute InChIKey + scaffold, dedup, drop invalid."""
    recs = []
    for _, row in df.iterrows():
        can, ik = standardize_smiles(row["smiles"])
        if can is None or not np.isfinite(row["y"]):
            continue
        rec = {"smiles": can, "y": float(row["y"]), "inchikey": ik}
        if temporal:
            rec["year"] = int(row["year"]) if pd.notna(row.get("year")) else None
        recs.append(rec)
    out = pd.DataFrame(recs)
    if out.empty:
        return out
    # Deduplicate by InChIKey
    if temporal:
        agg = out.groupby("inchikey").agg(
            smiles=("smiles", "first"), y=("y", "median"),
            year=("year", "min")).reset_index()
        agg = agg.dropna(subset=["year"])
        agg["year"] = agg["year"].astype(int)
    else:
        agg = out.groupby("inchikey").agg(
            smiles=("smiles", "first"), y=("y", "median")).reset_index()
    agg["scaffold"] = agg["smiles"].apply(lambda s: bemis_murcko_scaffold(s, generic=False))
    agg = agg.reset_index(drop=True)
    agg["source_id"] = agg.index
    return agg


def load_dataset(key: str, cfg: dict) -> pd.DataFrame:
    cache = Path(cfg["paths"]["data_dir"]) / "processed" / f"{key}.csv"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return pd.read_csv(cache)

    if key in MOLNET_COLS:
        path = download_molnet(key)
        raw = pd.read_csv(path)
        scol, ycol = MOLNET_COLS[key]
        df = pd.DataFrame({"smiles": raw[scol].astype(str), "y": pd.to_numeric(raw[ycol], errors="coerce")})
        out = _finalize(df, temporal=False)
    elif key in ("chembl_vegfr2", "chembl_cox2"):
        tgt = cfg["chembl_targets"][key]
        path = download_chembl_target(tgt["target_chembl_id"], tgt["standard_type"])
        rows = [json.loads(l) for l in open(path)]
        raw = pd.DataFrame(rows)
        raw = raw.rename(columns={"canonical_smiles": "smiles"})
        raw["y"] = pd.to_numeric(raw["pchembl_value"], errors="coerce")
        raw["year"] = pd.to_numeric(raw["document_year"], errors="coerce")
        raw = raw.dropna(subset=["smiles", "y"])
        out = _finalize(raw[["smiles", "y", "year"]], temporal=True)
    else:
        raise KeyError(f"Unknown dataset {key}")

    out.to_csv(cache, index=False)
    log.info(f"{key}: {len(out)} unique molecules "
             f"(y mean={out['y'].mean():.2f} sd={out['y'].std():.2f})")
    return out


def dataset_summary(key: str, df: pd.DataFrame) -> dict:
    d = {"key": key, "name": DATASET_META[key]["name"], "unit": DATASET_META[key]["unit"],
         "shift": DATASET_META[key]["shift"], "n": int(len(df)),
         "n_scaffolds": int(df["scaffold"].nunique()),
         "y_mean": float(df["y"].mean()), "y_std": float(df["y"].std()),
         "y_min": float(df["y"].min()), "y_max": float(df["y"].max())}
    if "year" in df.columns:
        d.update({"year_min": int(df["year"].min()), "year_max": int(df["year"].max())})
    return d
