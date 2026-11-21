# Applicability-Domain Conditional Conformal Prediction (ADCC-CP)

Reproducible code for **ADCC-CP**, a conformal method giving molecular-property models
distribution-free prediction intervals that stay valid under chemical-space (covariate) shift
**without estimating any density ratio**, by calibrating over a class of applicability-domain
shifts. Includes all baselines (split, normalized, Mondrian, localized, discriminator/KDE/KMM-
weighted conformal) and the prior AD-axis estimated-weight methods (ADR-CP, MW-CP), evaluated
across four MoleculeNet scaffold datasets and thirteen time-stamped ChEMBL targets under
temporal shift.

All results, tables and figures are generated from code — no number is hand-entered.
Released under the MIT license (`LICENSE`).

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

**Proposed — ADCC-CP (`adcc`): Applicability-Domain Conditional Conformal prediction.**
Function-class conditional conformal (Gibbs–Cherian–Candès, JRSSB 2025) over the class of
piecewise-linear functions of the applicability-domain coordinate a(x)=max Tanimoto to training.
Gives finite-sample coverage simultaneously (i) marginally, (ii) locally at every similarity
level, and (iii) under every covariate shift whose density ratio along a(x) lies in the class —
**without estimating any density ratio** (`src/conformal/methods.py:conditional_conformal_threshold`,
`ad_basis`). Pre-registered function class = continuous linear spline; ablation variants
`adcc_grp` (indicator / Mondrian-equivalent), `adcc_pl` (piecewise-linear), `adcc_norm`
(normalized score).

Baselines: split CP, normalized CP, Mondrian-AD CP, localized/Tanimoto-kernel CP; covariate-shift
weighted CP with a fingerprint discriminator, CoDrug-style logistic/KDE density ratios, and
KMM (kernel mean matching, KMM-CP-style). Prior-work AD-axis methods ADR-CP (`weighted_ad`) and
MW-CP (`mwcp`) are retained as the strongest estimated-weight comparators.

Reproduce the ADCC-CP study:
```bash
python experiments/dev_adcc.py 5              # function-class selection (scaffold dev data)
python experiments/run_panel_adcc.py 4        # held-out 13-target temporal panel
python experiments/validity_adcc.py 4         # exchangeable + known-shift validity controls
python experiments/misspec_diag.py            # label-free misspecification diagnostic delta_F
python experiments/analyze_adcc.py            # target-level stats, tables, figures
python tests/test_adcc.py                     # ADCC-CP coverage unit tests
```

Weights (for the estimated-weight baselines) are estimated from the **unlabeled deployment pool**,
so every method is deployable in a prospective screen.

## 7. Determinism

All randomness is seeded (`seed_list` in the config). Model seeds are passed explicitly.
`Date.now`/wall-clock randomness is not used in any experimental path.
