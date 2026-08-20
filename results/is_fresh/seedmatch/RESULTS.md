# Seed-matched $\delta_{\mathrm{feat}}$ re-measurement — results

> **Status: SCOPE PRE-COMMITTED, NUMBERS PENDING.**
> Sections 1–3 were written **before any result existed**, on purpose: they fix
> what this experiment may and may not license, so those statements cannot be
> shaded after the fact by whatever the numbers turn out to be. Sections 4+
> fill in when the chain lands. Design: `DESIGN.md`. Review:
> `design_review/DESIGN_REVIEW_ROUNDS.md`.

---

## 1. What this experiment is, and what it is not

The published grid measured the feature shift proxy $\delta_{\mathrm{feat}}$ on
the **seed-0** source network and joined it to episodes by (dataset,
architecture, corruption, severity, image index), while pooling episodes over
three source-model seeds — so **66.7%** of rotation and **58.8%** of masking
episodes carried a shift term measured through a different network from the one
adapted. All three source checkpoints (seed 0 included) are gone.

**This is a transport experiment about the measurement protocol. It is not a
correction of the published result.** The counterfactual a reader wants —
seed-matched $\delta_{\mathrm{feat}}$ on the *lost* networks, with the same
gains and gradients — is permanently unidentified, and retraining does not
recover it.

> **Estimand.** Conditional on fresh ResNet-26+GN networks trained under the
> nominal published recipe, and on the published episode definitions, what
> change in each $\delta_{\mathrm{feat}}$-dependent diagnostic is *caused by*
> replacing same-network feature measurement with the published seed-0
> measurement rule?
>
> This does not estimate the unavailable counterfactual seed-matched statistics
> of the lost published networks.

The retrained networks are **fresh realizations of the nominal recipe under a
different execution stack** (RTX 3080 vs 2080 Ti, torch 2.13.0+cu130 vs
2.8.0+cu128), not "new draws from the same training distribution".

## 2. THE CROSS-ARCHITECTURE SIGN CONTRAST IS NOT RE-TESTED BY THIS EXPERIMENT

Stated here, prominently and in advance, because the manuscript text must be
scoped to it.

The published audit reports that $\delta_{\mathrm{feat}}$'s cell-level relation
to labelled risk **reverses sign with the architecture**: $+0.78$ (`ttt_mask`)
and $+0.76$ (`ttt_rot`) on ResNet-26+GroupNorm against $-0.54$ (`tent`) and
$-0.92$ (`pl`) on WRN-28-10+BatchNorm.

**Only the ResNet-26 side is re-measured here.** Retraining six WRN-28-10
networks is ~14.5 GPU-h on its own, more than this experiment's entire budget.
A fresh corrected ResNet side set against a historical uncorrected WRN side
differs simultaneously in architecture, normalization, objective family,
training realization, measurement treatment and execution environment.

Permissible statements, fixed before the numbers:

* *(if the ResNet-side sign is unchanged)* — "In the fresh ResNet-26+GN
  replication, correcting the seed mismatch did not change the sign of the
  ResNet-side association. The historical WRN-28-10+BN estimates remain
  negative, but the cross-architecture sign reversal itself was **not
  re-tested**, because the WRN side was not remeasured."
* *(if the ResNet-side sign changes)* — "The ResNet-side sign is sensitive to
  seed matching in the fresh replication, so the published cross-architecture
  sign contrast cannot be treated as robust to the disclosed measurement
  defect."

**Not permissible:** "the sign-flip conclusion is unaffected by seed matching."
Design v1 claimed that; it is withdrawn.

The phrase **"architecture sign-flip" is not used** in this report. In the
published grid ResNet ≡ the stochastic methods and WRN ≡ the deterministic
ones, so there is no architecture-only experiment. It is called the
**historical cross-family / cross-architecture sign contrast**.

## 3. Other fixed scope limits

