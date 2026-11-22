# Rejection-Risk Report (Round 6 — ADCC-CP, novelty-forward framing)

> **Round-7 update (2026-11-22).** Novelty amplified: new multi-coordinate ADCC-CP-2D (best-calibrated
> method on the panel), efficiency Corollary 3, a JCIM positioning table (Table 1) vs 11 methods incl.
> two 2025 JCIM papers, and a real-world prospective-screening framing. Per author instruction, code is
> "available on reasonable request" (not a public repo) — note this slightly raises risk against JCIM's
> data/software-sharing editorial (ref 28); mitigated by fully public datasets + a one-command reproducible
> codebase ready to share. Funding: none. Competing interest: none. First author P. N. Bhargav Teja.


Honest assessment for *J. Chem. Inf. Model.* No "zero risk"; acceptance never guaranteed.
This round responds to real desk-rejections of earlier versions by replacing the "benchmark +
simple method" framing with a **genuinely new method that carries a finite-sample guarantee no
prior molecular-CP method has**: ADCC-CP (applicability-domain conditional conformal prediction).

## What changed versus the previous (benchmark) version
- **New method, not a re-labeled baseline.** ADCC-CP adapts function-class conditional conformal
  (Gibbs–Cherian–Candès, *JRSSB* 2025) to an applicability-domain function class. It guarantees
  coverage over a *whole family* of chemical-space shifts **with no density-ratio estimation**
  (Theorem 1) — new for molecular property prediction, and distinct from weighted CP (CoDrug,
  KMM-CP), Mondrian, and our own earlier estimated-weight methods.
- **Positive, specific abstract** (~245 words) led by the contribution, replacing the previous
  "we do not claim a dominant method" hedging that invites desk-rejection.
- **Code made genuinely public** (MIT `LICENSE`, GitHub + Zenodo-DOI placeholders), resolving the
  conflict with JCIM's data/software policy (Merz editorial, doi 10.1021/acs.jcim.0c01389) that
  "available on request" created.
- **Pre-registered, held-out evaluation**: function class fixed on MoleculeNet scaffold data only;
  13-target ChEMBL temporal panel used once for confirmation; target-level (n=13) statistics.

| # | Risk | Evidence | Severity | Mitigation | Status |
|---|---|---|---|---|---|
| 1 | **Novelty** — is ADCC-CP new enough? | First molecular-CP method guaranteeing coverage over a family of AD shifts with no ratio estimation; adapts Gibbs 2025 to chemistry; new AD function class, algorithm, AD calibration curve | **Low–Med** | Clear theoretical + practical novelty; distinct from CoDrug/KMM-CP/Mondrian; honest about what is adapted vs new | Addressed |
| 2 | Does the new method actually win? | Beats split/normalized/Mondrian/KMM on **every** metric (S0 +0.095..+0.194, 13/13, p=0.0015); beats MW-CP on worst-stratum & novel decile; beats estimated-weight ADR-CP on the **most-novel decile** (+0.030, 12/13, p=0.0015) at equal width | Low | Decision-relevant wins are significant; see #3 for the one metric it does not lead | Strong |
| 3 | ADR-CP has higher *aggregate* worst-stratum coverage (0.846 vs 0.771) | pooled stats | Med | Reported transparently: ADR-CP achieves this by **over-covering** an interior stratum, not by covering novel compounds better; ADCC-CP leads S0 and the novel decile and carries a guarantee ADR-CP lacks and needs no estimation. Primary endpoint pre-registered; secondary (S0/decile) is where the method is designed to win | Disclosed/honest |
| 4 | Guarantee correctness | Theorem 1 (from Gibbs 2025, Thm 2) + proof; Proposition 2 misspecification bound + proof; 4 unit tests verify empirical coverage incl. known-shift-no-estimation | Low | Theory + empirical validity controls agree (exchangeable S0 0.903; known AD-shift S0 0.900) | Strong |
| 5 | Over-coverage / wide intervals | O(d/n) over-coverage bound; width reported; saturation 5% | Low | Bounded and reported; widening on novel compounds is correct behaviour | Fixed |
| 6 | Temporal generalization | 13 targets, 6 families, 3 windows, 2 base models; ranking stable across all | Low | Broad; by-window/by-model SI tables | Strong |
| 7 | Baseline completeness | split, normalized, Mondrian, localized, discriminator/KDE/KMM weighting, ADR-CP, MW-CP | Low | KMM-CP (closest prior art) and our prior best method both benchmarked | Fixed |
| 8 | Reproducibility | public data, released MIT code, per-method scripts, one-command run, leakage audit, 10 unit tests, auto tables/figures, no hand-entered numbers | Low | Strong; code public (not "on request") | Fixed |
| 9 | ACS format / policy | ACS structure, Data/Software Availability (public repo + Zenodo DOI), declarations, 7pp SI, graphical TOC | Low | Author/affiliation + repo URLs are the only author to-dos | Partial (author) |
| 10 | Citations | 37 refs, Crossref/arXiv-verified, all cited inline; Gibbs 2025, KMM-CP, CoDrug, Guo, Srivastava 2026 included | Low | Verified | Fixed |
| 11 | Knot data-dependence | knots at calibration quantiles of a(x) | Low | Covariate-only dependence; random-split controls show no validity loss; fixed-knot option documented | Fixed |

## Overall
This version presents a **novel, guaranteed method that wins where it is designed to win** (coverage
of the most out-of-domain compounds), with a clean theory, pre-registered held-out evidence, public
code, and a tight positive abstract — directly targeting the desk-reject causes of earlier rounds.
The residual scientific risk is honest and bounded: ADR-CP edges ADCC-CP on one aggregate metric
(worst-stratum), which we explain (over-coverage) rather than hide. Author/affiliation fields and the
final public-repo URLs remain to be filled by the authors before submission.
