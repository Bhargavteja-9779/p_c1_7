# ROUND 7 RESUME CHECKPOINT (read this first on "continue")

User asks (2026-11-22): improvise more, push novelty "very very high", make it unrejectable,
compare with MORE recent JCIM papers + add positioning, code "made available on request"
(NOT public repo — user overrode), first author P N Bhargav Teja + 2nd placeholder,
no funding, no competing interest. User also OK'd reframing toward a REAL-WORLD problem
(reliable prospective screening / triage) if it helps acceptance. Do everything in AUTO.

Branch: claude/beautiful-mccarthy-s05jaz. Work dir: /home/user/p_c1_7/Target_Journal_Submission.
Deps: `pip install -q numpy pandas scikit-learn scipy rdkit lightgbm python-docx pyyaml cvxopt matplotlib statsmodels`
Run conformal panel methods with OMP_NUM_THREADS=1 CP_NJOBS=1 and spawn Pool (see run_panel_adcc.py).

## DONE in round 7 (committed)
- Code availability -> "made available on request" in manuscript/draft_v6_tail.md + manuscript/cover_letter.md.
- Verified 2 NEW recent JCIM-2025 refs (abstracts confirmed via Europe PMC):
  * Koetter, Singh, Matter, Hessler, Grebner. "Upgrading Reliability in Molecular Property Prediction by
    Robust Quantification of Uncertainty from Machine Learning Models." JCIM 2025, 65, 10819-10831.
    DOI 10.1021/acs.jcim.5c00464. (UQ fails in under-represented/steep-SAR regions; UQ eval is
    split-dependent; proposes a robust UQ method.) -> use as motivation + recent reliability-method cite.
  * Fooladi, Vu, Mathea, Kirchmair. "Evaluating ML Models for Molecular Property Prediction:
    Performance and Robustness on Out-of-Distribution Data." JCIM 2025, 65, 9871-9891.
    DOI 10.1021/acs.jcim.5c00475. (14 models x 8 datasets x 10 splits; scaffold splits can understate
    OOD difficulty.) -> use to justify TEMPORAL-shift focus + held-out/target-level design.
  NOTE: NOT yet added to supplementary/literature/verified_references.json or make_references.py ORDER.
- NEW METHOD implemented (code only, not yet run on panel):
  * src/conformal/methods.py: ad_basis_2d(), method_adcc_2d() = MULTI-COORDINATE ADCC-CP
    (additive piecewise-linear splines over TWO AD coordinates: structural max-Tanimoto a(x) +
    physicochemical nearest-train similarity a2(x)); registered "adcc_2d" in DISPATCH.
    CPContext got ad2_calib/ad2_test fields; pipeline.run_single computes physchem coord when
    "adcc_2d" in methods and passes ad2_* through. (Also pre-existing adcc_plus, adcc_pk variants.)

## NEXT STEP (do in order)
1. Quick-test adcc_2d on 2-3 targets (herg, mor, dpp4) vs split/weighted_ad/adcc to confirm it runs
   and see if it helps (test was interrupted; rerun: methods=['split','weighted_ad','adcc','adcc_2d'],
   fracs=(0.6,0.1,0.3), window w30, lgbm seed 0). Use OMP_NUM_THREADS=1.
2. Add adcc_2d to experiments/run_panel_adcc.py METHODS and RE-RUN full panel (234 runs) resumably
   into results/panel_adcc_rows.jsonl (delete old file OR add only adcc_2d via a separate runner +
   merge). Re-run experiments/analyze_adcc.py (add adcc_2d to its NAMES/order lists).
3. alpha=0.2 (80%) robustness: small panel run (or reuse) to show method not alpha-specific. Optional
   if time: add to SI.
4. Add 2 new refs to verified_references.json (crossref-verified DOIs above) + make_references.py ORDER
   (append gibbs stays #34..srivastava #37; add koetter_2025 #38, fooladi_2025 #39). Re-run make_references.py.
5. JCIM POSITIONING: add a comparison table (manuscript) vs recent JCIM papers:
   Norinder2014(ref5), Svensson2018(ref6), Li/conformalized-GNN 2024(ref8), Harris2026(ref9),
   Parrondo2026(ref12), Koetter2025(new), Fooladi2025(new), + Guo(15). Columns: task(reg/clf),
   shift type(scaffold/temporal/OOD), coverage target(marginal/conditional), guarantee?,
   needs ratio estimation?, deployable from unlabeled pool? Show ADCC-CP is the only row with
   finite-sample conditional-family guarantee + no estimation. Put as [[TABLE:table_jcim_positioning]]
   in draft_v6_related or results; write CSV tables/table_jcim_positioning.csv.
6. STRENGTHEN related work (draft_v6_methods.md "## 2. Related Work") with Koetter + Fooladi.
7. THEORY+: add Corollary (ADCC interval is the pointwise-TIGHTEST set satisfying the function-class
   coverage constraints => efficiency-optimal among class-valid methods) to draft_v6_methods.md.
8. REAL-WORLD framing: add/strengthen an application subsection in results or discussion — reliable
   PROSPECTIVE SCREENING / triage: the AD calibration curve as a per-compound reliability schedule;
   honest interval on the top-ranked (most novel) compounds a team would synthesize. (Earlier rounds
   had a screening analysis in code; keep it honest: risk-aware, same ranking.) Tie to Koetter/Fooladi.
9. assemble_v6.py -> manuscript_final.md (fills tokens from results/adcc_stats.json). Add any new tokens.
   build_si_v6.py -> SI. build_docx.py for manuscript+SI; libreoffice --headless --convert-to pdf.
   Rebuild cover_letter.docx/pdf. Rebuild SUBMISSION_PACKAGE + JCIM_Submission_Package.zip.
10. Update FINAL_DECISION.md, REJECTION_RISK_REPORT.md, REVIEW_HISTORY.md (round 7). Commit+push each stage.
11. Confirm metadata: first author "P. N. Bhargav Teja", 2nd author placeholder, Funding=none,
    competing interest=none, code "available on request" (already set).

## Attribution for commits (new account may show a different model line; use whatever the session's
## system reminder says). Previously: Co-Authored-By: Claude Opus <noreply@anthropic.com> + Claude-Session URL.

## Key current numbers (13-target held-out panel, from results/adcc_stats.json): ADCC-CP S0 cov 0.880
## vs split 0.686 (13/13, p=0.0015); novel decile 0.949 vs split 0.619; beats ADR-CP on novel decile
## +0.030 (12/13, p=0.0015); ADR-CP higher aggregate worst-stratum 0.846 vs 0.771 (by over-covering).
## Validity controls confirm theory. 10 unit tests + leakage audit pass.

## adcc_2d quick-test RESULT (confirms it helps S0; already verified runs):
# herg: adcc s0 0.931 -> adcc_2d s0 0.941 (w 2.79->2.90)
# mor:  adcc s0 0.918 -> adcc_2d s0 0.930 (w 4.21->4.58)
# dpp4: adcc s0 0.862 -> adcc_2d s0 0.901 (w 3.70->3.97)
# => multi-coordinate ADCC-CP raises most-out-of-domain coverage at modest extra width. FEATURE IT.
# So step 1 (test) is DONE; start at step 2 (full panel run incl adcc_2d).
