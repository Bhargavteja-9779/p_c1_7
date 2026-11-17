# Review 5 — Dataset & Leakage Reviewer

**Perspective:** Can any information leak from test to training/calibration?

## Findings

**[MODERATE → addressed] L1. Transductive use of the test pool.** The PCA for the discriminator/KMM weights and the AD density ratio are fit using the unlabeled test (pool) covariates. This is legitimate transductive covariate-shift correction (only labels matter for validity, and no labels are used), but it must be stated so readers do not mistake it for leakage. *Resolution:* stated in §3.1/§3.5 and in the leakage audit; the deployment pool is exactly the unlabeled compounds to be screened, available prospectively.

**[PASS] L2. Scaffold-disjointness** verified (0 shared Bemis–Murcko scaffolds across train/calib/test, three seeds, all datasets) by `leakage_audit.py`.

**[PASS] L3. Temporal monotonicity** verified (max train/calib year ≤ min test year).

**[PASS] L4. De-duplication** by InChIKey (unique = total) for all datasets; ChEMBL activities aggregated by median pChEMBL, earliest year retained.

**[PASS] L5. AD score to training only; calibration labels never in test; weights use covariates only.** Confirmed in code and audit JSON.

**[MINOR] L6. ESOL count (1117 vs nominal 1128) and BACE (1510 vs 1513)** differ slightly from raw files due to RDKit sanitization/dedup. State this (done implicitly via dataset summaries; add a note).

## Recommendation: ACCEPT (leakage controls are thorough and audited). Add the transductive-pool clarification (done).
