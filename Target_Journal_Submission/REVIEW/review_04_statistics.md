# Review 4 — Statistical Reviewer

**Perspective:** Validity of the statistical inference.

## Findings

**[MAJOR → addressed] S1. Pooling independence for the temporal test.** The pooled temporal Wilcoxon (n=20) mixes 2 targets × 2 models × 5 seeds; the two models on the same target/seed are not independent, mildly inflating the effective n. *Resolution:* per-target results are reported (VEGFR2: ADR-CP 0.913; COX-2: 0.843) and the pooled test is presented as a secondary summary; effect sizes are large (rank-biserial 0.9–1.0) so the conclusion is robust to the dependence. Text notes the caveat.

**[MODERATE → addressed] S2. Multiple comparisons.** Holm–Bonferroni is applied across the full family of proposed-vs-baseline comparisons (`statistics.py`). Significance requires Holm p<0.05 AND a bootstrap CI excluding zero. Correct.

**[MODERATE] S3. Scaffold pooled null reported honestly.** Pooled over 4 scaffold datasets, proposed ≈ split (p=1.0); per-dataset, lipophilicity ADE-CP is significant (p<1e-4). Both reported (§6.4, §S1, §S8) — no cherry-picking.

**[MINOR] S4.** Seeds pre-declared {0..19}; bootstrap CIs (2000 resamples) and rank-biserial effect sizes reported. Good. State the unit of analysis explicitly (done, §3.7).

## Recommendation: MINOR_REVISION. Inference is sound; add the pooling-dependence caveat (done).
