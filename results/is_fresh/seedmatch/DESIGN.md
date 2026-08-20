# Seed-matched $\delta_{\mathrm{feat}}$ re-measurement — design v2

**v2 supersedes v1 after one adversarial design review** (GPT-5.6 Sol, effort
高, `design_review/DESIGN_REVIEW_ROUNDS.md`, 28,748 chars). v1 is preserved in
`design_review/DESIGN_v1_superseded.md`. §10 records every change the review
forced and every point on which v1 was wrong, because several of them were
wrong in ways that would have produced a confidently misinterpreted result.

Staging: `experiments/results/is_fresh_incoming_gpu3/`. Nothing under
`paper/is2/` is read-write by this experiment; manuscript defects found along
the way are reported, not edited (§9).

---

## 1. The finding this addresses

The manuscript discloses that in the main stochastic CIFAR grid the feature
shift proxy $\delta_{\mathrm{feat}}$ is measured on the **seed-0** source model
and joined to episodes by (dataset, architecture, corruption, severity, image
index), while the episodes are pooled over **three** source-model seeds.
Consequently **66.7%** of rotation episodes (seed-cell count 210/315) and
**58.8%** of masking episodes (150/255) carry a shift term measured through a
different network from the one adapted; every rotation cell and 75 of the 105
masking cells contain at least one such episode.

Reconstructed independently from the record metadata and confirmed exactly:
rotation $26880/40320 = 66.7\%$, masking $19200/32640 = 58.8\%$.

Verified on the compute host: `experiments/ckpt/` retains only
`cifar10_resnet26ttt_s20260806.pt` and three `closure/` nets. **Seeds 0, 1 and
2 are gone for both datasets — including seed 0.**

The argument this addresses: the observed weakness of
$\delta_{\mathrm{feat}}$ — not monotone in severity, median within-cell
Spearman against labelled frozen loss $-0.144$ — is partly *cross-model
measurement noise*, not a property of the proxy.

---

## 2. Estimand, and what it does and does not license

The counterfactual a reader wants is
$T(\text{lost seed-matched }\delta) - T(\text{published seed-0 }\delta)$ on the
lost networks, with the same gains, gradients and episodes. **That is
permanently unidentified. Retraining does not recover it, and this experiment
does not claim to.**

> **Estimand.** Conditional on fresh ResNet-26+GN networks trained under the
> nominal published recipe, and on the published episode definitions, what
> change in each $\delta_{\mathrm{feat}}$-dependent diagnostic is *caused by*
> replacing same-network feature measurement with the published seed-0
> measurement rule?
>
> This does not estimate the unavailable counterfactual seed-matched statistics
> of the lost published networks.

This is a **transport experiment about the measurement protocol**, not a
correction of the published result.

The retrained networks are **fresh realizations of the nominal published recipe
under a different execution stack** (RTX 3080 vs 2080 Ti, torch 2.13.0+cu130 vs
2.8.0+cu128, different cuDNN/AMP nondeterminism). v1 called them "new draws from
the same training distribution"; that is stronger than can be established and
has been withdrawn.

### Licensed and unlicensed conclusions, fixed in advance

