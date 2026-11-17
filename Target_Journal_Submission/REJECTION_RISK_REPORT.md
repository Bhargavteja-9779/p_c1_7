# Rejection-Risk Report (Phase 41)

Honest assessment of residual risks for *J. Chem. Inf. Model.* submission. No "zero risk"
is claimed; acceptance is never guaranteed.

| # | Risk | Evidence | Severity | Mitigation | Fixed? |
|---|---|---|---|---|---|
| 1 | **Novelty judged incremental** vs the CoDrug→KMM-CP weighting line | KMM-CP (2026) and CoDrug (2023) do covariate-shift CP for molecules; ADR-CP/ADE-CP are instantiations of weighted CP / CQR | **High** | Repositioned around what is genuinely new: regression + AD-*conditional* coverage, ADE-CP extrapolation, temporal shift, label-free diagnostic; KMM added as baseline and shown insufficient for conditional coverage | Mitigated, not eliminated |
| 2 | Proposed methods do not beat the simple **Mondrian** baseline on scaffold shift | Pooled scaffold: proposed ≈ split ≈ Mondrian (p=1.0) | Medium | Framed honestly; the win is on temporal shift (ADR-CP ≫ Mondrian, p<0.001) and mild scaffold (ADE-CP sig.); diagnostic explains the regimes | Disclosed |
| 3 | **Temporal generalization** from two ChEMBL targets | VEGFR2, COX-2 only | Medium | Both positive; two models; per-target reported; controlled sweep corroborates; listed as limitation | Disclosed |
| 4 | **Methodology**: ADE-CP extrapolation lacks out-of-domain guarantee | By construction (CQR under exchangeability) | Medium | Stated explicitly; validated empirically; severe-shift failure reported | Disclosed |
| 5 | **Statistics**: pooled temporal test dependence | 2 models × 2 targets pooled | Low | Per-target primary; large effect sizes; caveat | Fixed |
| 6 | **Coverage via saturation** could mislead | Localized/KDE reach high coverage at 48–95% saturation | Low | Saturated-fraction reported; Pareto framing | Fixed |
| 7 | **Dataset** scope: ECFP4 only, small MoleculeNet sets | FreeSolv n=642 | Low | Multiple datasets/sizes; shift measured not assumed; limitation noted | Disclosed |
| 8 | **Reproducibility** gaps | — | Low | Public data, released tested code, one-command run, leakage audit, auto-generated tables/figures | Fixed |
| 9 | **Journal formatting** (ACS): TOC graphic, exact reference style | — | Low | DOCX follows ACS structure + Data/Software Availability; TOC graphic flagged as author to-do | Partial |
| 10 | **Citation** accuracy | — | Low | 33 refs Crossref/arXiv-verified; venue errors fixed | Fixed |
| 11 | **Journal quartile/JIF** from aggregators, not Clarivate | §journal_verification | Low (not a manuscript risk) | Disclosed in journal selection | Disclosed |
| 12 | **DL baseline**: no D-MPNN at scale | CPU budget | Low | Fingerprint MLP as DL baseline; methods model-agnostic; limitation noted | Disclosed |
| 13 | **Scope fit** to JCIM | Active UQ/AD stream in JCIM | Low | Strong fit documented | Fixed |

## Overall
The dominant residual risk is **novelty perception** (Risk 1): a reviewer who prizes a new
algorithm over a rigorous characterization + deployable tools + honest limits may rate it
MAJOR_REVISION. This has been minimized by (a) citing and benchmarking against the most
relevant prior art (KMM-CP, CoDrug), (b) demonstrating that none of the weighting methods —
including KMM — restores *conditional* coverage, which is the paper's distinct objective, and
(c) leading with the temporal result and the diagnostic. The scientific content is sound,
reproducible, and honestly scoped.
