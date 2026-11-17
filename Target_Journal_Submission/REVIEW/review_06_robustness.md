# Review 6 — Robustness & Generalization Reviewer

**Perspective:** Try to invalidate the central claim.

## Findings

**[MAJOR → addressed] R1. Temporal evidence rests on two targets.** The strongest claim (ADR-CP restores temporal conditional coverage) uses VEGFR2 and COX-2 only. *Resolution:* both targets reported individually (both show the effect: 0.913 and 0.843 worst-stratum vs split 0.70/0.66), across two model families (RF and GBM), and the controlled PC1 sweep reproduces the shift→coverage law within a single dataset. The claim is bounded to "under realistic temporal shift on these targets" and generalization beyond is listed as a limitation. Suggest future work on more targets.

**[MAJOR → addressed] R2. Is the scaffold 'impossibility' an artifact of tiny datasets?** FreeSolv (n=642) and ESOL (n=1117) are small. *Resolution:* the severe-shift regime is defined by *measured* discriminator AUC (0.93–0.98), not dataset size; the controlled sweep shows the same coverage collapse at high AUC within the large Lipophilicity dataset (AUC→0.95). So the effect is shift-magnitude-driven, not size-driven.

**[MODERATE] R3. Diagnostic holds within- and across-dataset.** Spearman ρ=-0.56 (pooled) and the within-dataset sweep both show it. Good.

**[MINOR] R4.** Report the fingerprint/featurization sensitivity (only ECFP4 used) as a limitation. Done (§7).

## Recommendation: MINOR_REVISION. Claims are appropriately bounded; strengthen the "two targets" caveat (done).
