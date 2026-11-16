# Applicability-Domain–Aware Conformal Prediction for Molecular Property Regression under Covariate Shift

Reproducible code for the study of **conditional (applicability-domain-stratified) coverage**
of conformal prediction for molecular property **regression** under scaffold and temporal
**covariate shift**, including two proposed AD-axis methods (**ADR-CP**, AD-reweighted;
**ADE-CP**, AD-extrapolated), CoDrug-style weighting baselines, and a label-free
**shift-magnitude diagnostic**.

All results, tables and figures are generated from code — no number is hand-entered.

## 1. Environment

CPU-only; no GPU required. Developed with Python 3.13.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt           # or: conda env create -f environment.yml
```

Key packages (pinned in `requirements.txt`): numpy, pandas, scipy, scikit-learn,
lightgbm, rdkit, matplotlib, statsmodels, python-docx.

## 2. Data (downloaded automatically, public)

- **MoleculeNet regression** (ESOL, FreeSolv, Lipophilicity, BACE) via the DeepChem S3 mirror.
- **ChEMBL** target activities (VEGFR2/CHEMBL279, COX-2/CHEMBL230) via the EBI REST API,
  keeping `canonical_smiles`, `pchembl_value`, `document_year` for temporal splits.

Raw files cache under `data/raw/`; cleaned, de-duplicated tables under `data/processed/`.
Preprocessing: RDKit standardization (largest fragment, neutralize), canonical SMILES,
InChIKey de-duplication (median y; earliest year for temporal), Bemis–Murcko scaffolds.

## 3. Reproduce

```bash
python run_all.py --mode quick     # ~5-10 min pipeline check (ESOL+FreeSolv, LightGBM, 3 seeds)
python run_all.py --mode full      # full study (all datasets, models, 20 seeds, 2 alphas)
python run_all.py --mode full --stage analysis   # regenerate stats/tables/figures from saved runs
```

Experiments are **resumable**: completed runs are recorded in `results/run_meta.jsonl`
and skipped on re-invocation, so an interrupted run continues where it stopped.

Outputs:
- `results/raw_results.csv` — one row per (method × dataset × model × seed × α × split).
- `results/metrics.json`, `results/statistics.json` — aggregates + paired tests.
- `results/leakage_audit.json` — Phase-8 data-leakage checks.
- `tables/*.csv`, `tables/*.md` — publication tables.
- `figures/*.png`, `figures/*.pdf` — publication figures.

## 4. Tests and audits

```bash
python tests/test_conformal.py            # conformal + weighting correctness (synthetic)
python experiments/leakage_audit.py       # scaffold-disjointness, temporal monotonicity, dedup, no label leakage
```

## 5. Code layout

```
config/default.yaml        all hyperparameters, datasets, seeds, methods
run_all.py                 orchestrator (quick/full; experiments -> stats -> tables -> figures)
src/
  utils.py                 seeding, hardware detect, config, IO
  data/                    download.py (MoleculeNet, ChEMBL), datasets.py (load + preprocess)
  preprocessing/           standardize.py, features.py (ECFP4 + vectorized Tanimoto), splits.py
  models/regressors.py     Ridge, RandomForest, LightGBM, fingerprint-MLP (uniform interface)
  conformal/               weighting.py (density ratios + weighted quantile), base.py, methods.py
  evaluation/metrics.py    coverage, conditional coverage, width, saturation, decision utility
  statistics/              tests.py (Wilcoxon, Holm, bootstrap), aggregate.py
  visualization/           plots.py (figures), tables.py (tables)
experiments/               run_experiments.py, leakage_audit.py
tests/                     unit tests
```

## 6. Methods implemented

Baselines: raw ensemble (B0), split CP (B1), normalized CP (B2), Mondrian-AD CP (B3),
localized/Tanimoto-kernel CP (B4), covariate-shift weighted CP with a fingerprint
discriminator (B5) and with CoDrug-style logistic/KDE density ratios.
Proposed: **ADR-CP** (`weighted_ad`, 1-D AD-coordinate density-ratio weighting) and
**ADE-CP** (`adecp`, AD conformal quantile extrapolation).

Weights are estimated from the **unlabeled deployment pool** (test fingerprints without
labels), so every method is deployable in a prospective screen.

## 7. Determinism

All randomness is seeded (`seed_list` in the config). Model seeds are passed explicitly.
`Date.now`/wall-clock randomness is not used in any experimental path.
