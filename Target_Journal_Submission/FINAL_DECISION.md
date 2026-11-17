# Final Scientific Self-Decision (Phase 42 / GU10)

## Decision: **READY FOR SUBMISSION** — with disclosed residual novelty risk.

### Target journal
*Journal of Chemical Information and Modeling* (ACS). Q1 (secondary sources), JIF 6.4;
measured median submission-to-acceptance 84 days (n=390, PubMed history) — within the
≤100-day preference. Scope fit: strong (active UQ/applicability-domain/conformal stream).

### Title
*Applicability-Domain–Aware Conformal Prediction for Molecular Property Regression under Covariate Shift: When Correction Helps, When It Cannot, and a Deployment Diagnostic.*

### Readiness checklist (GU10)
1. Central contribution defensible — **Yes**, after repositioning: first systematic
   applicability-domain–*conditional* coverage study for molecular *regression* under
   covariate shift (scaffold + **temporal**); the ADE-CP quantile-extrapolation method; a
   label-free pre-deployment diagnostic; and the finding that no weighting method (incl.
   KMM) restores conditional coverage. Incremental-novelty risk disclosed.
2. Methodology sound — **Yes** (guarantees correctly scoped to exchangeability; weighted-CP
   validity verified under known ratio; ADE-CP extrapolation stated as heuristic).
3. Major experiments executed — **Yes** (4,652 result rows; 6 datasets; 4 models; 2 shift
   types; 12 CP methods incl. CoDrug-style, discriminator, and KMM weightings; controlled sweep).
4. Baselines fair and comprehensive — **Yes** (incl. the most relevant prior art, KMM-CP).
5. Statistical claims supported — **Yes** (paired Wilcoxon + Holm; bootstrap CIs; effect
   sizes; per-target + pooled; honest nulls reported).
6. Code–results consistency — **Yes** (every manuscript number cross-checked against the
   machine-readable outputs; 11/11 consistency checks pass).
7. References verified — **Yes** (33 refs via Crossref/arXiv; all cited inline 1–33;
   venue errors corrected).
8. No unresolved fatal flaw — **Yes** (the one fatal issue — missing KMM-CP — resolved by
   citation + baseline + repositioning).
9. Ten-reviewer process documented — **Yes** (10 perspectives + 2 corroborating AI-agent
   reviews; `REVIEW/`).
10. Improvement cycle(s) completed / limitation disclosed — **Yes** (one full documented
    review→fix→re-experiment→revise cycle; full 10× automated iteration limited by the
    environment's 5-hour usage cap, disclosed per GU8).
11. Journal requirements checked — **Yes** (ACS format, Data & Software Availability,
    declarations, SI; TOC graphic flagged as an author to-do).
12. All important claims have supporting evidence — **Yes** (claim–evidence map via the
    consistency audit; overclaims removed).

### Why READY despite residual risk
Every experimentally defensible issue raised in review is fixed; the science is sound,
reproducible, and honestly scoped. The dominant residual risk is *novelty perception*
relative to the CoDrug→KMM-CP weighting line (Risk 1 in `REJECTION_RISK_REPORT.md`). This is
a reviewer-judgment risk, not a correctness or completeness gap, and it has been minimized by
benchmarking against KMM and showing it does not solve the conditional-coverage problem this
paper targets. No paper can be guaranteed acceptance; this one has minimized identifiable
rejection reasons.

### Honest caveats carried into submission
- Novelty is partly incremental on the weighting axis; originality rests on regression +
  AD-conditional coverage + ADE-CP + temporal + diagnostic.
- Temporal evidence rests on two ChEMBL targets.
- Severe-shift impossibility regime is fundamental and reported, not solved.
- Journal quartile/JIF and acceptance timeline are from reputable aggregators / measured
  metadata, not Clarivate directly (disclosed in journal selection).

### Author to-do before upload (cannot be auto-generated)
- Fill author names, affiliations, ORCIDs, corresponding-author details, repository URL.
- Add a TOC/abstract graphic per ACS requirements.
- Convert equations from Markdown to the journal's equation format if the editor requests.
