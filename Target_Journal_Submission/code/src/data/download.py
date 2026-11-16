"""Download raw datasets (public sources). Idempotent and cached under data/raw/.

MoleculeNet regression CSVs are mirrored by DeepChem on S3.
ChEMBL activities are pulled from the official EBI REST API (paginated), keeping
canonical_smiles, pchembl_value and document_year for temporal splitting.
"""
from __future__ import annotations
import json, time, urllib.request, urllib.parse
from pathlib import Path
from ..utils import ROOT, get_logger

log = get_logger()

MOLNET = {
    "esol": ("https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv",
             "delaney-processed.csv"),
    "freesolv": ("https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/SAMPL.csv", "SAMPL.csv"),
    "lipophilicity": ("https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/Lipophilicity.csv",
                      "Lipophilicity.csv"),
    "bace": ("https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/bace.csv", "bace.csv"),
}


def _raw_dir() -> Path:
    d = ROOT / "data" / "raw"
    d.mkdir(parents=True, exist_ok=True)
    return d


def download_molnet(name: str) -> Path:
    url, fname = MOLNET[name]
    out = _raw_dir() / fname
    if out.exists() and out.stat().st_size > 0:
        return out
    log.info(f"Downloading {name} <- {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out.write_bytes(r.read())
    return out


def download_chembl_target(target_chembl_id: str, standard_type: str = "IC50",
                           max_records: int = 20000) -> Path:
    """Pull pChEMBL activities for a target. Cached as JSONL."""
    out = _raw_dir() / f"chembl_{target_chembl_id}_{standard_type}.jsonl"
    if out.exists() and out.stat().st_size > 0:
        return out
    base = "https://www.ebi.ac.uk/chembl/api/data/activity"
    fields = ["canonical_smiles", "pchembl_value", "document_year",
              "standard_type", "standard_relation", "molecule_chembl_id"]
    got, offset, limit = [], 0, 1000
    while len(got) < max_records:
        q = {"target_chembl_id": target_chembl_id, "standard_type": standard_type,
             "pchembl_value__isnull": "false", "limit": limit, "offset": offset,
             "format": "json"}
        url = base + "?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    d = json.load(r)
                break
            except Exception as e:  # pragma: no cover
                log.warning(f"ChEMBL retry {attempt}: {e}")
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError("ChEMBL API failed repeatedly")
        acts = d.get("activities", [])
        if not acts:
            break
        for a in acts:
            got.append({k: a.get(k) for k in fields})
        offset += limit
        if d.get("page_meta", {}).get("next") is None:
            break
        time.sleep(0.3)
    with open(out, "w") as f:
        for rec in got:
            f.write(json.dumps(rec) + "\n")
    log.info(f"ChEMBL {target_chembl_id} {standard_type}: {len(got)} activity records -> {out.name}")
    return out