1. **Stage B is exposed-only.** Six runs (source seeds 1 and 2). This yields
   $\Delta_{\text{exposed}}$, the mismatch-*mechanism* effect. It does **not**
   yield $\Delta_{\text{protocol}}$, the full-grid reproduction-of-protocol
   effect, which needs fresh seed-0 gains that were not run. `ttt_mask`'s
   exposed analysis spans CIFAR-10's 75 cells only (the published grid has no
   CIFAR-100 masking run at seeds 1/2); `ttt_rot`'s spans all 105.
2. **Measurement mismatch is not proxy validity.** Even a perfect
   matched-vs-wrong result cannot show $\delta_{\mathrm{feat}}$ is a good shift
   measure: the arms could agree while both correlate badly with risk, or
   matching could move distances a lot and make risk concordance *worse*.
3. **Single realization** per (dataset, seed). The corruption-clustered
   bootstrap is robustness with respect to **corruption composition**,
   conditional on the six realized networks — never uncertainty over network
   draws.
4. **Out of scope entirely:** the "alignment transfers better than the shift
   proxy" conclusion is a GPT-2 / $\delta_{v2}$ result and contains no
   $\delta_{\mathrm{feat}}$. Seed-matching CIFAR $\delta_{\mathrm{feat}}$ cannot
   touch it and this report does not pretend to check it.
5. A difference below the pre-declared practical-effect threshold (paired
   $\Delta\rho$ of 0.05) is reported as **"below the preregistered
   practical-effect threshold"**, never as "a measured null". Any flip of the
   code-fixed $\rho\ge0.5$ gate is reported **separately**, as decision
   instability of the manuscript's gate, not as a substantive effect.

---

## 4. Findings that do not depend on the fresh networks

These are already established and will not change.

### 4.1 The disclosed census reproduces exactly

Rebuilt independently from the published episode records
(`episode_manifest.json`): rotation $26880/40320 = 66.7\%$ cross-seed, masking
$19200/32640 = 58.8\%$; 105/105 rotation cells and 75/105 masking cells contain
at least one cross-seed episode. Matches the manuscript.

### 4.2 The severity-monotonicity figure pools two different tests

The supplement reports mean $\delta_{\mathrm{feat}}$ "increases strictly across
severities 1–5 in only 23 of the 60 (dataset, architecture, corruption)
triples". Recomputed exactly from `f14_deltafeat_check.json`
(`sm_equivalence.py`, agreement to $10^{-9}$):

| triples | severities actually covered | strictly increasing |
|---|---|---|
| CIFAR-10 (30) | 1, 2, 3, 4, 5 — a genuine five-point test | **7 / 30 (23%)** |
| CIFAR-100 (30) | **3 and 5 only** — a two-point test | **16 / 30 (53%)** |
| pooled (60) | mixed | 23 / 60 (38%) |

No CIFAR-100 triple tests monotonicity "across severities 1–5". The pooled
figure is arithmetically correct and descriptively wrong, and the honest
five-point number, 7/30, is **worse** for the proxy than the pooled 38%
implies.

### 4.3 "Rank quantity only" is inaccurate for $D$

$D_i = w_i d_i$ with $w_i = a_i|a_i|/\sigma^2_{\mathrm{rel},i}$ is averaged
*within cells* before the cell means are ranked. Under a benign per-network
recalibration $d_{i,s} = a_s + b_s d_{i,0}$ the episode ordering of $\delta$ is
unchanged, yet $D_{i,s} = w_i a_s + b_s w_i d_{i,0}$; because $w_i$ varies in
sign and magnitude, the additive term $a_s w_i$ is **not** a constant cell
offset and can reorder cell means. A final Spearman does not make the pipeline
rank-invariant.

### 4.4 Data provenance is byte-exact

All five CIFAR-10-C files the original pipeline used are SHA-256 identical to
freshly downloaded Zenodo copies, so the fresh measurement runs on the same
bytes as the published grid.

---

## 5. Headline

**Seed-matched measurement does not rescue $\delta_{\mathrm{feat}}$, and does
not materially change any conclusion it feeds.** Every contrast is below the
preregistered practical-effect threshold of 0.05. On the primary endpoint the
sign is, if anything, *against* the rescue hypothesis: matched measurement is
marginally **less** concordant with labelled risk than the published seed-0
rule, not more.

