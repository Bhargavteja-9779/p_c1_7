# REPRODUCIBILITY_STATUS

| Item | Status |
|---|---|
| Public datasets, auto-download | YES (MoleculeNet S3, ChEMBL API) |
| Deterministic seeds | YES (config seed_list; model seeds explicit) |
| One-command run | YES (`python run_all.py --mode full`) |
| Resumable | YES (run_meta.jsonl skip-completed) |
| Tables/figures auto-generated | YES (no hand-entered numbers) |
| Unit tests | YES (tests/test_conformal.py, 6 pass) |
| Leakage audit | YES (experiments/leakage_audit.py, all pass) |
| CPU-only | YES (no GPU dependency) |
| Pinned deps | YES (requirements.txt, environment.yml) |

Residual: Chemprop/D-MPNN not trained (CPU budget) — DL baseline is a fingerprint MLP;
noted as a limitation.
