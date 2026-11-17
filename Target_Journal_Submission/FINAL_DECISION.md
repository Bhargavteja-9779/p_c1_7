# Final Scientific Self-Decision (Round 2, after major redevelopment)

## Decision: **READY to submit as a rigorous benchmark + principle paper** (authors' chosen framing), with the novelty risk disclosed below. **NOT** to be submitted as a dominant-novel-method paper.

The paper is reframed (title: "Where to Correct Matters More Than How: A Multi-Target Benchmark …") around the evidence that actually holds: a large, honest, reproducible benchmark establishing the applicability-domain-axis principle, a method with a group-conditional guarantee (MW-CP) presented with its honest trade-off, and a cautionary diagnostic refutation. This is scientifically sound and reproducible; its main residual risk is novelty perception (the empirically best method, ADR-CP, is simple). The authors have elected to finalize and submit under this framing.

The reviewer required (N1) a genuinely new AD-aware method that (N4–N6) demonstrably improves across ≥10 targets / ≥5 families / multiple windows, plus (N8) a validated diagnostic. We executed that program in full and report the outcome honestly, including where it contradicts our earlier draft.

### What the rigorous expansion established (all verified, reproducible)
- **A clear, significant empirical principle (C2).** Across **13 ChEMBL targets / 6 families** under temporal shift (3 windows), aligning the covariate-shift correction with the one-dimensional applicability-domain axis — **ADR-CP** — restores worst-stratum coverage better than every deployable baseline: pooled 0.839 vs split 0.670, Mondrian 0.732, KMM 0.715; **improves over split on 13/13 targets** (Holm p<0.001, rank-biserial 1.00). This holds across four model families and a **graph neural network**, and under an alternative fingerprint. This is a robust, non-obvious result (simple 1-D correction beats RKHS/KDE/latent weighting and stratification).
- **A guaranteed method (C3 / Theorem 1).** **MW-CP** has a finite-sample **group-conditional** coverage guarantee under covariate shift — the first for molecular property prediction. It is sound and beats split/KMM/Mondrian.

### What did NOT survive validation (reported, not hidden)
1. **The novel method does not win.** MW-CP (guaranteed) is significantly **worse than the simple ADR-CP** (ADR−MW median Δ +0.073, p<0.001): stratification fragments the calibration set. So the empirically best method is ADR-CP, which is an *instantiation of weighted conformal* — exactly the novelty level the reviewer judged insufficient. We did not find a novel algorithm that both carries a stronger guarantee and beats ADR-CP.
2. **The diagnostic does not generalize (N8 failed).** Target-level validation gives Spearman(AUC, achievable coverage) ρ = −0.02 (p=0.96) across 13 targets; leave-one-target-out false-safe rate 0.54. The earlier ρ≈−0.56 was an artifact of non-independent repeated splits (the exact flaw the reviewer flagged). The universal-threshold deployment rule is **withdrawn**.

### Requirement scorecard
- N1 (genuinely new method): **MW-CP delivered with a guarantee**, but it does not outperform the simple baseline — partial.
- N2 (rigorous guarantee statement): **met** (Theorem 1, assumptions explicit, group-conditional not pointwise).
- N3 (differentiate Guo/CoDrug/KMM-CP): **met** (subsection + table; KMM benchmarked and beaten on conditional coverage).
- N4 (≥10 temporal targets): **met** (13). N5 (≥5 families): **met** (6). N6 (multiple windows): **met** (3).
- N7 (graph model): **met** (D-MPNN-style GNN; finding holds).
- N8 (validated diagnostic): **not met** — validation *refuted* it; reported honestly.
- N9 (ablations): met (method axis + representation + model). N10 (stats/reproducibility): met. N11 (fix inconsistencies/overstatement): met. N12 (ACS package + code): met except author/repo placeholders and TOC graphic.

### Recommendation (for the user to decide)
Two honest paths:
- **(A) Reframe and submit as a rigorous benchmark + principle + guaranteed-option paper.** Lead with the AD-axis principle (ADR-CP, 13/13 targets), present MW-CP as the certified option with an explicit guarantee–efficiency trade-off, and present the diagnostic *refutation* as a cautionary contribution. This is scientifically sound and comparable in kind to recent JCIM UQ benchmarks, but carries **genuine novelty risk** because the best method is simple and the guaranteed method does not win.
- **(B) Continue method development** to find a novel procedure that beats ADR-CP while keeping a stronger-than-marginal guarantee (e.g., full-calibration conditional-coverage methods à la Gibbs et al. 2023 adapted to the AD axis). Uncertain payoff; our quantile-regression attempt (ADE-CP) did not beat ADR-CP.

We do **not** recommend submitting the current version as if it presented a dominant novel method — that would misrepresent the evidence. The honest, defensible contribution is path (A); whether it clears JCIM's novelty bar is a judgment the authors must make.

No fabrication; no overclaim; all numbers trace to released code and `results/`.