The strongest single result is §9: measuring through a **different seed's**
network disagrees no more than two independent training runs of the **same
seed** do. Cross-seed measurement is therefore not a special defect — it is
ordinary training nondeterminism, and retaining the checkpoints could not have
removed it.

## 6. Primary endpoint — same-network labelled-risk concordance

$\Delta r_{c,s} = \rho_i(d_{i,s}, L_{i,s}) - \rho_i(d_{i,0}, L_{i,s})$ within
each exposed (dataset, cell, source seed) group, $L$ being the labelled frozen
loss of the network the episode actually ran on. Median over groups;
common-resample corruption-clustered bootstrap (1000 replicates, 15 clusters).
**A positive value is what the rescue hypothesis predicts.**

| method | arm | median $\Delta r$ | 95% cluster CI | LOCO sign flips |
|---|---|---|---|---|
| `ttt_rot` (210 pairs) | matched − published | **−0.0143** | [−0.0184, −0.0053] | 0 |
| | matched − generic-wrong | −0.0009 | [−0.0099, +0.0042] | — |
| | published − generic-wrong | +0.0071 | [+0.0001, +0.0135] | — |
| `ttt_mask` (150 pairs) | matched − published | **−0.0057** | [−0.0207, +0.0054] | 0 |
| | matched − generic-wrong | +0.0005 | [−0.0100, +0.0057] | — |
| | published − generic-wrong | +0.0071 | [−0.0009, +0.0160] | — |

Three readings:

1. **Matching does not improve concordance.** Both point estimates are negative;
   `ttt_rot`'s CI excludes zero on the negative side. Correcting the measurement
   network makes $\delta_{\mathrm{feat}}$ *slightly worse* at ranking which
   images its own network does badly on.
2. **The absolute level is the real story.** Median within-cell
   $\rho(\delta_{\mathrm{feat}}, L)$ is $-0.045$ (matched) against $-0.018$
   (published) for `ttt_rot`, and $-0.045$ against $-0.019$ for `ttt_mask`.
   Both arms are indistinguishable from no relationship. The proxy's published
   weakness is a property of the proxy, not of the measurement rule.
3. **Being on the *correct* network is worth nothing over being on *a* wrong
   one**: matched − generic-wrong is $-0.0009$ and $+0.0005$. Seed 0 is a very
   slightly *better*-than-typical wrong network (+0.0071 both methods), which is
   the opposite of the direction the objection assumes, and negligible anyway.

Rank-calibrated arms are **identical** to raw, exactly as required: within a
fixed (dataset, cell, seed) group $q=F_m(d)$ is a strictly monotone transform of
$d$, so Spearman cannot move. This is asserted (§11), and it is what caught the
bug in §12.

## 7. Severity endpoint

Corruptions whose mean $\delta_{\mathrm{feat}}$ is strictly increasing in
severity, ResNet-26+GN, split by dataset because the two are different tests:

| arm | CIFAR-10 (5-point test) | CIFAR-100 (2-point test) |
|---|---|---|
| matched | 6 / 15 | 14 / 15 |
| published seed-0 | 5 / 15 | 14 / 15 |
| generic-wrong | 7 / 15 | 14 / 15 |

Unchanged across arms to within one corruption. The proxy fails severity
monotonicity on the genuine five-point test under *every* measurement rule, and
the two-point CIFAR-100 test passes at 14/15 under every rule — confirming §4.2
that the two-point test is near-vacuous and should never have been pooled with
the five-point one.

## 8. Per-network offset decomposition (exposed episodes, $n=46{,}080$)

| difference | mean | median | sd | mean abs |
|---|---|---|---|---|
| raw $d_{i,s}-d_{i,0}$ | −0.00078 | −0.00133 | 0.0194 | 0.0146 |
| standardized $z$ | −0.0120 | −0.0355 | 0.463 | 0.350 |
| rank-calibrated $q$ | −0.00187 | −0.00599 | 0.138 | 0.103 |

