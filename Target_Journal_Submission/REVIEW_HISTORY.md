# REVIEW_HISTORY

## Round 1 — Ten reviewer perspectives (GU5) + 2 corroborating AI-agent reviews
- Conducted 10 distinct reviewer perspectives (REVIEW/review_01..10) + 2 independent
  workflow agents (novelty, methodology) that corroborated them.
- **Most consequential finding:** missing prior art KMM-CP (Laghuvarapu et al. 2026) and
  Lee et al. (label shift); both verified via arXiv and cited. KMM-CP's premise (density-ratio
  instability) overlapped the claimed "negative result".
- **Revisions applied (one full documented cycle):**
  - Implemented KMM weighting baseline (cvxopt QP); re-ran scaffold+temporal (4,652 rows).
  - Finding: KMM does NOT restore conditional coverage (temporal worst-stratum 0.679 ≈ split),
    strengthening the thesis; ADR-CP beats KMM by +0.230 (Holm p=4e-5).
  - Repositioned contributions (C2 credited to CoDrug/KMM-CP; novelty = regression +
    conditional + ADE-CP + temporal + diagnostic).
  - Scoped ADE-CP guarantee (exchangeability only); added width caveat to decision utility;
    fixed venue errors (Hosni=ACS Omega etc.); cited all 33 refs inline.
  - Consistency audit: 11/11 manuscript numbers match data.
- Documented in REVIEW/final_audit.md.

## Execution-limit note (GU8)
Full 10×-cycle automated iteration was limited by the environment's 5-hour usage cap
(reviewer subagents failed twice at the cap). The substantive findings were resolved in the
main loop; readiness is judged on evidence, not cycle count (see FINAL_DECISION.md).
