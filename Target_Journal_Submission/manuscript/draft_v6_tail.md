## Associated Content

**Supporting Information.** The Supporting Information is available free of charge and contains: the function-class pre-registration and development-set selection (S-adcc-pre); the exchangeable and known-shift validity controls (S-adcc-validity); pooled panel results for all methods and ablations (S-adcc-panel); target-level paired tests for every endpoint (S-adcc-stats); per-target coverage and width (S-adcc-per-target); results by temporal window and by base model (S-adcc-window, S-adcc-model); the misspecification diagnostic $\delta_{\mathcal F}$ per target (S-adcc-diag); the robustness of the applicability-domain coordinate definition (S-adcc-coord); the full ablation over function classes (S-adcc-ablation); the data-leakage audit (S-adcc-leak); and the preliminary estimated-weight benchmark and the shift-magnitude diagnostic analysis that motivate this work (S-prior) (PDF). The source code and machine-readable results are provided as a ZIP archive (ADCC-CP_code.zip).

## Author Information

**Corresponding Author.** [Second Author — Supervisor], [Affiliation]; [email].

**Author Contributions.** Described using the CRediT taxonomy. **P. N. Bhargav Teja:** Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review & editing, Visualization. **[Second Author]:** Supervision. All authors have read and approved the final version of the manuscript.

**Funding.** This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Notes.** The authors declare no competing financial interest.

## Acknowledgments

**Use of AI tools.** During the preparation of this work the authors used Claude (Anthropic), a generative AI assistant, to help write and debug analysis code and to edit the language of the manuscript. All research ideas, study design, analyses, interpretations and conclusions are the authors' own; the authors reviewed, verified and edited all AI-assisted output, checked every reported number against the code outputs, and take full responsibility for the content of this publication.

## Data and Software Availability

All data are public and all results in this paper are fully reproducible.

**MoleculeNet regression datasets** (development/scaffold experiments), from the DeepChem repository: ESOL (`delaney-processed.csv`), FreeSolv (`SAMPL.csv`), Lipophilicity (`Lipophilicity.csv`), BACE (`bace.csv`), all under `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/`; described in MoleculeNet (`https://moleculenet.org/`).

**ChEMBL bioactivity panel** (temporal experiments), from ChEMBL (`https://www.ebi.ac.uk/chembl/`) via its public REST API, querying pChEMBL-valued activities with document year. The thirteen ChEMBL target identifiers are: EGFR (CHEMBL203), VEGFR2/KDR (CHEMBL279), JAK2 (CHEMBL2971), SRC (CHEMBL267), BACE-1 (CHEMBL4822), hERG (CHEMBL240), μ-opioid receptor (CHEMBL233), androgen receptor (CHEMBL1871), estrogen receptor α (CHEMBL206), glucocorticoid receptor (CHEMBL2034), MAO-B (CHEMBL2039), DPP-4 (CHEMBL284), COX-2 (CHEMBL230).

**Code.** A complete Python implementation of ADCC-CP and all baselines, together with the download, preprocessing, leakage-audit, experiment, statistics and figure-generation scripts that regenerate every table and figure with a single command, is provided with this submission as a code archive (ADCC-CP_code.zip; Python, MIT license; includes unit tests and the machine-readable result files) so that editors and reviewers can reproduce every reported number, consistent with the journal's guidelines on method and data sharing.²⁸ It is also available from the corresponding author upon reasonable request.

## References

[[Formatted from supplementary/literature/verified_references.json in ACS style.]]