Episode-level Spearman between the matched and published measurements:
**+0.887**. Mean raw difference (−0.0008) is two orders of magnitude below
$\delta_{\mathrm{feat}}$'s own scale (panel means 0.086–0.088 on CIFAR-10,
0.104–0.115 on CIFAR-100). The per-network panels are close in both location
and spread, so there is little offset/scale component to separate — the raw and
rank-calibrated pictures agree, and neither is large.

## 9. The natural scale of "cross-model measurement noise" — the decisive comparison

Within-cell Spearman between two measurements of the same images, same
statistic, same level:

| dataset | CROSS-SEED (fresh $s$ vs fresh 0) | CROSS-REALIZATION (published 0 vs fresh 0) | difference |
|---|---|---|---|
| CIFAR-10 | +0.861 ($s{=}1$), +0.805 ($s{=}2$) | **+0.857** | −0.024 |
| CIFAR-100 | +0.889 ($s{=}1$), +0.873 ($s{=}2$) | **+0.864** | **+0.018** |

Measuring $\delta_{\mathrm{feat}}$ through a **different seed's** network
disagrees by essentially the same amount as measuring through an **independently
retrained network of the same seed**. On CIFAR-100 the cross-seed measurements
agree *more* than the cross-realization pair does.

The consequence is structural, not statistical: a "seed-matched"
$\delta_{\mathrm{feat}}$ is itself only defined up to training nondeterminism of
the same magnitude as the mismatch it is supposed to repair. **Retaining the
per-seed checkpoints would not have eliminated this term.** The manuscript's
disclosure is honest but names an effect that is not separable from ordinary
run-to-run variation.

## 10. $\Delta_{\text{exposed}}$: the $D$–gain correlation (Stage B)

Cross-fit exactly as `f8_e2_crossfit.py`; five published split seeds
(20260801–05) as the reproduction endpoint, 100 further splits for stability;
paired bootstrap with common corruption resamples. Exposed episodes only.

| method | cells | $\rho$ matched | $\rho$ published | $\Delta\rho$ | 95% paired CI | 100-split |
|---|---|---|---|---|---|---|
| `ttt_rot` mean-final | 105 | +0.5113 | +0.4989 | **+0.0124** | [−0.0107, +0.0345] | +0.0160 |
| `ttt_rot` median-final | 105 | +0.4912 | +0.4892 | +0.0020 | [−0.0066, +0.0172] | +0.0036 |
| `ttt_mask` mean-final | 75 | +0.5378 | +0.5342 | +0.0036 | [−0.0258, +0.0181] | −0.0034 |
| `ttt_mask` median-final | 75 | +0.6648 | +0.6603 | +0.0045 | [−0.0056, +0.0074] | +0.0001 |

Every $\Delta\rho$ is **far below the 0.05 practical-effect threshold** and every
bootstrap CI includes zero. Seed-matching does not change the correlation the
diagnostic is judged on.

**Gate instability, reported separately as preregistered.** `ttt_rot` mean-final
sits at $\rho = 0.4989$ under the published rule and $0.5113$ under matched —
straddling the code-fixed $\rho \ge 0.5$ gate on a difference of $+0.0124$. The
gate flips; the science does not. This is decision instability of a knife-edge
threshold, **not** evidence of a measurement effect, and it must not be reported
as the latter. (Note these are exposed-only, two-seed correlations and are
therefore not directly comparable in level to the published three-seed 0.540 /
0.546.)

**Weight-leverage audit.** $|\Delta D|$ is dominated by a few episodes: the top
1% of episodes carry **24%** and the top 5% carry **53%** of total $|\Delta D|$,
with `ttt_rot`'s maximum $|w|$ of 47.1 against a median of 0.029 — a factor of
~1600, driven by episodes whose $\sigma^2_{\mathrm{rel}}$ is merely small and
positive. Any $D$-level effect here would rest on a handful of episodes. This is
an influence diagnostic; the headline formula was not altered.

## 11. Verification ledger — all green

