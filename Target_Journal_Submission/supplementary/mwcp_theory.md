# MW-CP: Method and Group-Conditional Coverage Guarantee

## Setup
Covariates $X\in\mathcal X$, response $Y\in\mathbb R$. Training/calibration data are drawn
from $P_{\text{cal}}$; the deployment pool and test point from $P_{\text{test}}$. We assume
**covariate shift**: $P_{\text{test}}(x,y)=P_{\text{test}}(x)\,P(y\mid x)$ and
$P_{\text{cal}}(x,y)=P_{\text{cal}}(x)\,P(y\mid x)$ (the conditional law $P(y\mid x)$ is shared;
only the input marginal changes).

Let $a:\mathcal X\to\mathbb R$ be the **applicability-domain coordinate** (maximum Tanimoto
similarity of $x$'s fingerprint to the training set). Fix thresholds
$-\infty=t_0<t_1<\dots<t_K=\infty$ and define strata $G_k=\{x: t_{k-1}<a(x)\le t_k\}$,
chosen as quantiles of the calibration $a$-values so each cell has adequate calibration mass.

Let $\hat f$ be any regressor fit on the training set (independent of the calibration set),
and $S(x,y)=|y-\hat f(x)|$ the nonconformity score. For $x\in G_k$ define the **within-stratum
covariate-shift ratio**
$$w_k(x)=\frac{\mathrm dP_{\text{test}}(x\mid X\in G_k)}{\mathrm dP_{\text{cal}}(x\mid X\in G_k)},\qquad x\in G_k.$$

## MW-CP construction
For a test point $X^\star\in G_k$, let $\mathcal C_k=\{i\in\text{cal}: X_i\in G_k\}$ and form
the weighted conformal threshold
$$Q_k(X^\star)=\inf\Big\{t:\ \sum_{i\in\mathcal C_k} p_i^{w_k}(X^\star)\,\mathbf 1\{S_i\le t\}\ \ge\ 1-\alpha\Big\},\quad
p_i^{w_k}(X^\star)=\frac{w_k(X_i)}{\sum_{j\in\mathcal C_k}w_k(X_j)+w_k(X^\star)},$$
and output $C(X^\star)=[\hat f(X^\star)-Q_k(X^\star),\ \hat f(X^\star)+Q_k(X^\star)]$
(with the usual $+\infty$ atom of mass $p^{w_k}_\infty(X^\star)=w_k(X^\star)/(\sum_j w_k(X_j)+w_k(X^\star))$
making $Q_k=+\infty$ when the calibration mass cannot reach $1-\alpha$).

In practice $w_k$ is estimated from the **unlabeled** pool restricted to $G_k$ (a one-dimensional
logistic density ratio along $a$), and $K$ is chosen so $|\mathcal C_k|\ge n_{\min}=\lceil 1/(1-\alpha)\rceil+1$;
sparse cells fall back to the pooled weighted threshold.

## Theorem (finite-sample group-conditional coverage)
Assume (A1) covariate shift with shared $P(y\mid x)$; (A2) for each $k$, conditional on
$X^\star\in G_k$, the calibration points $\{X_i\}_{i\in\mathcal C_k}$ and $X^\star$ are
**weighted-exchangeable** with weight $w_k$ in the sense of Tibshirani et al. (2019); and
(A3) $w_k$ is the true within-stratum ratio. Then for every $k$ with $|\mathcal C_k|\ge1$,
$$\Pr\big(Y^\star\in C(X^\star)\ \big|\ X^\star\in G_k\big)\ \ge\ 1-\alpha$$
in finite samples.

**Proof.** Condition on $X^\star\in G_k$. The construction is exactly weighted split conformal
applied to the sub-population $\{X\in G_k\}$ with weight function $w_k$ and score $S$. By the
weighted-exchangeability coverage guarantee (Tibshirani et al. 2019, Thm. 2 / Lemma 3), the
resulting set satisfies $\Pr(Y^\star\in C(X^\star)\mid X^\star\in G_k)\ge 1-\alpha$. $\qquad\blacksquare$

**Corollary (marginal coverage).** Taking the $P_{\text{test}}(X^\star\in G_k)$-weighted average
over $k$ gives $\Pr(Y^\star\in C(X^\star))\ge1-\alpha$. Hence MW-CP is at least as strong as
marginal weighted conformal, and additionally controls coverage within each AD stratum.

## What the guarantee is — and is not
- It is **group-conditional** (coverage within each AD stratum $G_k$), strictly between marginal
  coverage (ADR-CP/KMM/CoDrug; $K=1$) and pointwise conditional coverage.
- It is **not** pointwise conditional coverage $\Pr(Y^\star\in C(X^\star)\mid X^\star=x)$, which is
  impossible for any non-trivial distribution-free procedure in finite samples (Barber et al. 2021).
- (A3) is an idealization: $w_k$ is **estimated**, so empirically coverage is approximate; we
  report realized per-stratum coverage rather than relying on the theorem alone.
- The guarantee is conditional on the chosen stratification. If the relevant shift is orthogonal
  to $a$, grouping by $a$ cannot help; this is **testable** by the within-stratum train-vs-pool
  discriminator AUC (near $0.5$ indicates within-stratum exchangeability is plausible). We report
  within-stratum AUC as an assumption check.

## Relationship to existing methods
- **Mondrian CP** (Vovk): group-conditional coverage under within-group *exchangeability* (no shift).
  MW-CP extends it to within-group *covariate shift* via $w_k$ — the new element.
- **Weighted CP** (Tibshirani; CoDrug; KMM-CP): marginal coverage with a global weight ($K=1$).
  MW-CP targets the stronger group-conditional object.
- **ADR-CP** (this work, baseline): the $K=1$ special case (global 1-D AD weighting; marginal only).
- **ADE-CP** (this work, baseline): a conformalized-quantile-regression alternative that
  extrapolates the quantile along $a$ (two-fold calibration split for validity); heuristic out of
  domain, no group-conditional guarantee.
