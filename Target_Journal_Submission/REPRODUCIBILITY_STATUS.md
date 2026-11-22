# REPRODUCIBILITY_STATUS

| Item | Status |
|---|---|
| Public datasets, auto-download (MoleculeNet, ChEMBL) | YES |
| Deterministic seeds (config; explicit model seeds) | YES |
| One-command run (`python run_all.py --mode full`) | YES |
| Resumable (run_meta.jsonl skip-completed) | YES |
| Tables/figures auto-generated (no hand-entered numbers) | YES |
| Manuscript↔data consistency (11/11 checks) | YES |
| Unit tests (tests/, 10 pass) | YES |
| Leakage audit (experiments/leakage_audit.py, all pass) | YES |
| CPU-only, no GPU | YES |
| Pinned deps (requirements.txt, environment.yml) | YES |
| KMM baseline (cvxopt) | YES |
| 39 references verified, all cited inline in order of first citation | YES |

Residual: Chemprop/D-MPNN not trained at scale (CPU budget) — DL baseline is fingerprint MLP;
methods are model-agnostic wrappers (limitation disclosed). cvxopt added to requirements.


## Additional analyses
- 13 ChEMBL panel targets (auto-download), 3 temporal windows, per-target + target-level stats.
- MW-CP (group-conditional guarantee), KMM baseline (cvxopt), GNN baseline (torch CPU), FCFP ablation.
- Panel leakage audit (results/leakage_audit_panel.json): all 13 targets pass.
- Manuscript↔data consistency: pooled-panel numbers 6/6 match; title reframed to benchmark.
- New deps: cvxopt, torch (CPU). `run_all.py --mode full` orchestrates panel/gnn/ablation/diagnostic.