| outcome | may say | may **not** say |
|---|---|---|
| arms nearly identical | "In this fresh realization, the published seed-0 measurement rule had little effect relative to seed-matched measurement." | "Therefore cross-model measurement noise did not cause the weakness observed in the published grid." |
| matching materially improves the proxy | "The fresh experiment demonstrates that the disclosed mismatch mechanism *can* materially attenuate these diagnostics under the nominal training recipe." | "The published attenuation was caused by the mismatch" / "was understated by $X$." |
| fresh arm fails to reproduce the printed correlations | "poor transportability" — the paired contrast remains clean *for the fresh networks* | "inconclusive" (v1's wording: the contrast is not made uninterpretable by this) |

**The decisive question is not "does the number move".** A large raw
matched-minus-seed-0 difference is *not* evidence that cross-model noise
explains the proxy's published failure. The evidence that would be is an
improvement in the proxy's **same-network external validity**. §5 makes that
the primary endpoint; v1 had it as a secondary check.

### Two estimands, never substituted for one another

* $\Delta_{\text{protocol}} = T(\text{full fresh grid, matched}) - T(\text{full fresh grid, seed-0 rule})$
  — the reproduction-of-protocol effect. **Includes** seed-0 episodes, whose
  contribution is exactly zero by construction. That zero is *real dilution
  caused by the historical protocol* and belongs in this estimand.
* $\Delta_{\text{exposed}} = T(\text{seed 1/2 episodes only, matched}) - T(\text{same episodes, seed-0})$
  — the mismatch-*mechanism* effect, free of the structural point mass at zero.

This matters most for `ttt_mask`: its CIFAR-100 run is seed-0 only, so **all 30
CIFAR-100 masking cells cannot move at all**. A small full-grid $\Delta\rho$ for
`ttt_mask` would partly just be that dilution, and a hostile reading would say
so. Both numbers are reported, always as a pair.

---

## 3. The grid, read from the records rather than assumed

Read from `experiments/results/e2/*_main_*.json` metadata and
`e2_cifar/adapt_cifar.py`; `seedmatch/make_jobs.py --from-records` asserts the
transcription against the records and exits non-zero on any drift (it passes:
10 runs, episodes 128, steps 20, lr 1e-3).

| item | value |
|---|---|
| architecture, `ttt_rot`/`ttt_mask` | **ResNet-26 + GroupNorm**, *not* WRN-28-10 |
| architecture, `tent`/`pl` | WRN-28-10 + BatchNorm (out of scope, §8) |
| source recipe | SGD 0.1, momentum 0.9 nesterov, wd 5e-4, bs 128, cosine, 200 epochs, AMP, joint CE + rotation CE |
| published stochastic runs | `ttt_rot`: c10 s0,s1,s2 + c100 s0,s1,s2; `ttt_mask`: c10 s0,s1,s2 + c100 s0 |
| severities | c10 1–5; **c100 3,5 only** |
| episodes/cell | 128; cells 75 (c10), 30 (c100) |
| $\delta_{\mathrm{feat}}$ | cosine distance, pooled encoder feature of the corrupted image to the clean-test feature mean **of the same network** |

**Episode indices come from the recorded episode lists, never regenerated from
the RNG formula.** v1 documented the formula `rng(seed*977 + sev)`; reproducing
an RNG call under a different NumPy/software stack is unnecessary risk when the
indices are in the records. The recorded manifest is the source of truth and a
frozen copy of it drives every fresh computation. Population discovery is by
that manifest, not by glob.

### Seed usage

The seed **is the treatment variable** — it names both the network and the
episode set — so seeds 0/1/2 are reused deliberately, against `is_fresh`
common rule 2. Genuinely new randomness (cross-fit partitions, bootstraps) uses
the 20260801+ range. Declared, not silent.

### Data pinning — verified, not asserted

The compute host retained only 4 of the 15 CIFAR-10-C corruption files and no
CIFAR-100-C. Both archives were re-fetched from Zenodo (records 2535967 and
3555552, 2,918,471,680 and 2,918,473,216 bytes). **All five files the original
pipeline actually used are byte-identical to the freshly downloaded copies**
(SHA-256 verified for `contrast`, `fog`, `gaussian_noise`, `jpeg_compression`,
`labels`), so the fresh measurement runs on the same bytes the published grid
ran on.

---

## 4. Protocol

### Stage A — six source networks (running)

`train_source.py --dataset {cifar10,cifar100} --arch resnet26ttt --seed {0,1,2}`,
recipe untouched.

**Training sanity gate — renamed and made non-blocking.** v1 called this a
"comparability gate" and had the analysis refuse to run if any net fell outside
the published across-seed accuracy range $\pm 0.010$. Both were wrong: clean and
rotation accuracy are *extremely weak* evidence that the latent feature geometry
relevant to $\delta_{\mathrm{feat}}$ is comparable — a net can sit comfortably
inside the interval with materially different geometry — and letting an
arbitrary tolerance decide whether informative evidence exists is not defensible.
So the accuracy check is a **training sanity gate** only; a net outside range is
reported and its transport diagnostics (§6) are read as weaker, and nothing is
discarded. Published ranges, for reference: c10 acc 0.9152–0.9216 / rot
0.9061–0.9121; c100 acc 0.6567–0.6671 / rot 0.7696–0.7809.

### Stage C′ — the FULLY CROSSED measurement matrix (the core of the experiment)

For every episode observation $i$ in the frozen manifest, and **every**
measurement network $m \in \{0,1,2\}$ of the same dataset, record

* $d_{i,m}$ — $\delta_{\mathrm{feat}}$ of observation $i$ through network $m$,
  each network using **its own** clean-test feature centroid;
* $L_{i,m}$ — that network's **labelled** frozen cross-entropy on $i$, and
  whether its frozen prediction is correct.

v1 measured only the diagonal plus seed 0. Full crossing costs forward passes
only and buys three things v1 could not have: the derangement arms below; the
separation of "which network" from "which episode set" (seed $s$ determines
*both* the network and the 128 images, so a raw seed-1-vs-seed-2 difference is
not attributable to network geometry unless every episode is seen by every
network); and the calibration decomposition of §5.

**Three arms, not two.** For an episode adapted on source seed $s$:

| arm | measurement network |
|---|---|
| MATCHED | $m = s$ |
| PUBLISHED-STYLE | $m = 0$ for all $s$ |
| GENERIC-WRONG | mean over the two complete derangements $P_1: 0\to1, 1\to2, 2\to0$ and $P_2: 0\to2, 1\to0, 2\to1$ |

MATCHED vs PUBLISHED-STYLE is the measurement-rule contrast. MATCHED vs
GENERIC-WRONG asks whether being on *a* wrong network matters, with measurement-
network identity balanced. PUBLISHED-STYLE vs GENERIC-WRONG asks whether **seed
0 is an atypical wrong network** — which no two-arm design can ask. v1's single
permuted arm would have left "wrongness" entangled with one identity mapping.

CIFAR-100 masking has only source seed 0 and therefore contributes no balanced
source-seed comparison; it is never pooled into a claimed generic-mismatch
result without that qualification.

### Stage B — the adaptation grid: EXPOSED-ONLY (approved 2026-08-19)

v1 declared the 10-run adaptation re-run mandatory. The review is right that it
is not, for the *sharpest* version of the objection: the two most damaging
pieces of evidence against the proxy — its severity behaviour and its
within-cell relation to the source model's labelled frozen loss — **involve no
test-time adaptation at all**. Both are answerable from Stage A + Stage C′.

**Approved scope: exposed-only, 6 runs** — `ttt_rot` c10 s1,s2 + c100 s1,s2,
`ttt_mask` c10 s1,s2. These are exactly the runs whose source seed is not 0,
i.e. the episodes that were actually mismeasured. Seed-0 runs were never
cross-measured, so re-running them buys no mechanism information; they only
supply the structural point mass at zero that dilutes the full-grid effect.

This estimates $\Delta_{\text{exposed}}$ and **not** $\Delta_{\text{protocol}}$,
which needs fresh seed-0 gains. The four seed-0 runs are not launched and
require a fresh decision; `sm_downstream.py` asserts no seed-0 run is present
so the estimand label cannot silently become wrong.

`ttt_mask` has no CIFAR-100 seed 1/2 run in the published grid, so its exposed
analysis spans CIFAR-10's 75 cells while `ttt_rot`'s spans all 105. That
asymmetry is a property of the published grid and is stated, not smoothed over.

**ALTA is left at each run's published setting** rather than switched off. v1
switched it off on the argument that its output is not consumed; that is not
sufficient, because a code path can consume RNG or touch state, and there is no
benefit to manufacturing the argument. It costs nothing here: only the three
seed-0 runs had ALTA on, and **all six exposed runs had it off**, so this lane
reproduces the published settings with *zero* deviation rather than merely
defensibly. `make_jobs.py` carries the flag per run in the frozen transcription,
asserts it against the records, and asserts that no exposed run carries ALTA.

Recon heads are built only for networks actually undergoing `ttt_mask` — under
this scope exactly two (c10 s1, s2), not six.

---

## 5. Analysis

### 5.1 PRIMARY — does correct measurement make the proxy more concordant with the *same network's* labelled risk?

For every actually-mismatched (cell, source-seed) pair $(c,s)$, $s \in \{1,2\}$:

$$\Delta r_{c,s} \;=\; \rho_i\!\left(d_{i,s},\,L_{i,s}\right) \;-\; \rho_i\!\left(d_{i,0},\,L_{i,s}\right)$$

within cell $c$, where $L_{i,s}$ is the labelled frozen loss of the network the
episode actually ran on. Aggregated by **median** (the aggregation the published
audit uses for this quantity), with corruption-clustered uncertainty.

This is the statistic that directly asks the objection's question, and it is
sharp for a reason v1 missed: **within-cell Spearman is already invariant to
any per-network offset and positive rescaling.** An objection that claims the
published $-0.144$ arose from cross-network measurement therefore *cannot*
rescue the claim by pointing at large raw matched-minus-mismatched cosine
distances; they need genuine image-order disagreement between networks. The raw
difference distribution — v1's headline — is demoted to a mechanism diagnostic.

The same contrast is run with GENERIC-WRONG in place of PUBLISHED-STYLE.

### 5.2 Severity endpoint, with the published statistic and a wording defect fixed

The published severity statistic recomputed under MATCHED, PUBLISHED-STYLE and
GENERIC-WRONG. Reported **split by dataset**, because the pooled published
figure conflates two different tests (§9, defect 1).

### 5.3 The per-network offset decomposition

If network $s$'s distances were merely $d_{i,s} = a_s + b_s d_{i,0}$ with
$b_s>0$, the *episode ordering* would be unchanged while the raw differences
could look enormous. Analyses would then tell opposite stories for a trivial
reason. So the difference is decomposed on a **balanced reference panel** —
every network scored on exactly the same image-condition tuples with equal cell
weighting, built per dataset:

* $z_{i,m} = (d_{i,m}-\mu_m)/\sigma_m$ with $\mu_m,\sigma_m$ from the panel — removes offset and scale;
* $q_{i,m} = \hat F_m(d_{i,m})$, network $m$'s empirical CDF on the panel — removes **any** strictly monotone per-network recalibration, not just affine.

$q_{i,s}-q_{i,0}$ is the component that survives a genuinely rank-based
objection. Standardization is at **network × dataset** level and explicitly
*not* within corruption×severity cell, which would delete the between-cell
signal the downstream analysis exists to exploit.

**This also refutes a manuscript claim, and the report says so.** The
manuscript defends $\delta_{\mathrm{feat}}$ as "used as a rank quantity only".
That is mathematically inaccurate for $D$ (§9, defect 2).

### 5.4 SECONDARY — the $D$–gain correlation (only if Stage B runs)

Reported two ways: $\Delta\rho_{\text{raw}}$ on the actual raw $\delta$ (the
operational effect on the published formula, and the headline), and
$\Delta\rho_{\text{rankcal}}$ using $D^{(q)}_{i,m} = w_i q_{i,m}$ as a
*decomposition diagnostic that never replaces the published $D$*. Reading:
large raw / near-zero rank-calibrated ⇒ the effect is network calibration, not
disagreement about which examples are shifted; large both ⇒ substantive
geometry change; both near zero ⇒ mismatch unimportant in this realization.

**Weight-leverage audit, mandatory before declaring any protocol effect.**
$\Delta D_i = \frac{a_i|a_i|}{\sigma^2_{\mathrm{rel},i}}(d_{i,M}-d_{i,U})$: a
merely *positive* $\sigma^2_{\mathrm{rel}}$ can be small enough to amplify a
minor $\delta$ difference into a dominating $\Delta D$. Report the top-1% and
top-5% share of $|\Delta D|$, the maximum weight per cell, and a trimmed /
leave-one-episode-out sensitivity. Diagnostic only; the headline formula is not
altered.

### 5.5 Transport diagnostics — the best available evidence about the lost models

The lost checkpoints do not mean zero information about them. On identical
$(\text{dataset},\text{corruption},\text{severity},\text{idx})$ keys, compare
the **published seed-0 $\delta_{\mathrm{feat}}$ values, which are retained in
`results/e5/`**, against freshly measured seed-0 values: episode Spearman,
cell-mean Spearman, affine calibration, cell-ranking agreement. If new seed-0
does not even preserve old seed-0's ordering, the transport argument for the
whole experiment is weak and the report says so. Same comparison for any other
per-episode quantity retained on matching keys. **This is a central validation
section, not an afterthought, and it costs nothing.**

### 5.6 Inference on the paired difference

The target is $\Delta\rho = \rho_M - \rho_U$ on the *same* cells and the same
$Y$. Independent intervals for $\rho_M$ and $\rho_U$ are not computed and the
arms are never bootstrapped separately. Per replicate $b$: resample the 15
corruption clusters **once**, apply that identical cluster sample *including
multiplicities* to both arms, every split and the gains, recompute both
correlations, and form $\Delta_b = \frac1K\sum_k(\rho_{M,b,k}-\rho_{U,b,k})$.
The interval comes from the distribution of $\Delta_b$; the point estimate uses
the same ordering. Also reported: the **15 leave-one-corruption-out values of
$\Delta\rho$**, because with only 15 clusters a bootstrap interval alone would
conceal a leverage problem.

What this uncertainty is: robustness with respect to **corruption composition**,
conditional on the six realized networks. It is *not* uncertainty over retrained
networks, and no resampling of cells or corruptions licenses a claim about the
distribution of possible trained networks. The single-realization limitation is
substantive and stays in the report.

**Split seeds are Monte Carlo partitions, not replications.** The five published
split seeds share networks, cells, episodes, gains and feature values; only the
partition changes. "Same sign across five" is a sensitivity check, not $n=5$
evidence, and v1's use of it as a materiality criterion is withdrawn. The five
published seeds are retained as a **reproduction endpoint**; stability uses 100
additional preregistered splits, enough that Monte Carlo variation of the
split-averaged statistic is negligible.

### 5.7 Materiality

$0.05$ is kept as a **practical-effect threshold**, not a null boundary: values
below it are reported as "below the preregistered practical-effect threshold",
never as "a measured null", because a difference of 0.03 with a wide interval is
not a null. The code-fixed gate ($\rho\ge0.5$) flip is reported **separately**,
as *decision instability of the manuscript's gate* — 0.499→0.501 flips the gate
while being scientifically negligible, and conflating the two would be
misleading. The "2 of 2 stochastic methods" gate is a code gate, not two
independent confirmations: both arms share architecture, data, source-network
family, proxy, corruption grid and most of the measurement defect.

---

## 6. Verification and records

* Per-episode records retained in full; every job seeded and recorded;
  `run_meta` provenance; no host-absolute paths in staged JSON.
* Frozen episode manifest derived from the published records drives everything.
* Asserted reproduce-from-record checks, run before any headline number:
  1. **Wiring null**: MATCHED and PUBLISHED-STYLE must agree *exactly* on every
     seed-0 episode, and the alignment-only statistic (which contains no
     $\delta_{\mathrm{feat}}$) must be bit-identical across all arms.
  2. Crossed-matrix completeness: every manifest observation has $d_{i,m}$ and
     $L_{i,m}$ for all three $m$; the census is proved against the manifest, not
     against a glob.
  3. Cross-seed census recomputed from the fresh records reproduces the
     disclosed 66.7% / 58.8% and the 105 / 75-of-105 cell counts.
  4. Each network's recorded clean accuracy reproduced by an independent
     evaluation pass to within 0.002 before its feature map is written (already
     implemented in `sm_delta_feat.py`).
  5. `delta_proxy` Spearman $+1.000$ against `frozen_loss` within every
     single-run cell. **Renamed in all new output to `delta_lossproxy`** to end
     the collision the review flagged: it is a *different* quantity from
     `delta_feat`, constructed as `frozen_loss − clean_ref`, so $+1$ is expected
     by construction and is a join check, not a scientific result — as written
     in v1 it looked like a criterion contradicting the audit's $-0.144$.
* `verify_seedmatch.py` re-derives every printed number from the retained
  records and exits non-zero on any mismatch.

---

## 7. Compute — measured, not guessed

Profiling before committing (`seedmatch/profile_epoch.py`): an epoch of
resnet26ttt training on this host spends **69% of its wall clock waiting on the
dataloader**, with the GPU idle in 22 of 25 samples. Serial cost would be ~148
min per network — six networks alone ≈ 14.8 GPU-h, over budget. `num_workers`
was measured at 8 (published default, 44.4 s/epoch) and 16 (75.6 s/epoch,
**worse**), so the published config is also the fastest and no deviation is
needed. Concurrency — pure scheduling, touching no run's recipe — was measured
at 1.48× (2-way) and 1.69× (3-way); at 6-way the GPU runs at 99%.

| stage | measured basis | est. GPU-h |
|---|---|---|
| A: 6 source trainings, 6-way concurrent | 44.4 s/epoch serial, 200 epochs, ≥1.7× | **≈ 7–9** |
| C′: crossed $d_{i,m}$, $L_{i,m}$, 3 nets × 2 datasets | forward passes only | ≈ 0.5 |
| analysis, transport diagnostics (§5.5) | CPU | 0 |
| **Stage 1 total (what is authorized and running)** | | **≈ 8–9.5** |
| B (deferred): exposed-only 6 runs | 46 s/cell serial, 3.25× at 4-way | ≈ +1.5 |
| B (deferred): full 10 runs | 570 cells | ≈ +2.5 |

Stage 1 is under the 12 GPU-h reporting threshold. **Stage 1 + full Stage B
would be ≈ 11–12 GPU-h**, at the threshold — which is why Stage B is a separate,
reported decision rather than part of this launch.

Execution: six detached `setsid nohup` lanes, per-job done-markers (so a
relaunch resumes rather than repeats), 20 s heartbeats, and a remote finalizer
so the chain completes without the launching session.

---

## 8. Declared scope limits

1. **The WRN-28-10 arms are not re-measured** (~14.5 GPU-h to retrain, more than
   the whole budget). v1 claimed that if the ResNet side's sign is unchanged the
   sign-flip conclusion is unaffected. **That claim is withdrawn.** A fresh
   corrected ResNet side against a historical uncorrected WRN side differs
   simultaneously in architecture, normalization, objective family, training
   realization, measurement treatment and execution environment. Permissible
   statements, fixed now:
   * *(sign unchanged)* "In the fresh ResNet-26+GN replication, correcting the
     seed mismatch did not change the sign of the ResNet-side association. The
     historical WRN-28-10+BN estimates remain negative, but the
     cross-architecture sign reversal itself was **not re-tested**, because the
     WRN side was not remeasured."
   * *(sign changed)* "The ResNet-side sign is sensitive to seed matching in the
     fresh replication, so the published cross-architecture sign contrast cannot
     be treated as robust to the disclosed measurement defect."
   The term "architecture sign-flip" is not used in the new report: with
   ResNet≡stochastic and WRN≡deterministic there is no architecture-only
   experiment. It is called the **historical cross-family / cross-architecture
   sign contrast**.
2. Single realization per (dataset, seed); no uncertainty over network draws.
3. **Measurement mismatch is not proxy validity.** Even a perfect matched-vs-
   wrong experiment cannot show $\delta_{\mathrm{feat}}$ is a good shift
   measure: the arms could agree while both correlate badly with risk, or
   matching could move distances a lot and make risk correlation *worse*. The
   report keeps the two questions separate.
4. **Out of scope because $\delta_{\mathrm{feat}}$ does not enter it:** the
   "alignment transfers better than the shift proxy" conclusion is a GPT-2 /
   $\delta_{v2}$ result, not a $\delta_{\mathrm{feat}}$ one. Seed-matching CIFAR
   $\delta_{\mathrm{feat}}$ cannot touch it, and the report says so rather than
   pretending to check it.

---

## 9. Manuscript defects found while designing this (reported, not edited)

1. **The severity-monotonicity figure pools two different tests.** The
   supplement says mean $\delta_{\mathrm{feat}}$ "increases strictly across
   severities 1–5 in only 23 of the 60 (dataset, architecture, corruption)
   triples". Recomputed from `f14_deltafeat_check.json`: the 30 CIFAR-10 triples
   do span severities 1–5 and **7 of 30** are strictly increasing; the 30
   CIFAR-100 triples span **only severities 3 and 5** — a two-point comparison,
   trivially easier — and **16 of 30** are strictly increasing. The pooled
   "23 of 60" is arithmetically right and descriptively wrong: no CIFAR-100
   triple tests monotonicity "across severities 1–5", and the honest five-point
   number is 7/30 (23%), materially worse than the pooled 38% implies.
2. **"Rank quantity only" is mathematically inaccurate for $D$.** A final
   Spearman does not make the pipeline rank-invariant:
   $D_i = w_i d_i$ with $w_i = a_i|a_i|/\sigma^2_{\mathrm{rel},i}$ is averaged
   *within cells* before the 105 cell means are ranked. Under a benign
   recalibration $d_{i,s} = a_s + b_s d_{i,0}$ the episode ranking of $\delta$ is
   unchanged, yet $D_{i,s} = w_i a_s + b_s w_i d_{i,0}$, and because $w_i$ varies
   in sign and magnitude the additive term $a_s w_i$ is **not** a constant cell
   offset and can reorder cell means.
3. **`delta_proxy` vs `delta_feat` naming collision** — see §6.5.
4. `sup:e2-loco`'s LOCO paragraph quotes deviations (0.021, 0.011, ≤0.090) with
   no `% src:` binding them to `f24_e2gn_loco_sensitivity.json`; that citation
   survives only in the archived ledger and the superseded backup.

## 10. What the review changed

Adopted in full: the estimand restatement and the licensed/unlicensed table
(§2); $\Delta_{\text{protocol}}$ / $\Delta_{\text{exposed}}$ (§2); the fully
crossed measurement matrix and the two derangement arms (§4); the primary
endpoint moving from raw $\delta$ differences to same-network labelled-risk
concordance (§5.1); the $z$/$q$ calibration decomposition (§5.3); the weight-
leverage audit (§5.4); the transport diagnostics against retained published
values (§5.5); common-resample paired bootstrap and LOCO (§5.6); split seeds as
partitions not replications (§5.6); materiality wording and gate-instability
separation (§5.7); the accuracy gate demoted and unblocked (§4); recorded
indices over RNG regeneration and manifest over glob (§3); ALTA left as
published (§4); the WRN scope retraction (§8); data hash pinning (§3).

Rejected, with reason: none outright. Deferred: Stage B is not cancelled, it is
made conditional and separately reported (§4).

v1 positions now known to be wrong: that the adaptation re-run was mandatory;
that the raw per-episode difference distribution was the headline; that
accuracy range establishes comparability of feature geometry; that
"consistent sign across five split seeds" is evidence; that a single permuted
arm isolates generic wrongness; that the sign-flip conclusion could be declared
unaffected from one side.
