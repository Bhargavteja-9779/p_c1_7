"""RDKit standardization, canonicalization, InChIKey, Bemis-Murcko scaffold."""
from __future__ import annotations
from functools import lru_cache
from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

_lfc = rdMolStandardize.LargestFragmentChooser()
_uncharger = rdMolStandardize.Uncharger()


def standardize_smiles(smiles: str):
    """Return (canonical_smiles, inchikey) after salt stripping + neutralization,
    or (None, None) if the SMILES cannot be parsed."""
    if smiles is None:
        return None, None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None
    try:
        mol = _lfc.choose(mol)
        mol = _uncharger.uncharge(mol)
        Chem.SanitizeMol(mol)
    except Exception:
        return None, None
    try:
        can = Chem.MolToSmiles(mol, canonical=True)
        ik = Chem.MolToInchiKey(mol)
    except Exception:
        return None, None
    if not can or ik is None:
        return None, None
    return can, ik


def bemis_murcko_scaffold(smiles: str, generic: bool = True) -> str:
    """Generic (graph) Bemis-Murcko scaffold SMILES; '' for acyclic molecules."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        if generic:
            scaf = MurckoScaffold.MakeScaffoldGeneric(scaf)
        s = Chem.MolToSmiles(scaf, canonical=True)
        return s if s else ""
    except Exception:
        return ""