| check | result |
|---|---|
| Statistics port reproduces published `f14` audit | exact to $10^{-9}$ (5/5 quantities) |
| Manifest reproduces disclosed cross-seed census | 66.7% / 58.8%, 105/105 and 75/105 — exact |
| Wiring null: seed-0 episodes identical across arms | 0 / 26,880 disagree |
| Wiring null: rank-calibration invariance | 0 violations |
| Crossed-matrix completeness vs manifest | 28,440 (c10) and 11,355 (c100) per network, all 6 |
| Checkpoint accuracy reproduction (tol 0.002) | all 6 exact to 4 dp |
| Noise homogeneity ($\sigma^2_{\mathrm{rel}}>0$) | asserted, no violations |
| Expected (cell, seed) pair counts | 210 / 150, asserted |
| CIFAR-C byte-provenance | 5/5 SHA-256 identical to published-run files |

**Training sanity gate** — all six networks inside the published across-seed
range (gate = range ± 0.010):

| net | clean acc | published range | rot acc | published range |
|---|---|---|---|---|
| c10 s0/s1/s2 | 0.9173 / 0.9151 / 0.9208 | 0.9152–0.9216 | 0.9064 / 0.9067 / 0.9115 | 0.9061–0.9121 |
| c100 s0/s1/s2 | 0.6655 / 0.6661 / 0.6612 | 0.6567–0.6671 | 0.7758 / 0.7714 / 0.7779 | 0.7696–0.7809 |

All pass. (c10 s1 clean accuracy is 0.9151 against a published minimum of
0.9152 — 0.0001 below the raw range, inside the declared tolerance. Recorded
rather than rounded away.)

**Transport** (§4 of `sm_transport.json`): fresh seed-0 reproduces published
seed-0 at episode $\rho = +0.897$ (c10) / $+0.895$ (c100), **cell-mean
$\rho = +0.975$ / $+0.962$** — the level the downstream analysis actually
consumes — and within-cell median $+0.857$ / $+0.864$. Frozen-loss agreement
old vs fresh is $\rho \approx +0.75$–$0.80$ across all source seeds. The fresh
family is a sound transport vehicle; conclusions here are not weakened by a
transport failure.

## 12. One bug found and fixed during analysis

The first analysis pass grouped cells by `(corruption|severity, seed)` **without
the dataset**. CIFAR-10 and CIFAR-100 cells sharing a corruption at severities 3
and 5 — the two severities the CIFAR-100 grid runs — were silently merged into
one within-cell correlation, pooling a 10-class and a 100-class problem with
different loss scales and feature geometries, and collapsing `ttt_rot`'s 210
(cell, seed) pairs to 150.

It was caught by the **rank-calibration control**, which diverged from the raw
arm for `ttt_rot` ($-0.0332$ vs $-0.0032$) while matching exactly for the
CIFAR-10-only `ttt_mask` — impossible unless the grouping had pooled different
panels. Fixed; both an invariance assertion and an expected-pair-count assertion
now guard it. The superseded output is retained as
`sm_analysis.SUPERSEDED_dataset_collision.json`. Corrected `ttt_rot` matched −
published moved from $-0.0332$ to $-0.0143$; **no conclusion changes**, since
both are below threshold and of the same sign.

`sm_downstream.py` was never affected — its cell key always carried the dataset.

## 13. What this licenses

* Reportable: in this fresh realization, replacing same-network measurement with
  the published seed-0 rule changes no $\delta_{\mathrm{feat}}$-dependent
  diagnostic by more than the preregistered practical-effect threshold, and the
  cross-seed disagreement it induces is no larger than the disagreement between
  two independent training runs of the same seed.
* **Not** reportable: "therefore cross-model measurement noise did not cause the
  weakness observed in the published grid." One fresh realization cannot license
  that (§1).
* The published cross-architecture sign contrast is **not re-tested** (§2).
* $\Delta_{\text{protocol}}$ is **not** estimated (§3.1). Nothing in these
  results makes it decisive: every exposed contrast is below threshold, so the
  full-grid version — which can only be *more* diluted by the seed-0 point mass
  at zero — cannot exceed it. The remaining four seed-0 runs are not recommended.
