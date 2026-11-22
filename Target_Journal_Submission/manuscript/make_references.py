"""Format verified_references.json into an ACS-style numbered reference list, in a
specified citation order. Only verified entries are emitted; anything unverified raises.
Writes manuscript/references_acs.md and references_order.json.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFS = json.load(open(HERE.parent / "supplementary" / "literature" / "verified_references.json"))

# Citation order = first appearance in the manuscript. Keys must exist in REFS.
ORDER = [
    "cortes_deepconf_2019",   # 1  AD/reliability in cheminformatics (also deep confidence)
    "papadopoulos_2008",      # 2  inductive/split CP
    "vovk_2005",              # 3  CP + Mondrian foundations
    "lei_2018",               # 4  distribution-free regression CP
    "norinder_2014",          # 5  CP in QSAR
    "svensson_2018",          # 6  conformal regression QSAR (normalized)
    "angelopoulos_bates",     # 7  gentle intro / risk control
    "li_cfr_2024",            # 8  conformal GNN ADMET (JCIM)
    "harris_2026",            # 9  domain-classifier UQ filter (JCIM)
    "morger_2022",            # 10 data drifts / recalibration
    "hosni_2026",             # 11 explicit AD flags reliability
    "parrondo_2026",          # 12 UQ-under-shift benchmark (JCIM)
    "tibshirani_wcp_2019",    # 13 weighted CP
    "codrug_2023",            # 14 CoDrug (classification weighted CP)
    "guo_2027",               # 15 scaffold-shift conditional failure (regression)
    "barber_limits",          # 16 impossibility of conditional coverage
    "romano_cqr_2019",        # 17 CQR
    "guan_lcp",               # 18 localized CP
    "orsolic_dad_2023",       # 19 dynamic AD / local conformal
    "klarner_qsavi_2023",     # 20 Bayesian covariate shift
    "li_partition_2026",      # 21 data-set partitioning (JCIM)
    "moleculenet_2018",       # 22 MoleculeNet
    "delaney_esol_2004",      # 23 ESOL
    "freesolv_2014",          # 24 FreeSolv
    "bace_2016",              # 25 BACE
    "chembl_2019",            # 26 ChEMBL
    "ash_2025",               # 27 method-comparison protocols (JCIM)
    "merz_editorial_2020",    # 28 data/software sharing editorial (JCIM)
    "kmmcp_2026",             # 29 KMM-CP (covariate-shift CP for molecules)
    "sklearn_2011",           # 30 scikit-learn
    "lightgbm_2017",          # 31 LightGBM
    "rdkit",                  # 32 RDKit
    "lee_labelshift_2025",    # 33 molecular CP under label shift
    "gibbs_ccc_2025",         # 34 conformal prediction with conditional guarantees
    "koenker_1978",           # 35 regression quantiles
    "jung_multivalid_2023",   # 36 batch multivalid conformal
    "srivastava_2026",        # 37 conformal under scaffold shift audit (preprint)
    "koetter_2025",           # 38 robust UQ for molecular property prediction (JCIM 2025)
    "fooladi_2025",           # 39 OOD robustness evaluation (JCIM 2025)
]


def _clean(s):
    return " ".join(str(s).split()) if s else ""


def _authors_acs(a):
    a = _clean(a)
    if not a:
        return "[authors]"
    return a if a.endswith(".") else a + "."


def fmt(ref):
    a = _authors_acs(ref.get("authors", ""))
    title = _clean(ref.get("title", "")).rstrip(".")
    cont = _clean(ref.get("container", ""))
    yr = ref.get("year", "")
    vol = ref.get("volume"); pg = ref.get("page"); doi = ref.get("doi"); arx = ref.get("arxiv")
    v = ref.get("verified")
    if ref.get("type") == "book":
        pub = ref.get("publisher", ""); city = ref.get("city", "")
        return f"{a} {title}; {pub}: {city}, {yr}."
    if v == "crossref":
        s = f"{a} {title}. *{cont}* **{yr}**"
        if vol: s += f", *{vol}*"
        if pg: s += f", {pg}"
        s += "."
        if doi: s += f" DOI: {doi}."
        return s
    if v == "arxiv":
        return f"{a} {title}. *{cont}* **{yr}**. arXiv:{arx}."
    if v in ("no_doi_jmlr", "no_doi_neurips"):
        s = f"{a} {title}. *{cont}* **{yr}**"
        if vol: s += f", *{vol}*"
        if pg: s += f", {pg}"
        return s + "."
    if v == "software":
        return f"{a} {title}. {cont} ({yr})."
    if v == "crossref" and ref.get("type") == "book":
        pub = ref.get("publisher", ""); city = ref.get("city", "")
        return f"{a} {title}; {pub}: {city}, {yr}."
    raise ValueError(f"Unverified reference: {ref}")


def main():
    missing = [k for k in ORDER if k not in REFS]
    if missing:
        raise SystemExit(f"Missing refs in database: {missing}")
    lines = []
    for i, k in enumerate(ORDER, 1):
        lines.append(f"{i}. {fmt(REFS[k])}")
    out = "\n".join(lines)
    (HERE / "references_acs.md").write_text("## References\n\n" + out + "\n")
    json.dump({k: i for i, k in enumerate(ORDER, 1)}, open(HERE / "references_order.json", "w"), indent=1)
    print(out)
    print(f"\n{len(ORDER)} references formatted.")


if __name__ == "__main__":
    main()
