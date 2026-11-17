# Rejection-Risk Report (Round 2 — rigorous benchmark framing)

Honest assessment for *J. Chem. Inf. Model.* No "zero risk"; acceptance never guaranteed.
Framing: a multi-target benchmark establishing the AD-axis principle + a group-conditional
guarantee (MW-CP) + a cautionary diagnostic refutation.

| # | Risk | Evidence | Severity | Mitigation | Status |
|---|---|---|---|---|---|
| 1 | **Novelty perception** — the empirically best method (ADR-CP) is a simple instantiation of weighted conformal | ADR-CP = Tibshirani WCP on a 1-D AD feature | **High** | Reframed as a benchmark + principle paper; the contribution is the *finding* (where-to-correct beats how, 13/13 targets), the *guarantee* (MW-CP, Theorem 1), and the *diagnostic refutation*; comparable in kind to recent JCIM UQ benchmarks (Parrondo-Pizarro 2026; Guo 2027) | Disclosed, not eliminated |
| 2 | **Guaranteed method does not win** | MW-CP < ADR-CP (Δ +0.073, p<0.001) | Medium | Presented honestly as a guarantee–efficiency trade-off; MW-CP is the certified option, ADR-CP the deployed-coverage option | Disclosed |
| 3 | **Diagnostic refuted** | target-level ρ≈0/+0.65; LOTO false-safe 0.54 | Medium (handled) | Reported as a *cautionary* contribution (refute a single-threshold rule), not a proposed tool; corrects the split-level artifact | Fixed/honest |
| 4 | Temporal generalization | 13 targets, 6 families, 3 windows, per-target + target-level stats | Low | Broad, rigorous; GNN + FCFP robustness | Strong |
| 5 | MW-CP guarantee correctness | Theorem 1 + proof; assumption check (within-stratum AUC) | Low | Group-conditional (not pointwise) stated precisely | Fixed |
| 6 | Coverage-via-saturation | localized/KDE reach coverage only by saturating | Low | saturated-fraction reported; excluded from "restoration" claims | Fixed |
| 7 | Baselines completeness | split, normalized, Mondrian, localized, discriminator, KDE, KMM, ADE-CP | Low | KMM-CP (closest prior art) implemented & benchmarked | Fixed |
| 8 | Reproducibility | public data, released tested code, one-command run, leakage audit, auto tables/figures, 6/6 number-consistency checks | Low | Strong | Fixed |
| 9 | ACS format | ACS structure, Data/Software Availability, declarations, SI | Low | Author placeholders + TOC graphic flagged as author to-do | Partial |
| 10 | Citations | 33 refs Crossref/arXiv-verified, all cited inline; Guo/KMM-CP/Lee included | Low | Verified | Fixed |
| 11 | Numerical consistency (E1–E6) | E1 raw_ensemble removed; E2 labeled; E3 per-target+CI; E4 width caveat; E5 FCFP ablation; E6 per-model | Low | All addressed | Fixed |

## Overall
The science is sound, broad, reproducible, and honestly scoped. The dominant risk is that a
JCIM reviewer prizing a *dominant novel algorithm* over a rigorous benchmark + guarantee +
honest negatives rates it a major revision or reject on novelty grounds. The authors have
chosen to submit under the benchmark framing with this risk disclosed. All identifiable
*correctness, completeness, and reproducibility* rejection reasons have been minimized.
