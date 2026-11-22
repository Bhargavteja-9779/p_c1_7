# JCIM Submission Guide (not for upload)

**Journal:** Journal of Chemical Information and Modeling (ACS), via ACS Paragon Plus
**Manuscript type:** Article
**Title:** Applicability-Domain Conditional Conformal Prediction: Distribution-Free Coverage over Chemical-Space Shifts without Density-Ratio Estimation
**Abstract:** 247 words (in the manuscript; paste the same text into the submission form)
**Keywords:** conformal prediction; conditional coverage; applicability domain; covariate shift; molecular property prediction; QSAR; prediction intervals; distribution-free inference

## What to upload, and under which file designation

| File | Paragon Plus designation |
|---|---|
| 01_Cover_Letter/Cover_Letter.pdf (or .docx) | Cover Letter |
| 02_Manuscript/Manuscript.docx (PDF also provided) | Manuscript File |
| 03_Supporting_Information/Supporting_Information.pdf | Supporting Information for Publication |
| 06_Code_Archive/ADCC-CP_code.zip | Supporting Information for Publication (code and data) |
| 05_Graphical_TOC/TOC_graphic.png or .pdf | Table of Contents (TOC) Graphic |
| 04_Figures/Figure_1, Figure_2 (PDF, vector) | Figure (only if the system asks for separate figures; they are already embedded in the manuscript) |
| 07_Source_Data_Tables/*.csv | Optional: Supporting Information (machine-readable table data) |

## You must fill these in before submitting

1. **Second / corresponding author**: name, affiliation, e-mail, ORCID. Replace `[Second Author — Supervisor]`, `[Affiliation]` and `[email]` in `manuscript/draft_v6_abstract.md`, `manuscript/draft_v6_tail.md` and `manuscript/cover_letter.md`, then rebuild (`python manuscript/assemble_v6.py && python build_package.py`). Or edit the DOCX files directly.
2. **Cover-letter signature block**: `[Corresponding Author Name]`, `[Affiliation]`, `[Email]`, `[ORCID]`.
3. **Date** in the cover letter (currently 22 November 2026).
4. **Suggested reviewers** (entered in the submission form; check conflicts of interest and look up current e-mail addresses yourself). These are active researchers in conformal prediction / uncertainty for QSAR whose work is cited in the manuscript: Ulf Norinder; Isidro Cortés-Ciriano; Fredrik Svensson; Johannes Kirchmair; Raquel Rodríguez-Pérez; Andrea Volkamer.
5. **ACS Journal Publishing Agreement**: completed online after acceptance.

## Declarations already in the manuscript
- Funding: none. Competing interests: none.
- AI-use disclosure (ACS policy): in Acknowledgments.
- Data and Software Availability: public data sources with all 13 ChEMBL target IDs; code provided as the SI archive and available from the corresponding author on request.

## Before you click submit
- Open Manuscript.docx in Word and confirm that equations display (they are native Word equations).
- Confirm that author names and affiliations match on the manuscript, the cover letter and the submission form.
