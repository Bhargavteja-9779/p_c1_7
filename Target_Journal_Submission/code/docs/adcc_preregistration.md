# ADCC-CP — variant selection record (pre-registration of the held-out evaluation)

**Date locked:** 2026-11-21, before any ADCC-CP run on the ChEMBL temporal panel.

## Selection protocol
Development data = the four MoleculeNet scaffold-split datasets only (ESOL, FreeSolv,
Lipophilicity, BACE; LightGBM; seeds 0–4; α = 0.10). The 13-target ChEMBL temporal panel was
**held out** and never used to choose among ADCC variants. Raw rows: `results/dev_adcc_rows.jsonl`
(script `experiments/dev_adcc.py`).

Candidate function classes F_AD (all functions of the AD coordinate a(x), rounded to 0.01):
| variant | basis | d |
|---|---|---|
| grp | AD-stratum indicators (Mondrian-equivalent) | 4 |
| pl | stratum indicators + within-stratum linear tilt | 8 |
| **spline** | continuous linear spline in a, knots at the AD-stratum edges | 5 |
| sig | pl + local difficulty σ(x) | 9 |
| norm | pl, normalized score |r|/σ(x) | 8 |

## Dev results (mean over 5 seeds; worst-AD-stratum coverage / saturated fraction)
| variant | BACE | ESOL | FreeSolv | Lipo |
|---|---|---|---|---|
| split | 0.845 / 0 | 0.709 / 0 | 0.589 / 0 | 0.825 / 0 |
| weighted_ad (ADR-CP) | 0.858 / 0 | 0.698 / 0 | 0.614 / 0 | 0.824 / 0 |
| grp | 0.824 / 0 | 0.637 / 0 | 0.630 / 0 | 0.886 / 0 |
| pl | 0.845 / .003 | 0.690 / .013 | 0.663 / .145 | 0.884 / 0 |
| **spline** | **0.878 / .002** | 0.679 / .008 | 0.674 / .123 | **0.900 / 0** |
| sig | 0.866 / .003 | 0.693 / .012 | 0.663 / .133 | 0.883 / 0 |
| norm | 0.858 / .038 | 0.708 / .082 | 0.763 / .138 | 0.865 / .010 |

## Decision (locked)
Primary ADCC-CP = **spline** (best worst-stratum coverage on 2/4 datasets, second-lowest saturation
among the extrapolating classes, smallest dimension d=5 so the d/(n+1) interpolation slack is smallest).
All other variants are reported as pre-specified ablations on the panel. Primary endpoint on the panel:
worst-AD-stratum coverage (α=0.10), paired against split, Mondrian, ADR-CP and MW-CP with target-level
(n=13) cluster bootstrap CIs; secondary: mean width, saturated fraction, most-novel-decile coverage.
