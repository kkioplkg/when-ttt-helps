# Theory-closure experiments — final results

**Status: COMPLETE.** All lanes finished; every headline below has been
reproduced by the independent verifier (`code/verify_closure.py`), which
reports `all_routes_clean = True`. Raw per-episode records (71 files, 128 MB)
and all analysis JSONs are in `records/` and `json/`, hash-verified against
`closure_manifest.sha256` (150/150 files, 0 mismatches).

Design: `DESIGN.md` (v3), which records the two adversarial design audits it
was revised against and what each forced. Code: `code/`.

**Scale.** 89 700 P1 records / 358 800 (episode, declared-law) rows; 9 100 P2
trajectories; 675 `q`-sweeps; 2 880 boundary probes; 58 500 batch-scope rows;
3 120 shell-search episodes. Total compute ≈ **12.3 GPU-hours** on one RTX 3080,
lanes strictly sequential.

---

## 1. Models

Nine binary source models (3 CIFAR-10 pairs × 3 seeds), difficulty spread as
designed, plus a WRN-28-10 BatchNorm(eval) architecture arm:

| pair | classes | clean test accuracy |
|---|---|---|
| `auto_frog` | automobile vs frog | 0.991 / 0.987 / 0.986 |
| `plane_ship` | airplane vs ship | 0.953 / 0.951 / 0.952 |
| `cat_dog` | cat vs dog | 0.865 / 0.869 / 0.875 |

Three 10-class `ResNet26TTT` source models for P2, all of which **pass the
project's operative source-model criterion** — see §12.

---

## 2. T1.1 — the binary sign law

**0 violations in 358 709 testable rows.** 91 rows fell outside the theorem's
hypotheses (`q = p` or a vanishing gradient) and are counted, reported and
excluded — never silently dropped. Every one of the ten model × architecture
cells is at zero:

| model | violations / rows |
|---|---|
| `auto_frog` × 3 seeds | 0 / 39 000 each |
| `plane_ship` × 3 seeds | 0 / 39 000 each |
| `cat_dog` × 3 seeds | 0 / 41 600, 0 / 39 000, 0 / 39 000 |
| `cat_dog` WRN-28-10 BN(eval) | 0 / 5 109 |

At float64 — the precision at which the theorem's *magnitude* claims are
meaningful — the identity holds to machine epsilon:

| | `min |α_ent|` | `resid_H` p50 / max | `resid_R` p50 / max | unresolvable |
|---|---|---|---|---|
| float64, T=1 | **0.999999999999999 4** | 7.3e-15 / 1.9e-10 | 4.4e-16 / 9.6e-11 | **0** |
| float64, T=2 | 0.999999999999999 4 | 6.1e-16 / 2.5e-12 | 4.2e-16 / 4.8e-13 | **0** |
| float64, T=4 | 0.999999999999999 3 | 4.2e-16 / 3.4e-13 | 4.2e-16 / 1.5e-12 | **0** |
| float32, T=1 | 0.999827 | 7.4e-06 / 1.0e-02 | 2.6e-07 / 4.4e-04 | 1 368 / 8 430 |

The theorem's two **vector** factorizations hold, not merely its sign.

**On the "unresolvable" column.** A relative residual `‖g − c·g_s‖/‖g‖` is a
0/0 quantity when its coefficient underflows: at `p = 1` in float32,
`p(1−p) = 0` exactly, so the ratio is identically 1 whatever the gradient does,
and likewise when `|q − p|` falls to a few machine epsilons (`‖g_R‖` measured at
7e-10 in those rows). Those rows — 0.06 % of the total, all in float32, all
saturated — are reported separately rather than allowed to set a misleading
"max residual = 1.0". The sign identity is unaffected: those same rows carry
`|α| = 1.0000001` and contribute zero violations.

## 3. T1.1's discriminating comparison — the theorem is not "helps iff correct"

Under a declared law with `ε > 0`, Theorem 5.2 and modal-label correctness
disagree on the overconfident instances. They disagree **often**, and the
theorem wins **every single time**:

| condition | disagreements | theorem correct on |
|---|---|---|
| T=1, ε=0.1 | 25 252 / 31 200 (80.9 %) | **25 252 / 25 252 (100 %)** |
| T=1, ε=0.25 | 26 603 / 31 200 | **100 %** |
| T=1, ε=0.4 | 27 289 / 31 200 | **100 %** |
| T=2, ε=0.1 … 0.4 | 20 449 → 25 412 / 29 250 | **100 %** |
| T=4, ε=0.1 … 0.4 | 10 625 → 24 616 / 29 250 | **100 %** |

This is the evidence that the closed loop tests the theorem rather than a
tautology: on four fifths of instances the naive reading gives the wrong answer
about whether entropy descent helps, and the sign law gives the right one.

## 4. T1.2 — zero-point directional derivative

Central-difference estimate of `d/dη R(θ+ηv)|₀` against the predicted
`−α_ent‖g_R‖`, minimum of the error curve over `h ∈ {1e-3 … 1e-7}`:

| precision | rel. error p50 | p99 | max |
|---|---|---|---|
| float64 | **7.7e-11 – 1.9e-10** | 2.2e-6 | 8.4e-4 |
| float32 | 7.1e-3 | 4.8e-1 | 1.2 |

The float32 floor is ~1e-4–1e-2 and the float64 floor is ~1e-10, which is why
T1.2's primary precision is float64. The whole error curve is retained per
episode; the minimum over the preregistered `h` grid is the measurement, so no
`h` was chosen after seeing the answer.

## 5. T1.4 — the `q`-sweep: a calibration law, not a correctness law

**COMPLETE, 675 sweeps**, float64, ~117–122 grid points each.

| quantity | result |
|---|---|
| sweeps with **exactly one** alignment sign flip | **675 / 675** |
| sweeps with **modal prediction constant** throughout | **675 / 675** |
| `max |q_flip − p|` | **0.0** |

Holding the network, the instance and `p` fixed and moving only the declared
target conditional `q`, the alignment flips sign **exactly at `q = p`** while
`argmax p` never changes anywhere on the sweep. This is the sharpest single
statement the suite produces.

## 6. T1.5 — the near-boundary limit is arithmetic, not the theorem's

**2 880 probes**, constructed `q = p ± δ` down to `δ = 1e-12`, four temperatures
spanning `|s|` over three decades.

| precision | median smallest δ resolved | n per temperature | unresolved | vs machine ε |
|---|---|---|---|---|
| float32 | **1e-7** | 360 | **0** | **0.84 × ε** |
| float64 | **1e-12** (grid floor; true boundary below it) | 360 | **0** | — |

Identical at `T = 1, 10, 100, 1000`. The sign law resolves down to machine
epsilon in the working precision, and the failure boundary moves ≥ 5 decades
with precision while not moving at all with `|s|` — the signature of an
arithmetic limit. This is a testable attribution, not "float64 fixed it".

## 7. T2.1 — where the theorem stops (`N > 1`)

`|cos(g_H^B, g_R^B)|`; **no agreement rate is computed**, because Theorem 5.2
defines no batch right-hand side.

| N | mean | p50 | min | sign-homogeneous | sign-mixed |
|---|---|---|---|---|---|
| 1 | **1.000000** | 1.000000 | **1.000000** | 1.000000 (11 700/11 700) | — |
| 2 | 0.893 | 0.966 | 0.000232 | 0.916 | 0.692 |
| 4 | 0.782 | 0.876 | 0.000007 | 0.831 | 0.577 |
| 8 | 0.674 | 0.742 | 0.000159 | 0.745 | 0.512 |
| 16 | 0.593 | 0.630 | 0.000021 | 0.664 | 0.505 |

Collinearity is exact at `N = 1` — to all six printed digits, on every one of
11 700 batches — and is lost immediately at `N ≥ 2`, consistently faster when
the batch mixes the theorem's per-member signs. That is the mechanism: both
batch gradients are different weightings of the same `∇s_i`, and disagreeing
signs pull them apart.

## 8. T2.2 / T2.5 — A2 is falsified on real trajectories, and how much depends on the objective

Falsification criterion (stated on the inner product, with explicit
non-degeneracy): `‖ḡ_t‖ > 0`, `‖∇R_t‖ > 0`, `⟨ḡ_t, ∇R_t⟩ ≤ 0`. `Θ_loc` is the
ball containing the realized path, so A4 holds by construction and the
falsification is unconditional on that ball.

| objective (plain SGD) | episodes | A2 falsified **on-path** | `α_path_min` p50 | p5 | min |
|---|---|---|---|---|---|
| entropy (`tent`) | 3 900 | **909 (23.3 %)** | 0.9991 | −0.9855 | −1.0000 |
| rotation (`ttt_rot`) | 3 900 | **1 911 (49.0 %)** | **0.0048** | −0.2679 | −0.6078 |

T2.5's shell search (preregistered radii `{1e-4, 1e-3, 1e-2} × ‖θ_t‖`, 8 random
directions, 3 120 episodes) adds the asymmetric cases the trajectory misses:

| objective | on-path falsified | **asymmetric** (path positive, shell negative) | on-path `α` p50 |
|---|---|---|---|
| entropy | 349 / 1 560 (22.4 %) | **23 / 1 560 (1.5 %)** | 0.9993 |
| rotation | 695 / 1 560 (44.6 %) | **220 / 1 560 (14.1 %)** | 0.065 |

For rotation the count of shell points containing a falsifying direction grows
monotonically with radius (e.g. 519 → 524 → 600 of 1 560 across the three
radii); for entropy it is essentially flat (375 → 376 → 383).

**The finding, stated as measured.** A2's persistence clause is
**objective-dependent**. For entropy, alignment is strong (`α ≈ 0.999`) and
locally robust — only 1.5 % of episodes are asymmetric. For rotation, alignment
is near-zero along the whole path (`α_path_min` median 0.005), already violated
on-path in 49 % of episodes, and a further 14.1 % of episodes look fine on the
path but are falsified by a perturbation of relative size 1e-4–1e-2: **persistent
alignment is not locally robust for the rotation objective.** Shell minima are
minima over a finite direction sample, so they upper-bound the region infimum:
a negative value falsifies, a positive sample proves nothing.

**Step-cap consequence.** `η̂` — the trajectory-derived *optimistic upper bound*
on the maximal admissible cap (only `η_practical > η̂` is informative):

| objective | `η̂` p50 | episodes with `η̂` < practical lr (1e-3) |
|---|---|---|
| entropy | 4.2e-3 | 1 635 / 3 900 (41.9 %) |
| rotation | **2.5e-7** | **3 170 / 3 900 (81.3 %)** |

For rotation, even the optimistic bound is ~4 000× below the step size that is
actually used, on four fifths of episodes. Where `α_path_min ≤ 0` the formula's
premise is void and `η̂` is not a step size at all.

## 9. T2.3 / T2.4 — Jacobian conditioning and the Proposition 5.5 certificate

| quantity (t=0, plain SGD) | entropy p50 | rotation p50 | p95 |
|---|---|---|---|
| `κ_J` (literal) | **4.42** | **5.77** | 9.3 / 13.2 |
| `L_J` | 51.7 | 80.3 | 105 / 177 |
| `μ_J` literal | 9.90 | 11.8 | — |
| `μ_J` restricted | 20.65 | 29.24 | — |
| **`μ_restricted / μ_literal`** | **1.93** | **2.29** | **3.8 / 5.0** |
| `cond(J Jᵀ)` | 1.1e10 | 2.0e10 | 3.5e10 / 8.2e10 |
| `κ_crit` | **1.000** | **1.000** | 1.011 / 1.012 |
| `LB` | −18.6 | −32.3 | −5.1 / −8.7 |

**Both readings are measured, and neither is used throughout.** The table above
reports the **literal** (unprojected) reading `J Jᵀ ⪰ μ_J² Π`, which is the one
`DESIGN.md` froze for this suite and the conservative of the two: read
restrictedly, `κ_J` is smaller by a median factor of ~2 and up to 5. The
**manuscript states Assumption 5.4 on the restricted (compressed) form**
`Π J Jᵀ Π ⪰ μ_J² Π` — the form its own pullback step consumes — and cites the
matching restricted constant, median **2.15** (entropy) and **2.36**
(rotation). So the split is deliberate and is recorded rather than resolved:
`json/KAPPA_RESTRICTED.json` carries `kappa_literal` and `kappa_restricted`
side by side for every episode, this document reports the literal reading, the
manuscript cites the restricted one, and the gap between them stays visible in
both. Neither the direction nor the size of that gap is a theorem: as a
hypothesis the unprojected form is strictly stronger, so the `κ_J` it admits is
*no smaller* — the two optima may in principle coincide, and here they do not.

**The certificate funnel — `eligible → Z ≥ 0 → LB > 0`:**

| step | entropy | rotation |
|---|---|---|
| eligible (Def. 5.3 hypotheses) | **3 900 / 3 900 (100 %)** | 3 900 / 3 900 |
| `Z ≥ 0` (logit-space bracket) | ~2 950–2 991 (~76 %) | ~2 956–2 997 (~76 %) |
| **`LB > 0` (certifies `α_ent > 0`)** | **0 / 3 900** | **0 / 3 900** |
| `LB ≤ −1` (fully vacuous) | **3 900 / 3 900 (100 %)** | **3 900 / 3 900** |

Identical at every measured step `t ∈ {0,1,5,10,20}`.

**The finding.** Proposition 5.5 is *mathematically valid but numerically
inactive* on these networks, and the funnel says exactly where it dies: the
logit-space calibration bracket `Z` is favourable on three quarters of
instances, so the calibration half carries signal; the certificate is destroyed
by the Jacobian pullback. Quantitatively, `κ_crit` — the largest `κ_J` at which
the bound would still fire — has median **1.000**, i.e. the certificate requires
an essentially **isometric** pullback, against a measured `κ_J` of 4–6 under the
literal reading and 2.15 / 2.36 under the restricted one. Neither reading
reaches it: pooled over both objectives and all five measured steps, the
smallest **restricted** `κ_J` is 1.079 against a largest `κ_crit` of 1.035, so
the two ranges are disjoint under the reading most favourable to the bound. The
soundness check is vacuously satisfied: the bound never fires, so it is never
wrong.

## 10. T3.2 — momentum practice-trajectory stress test (beyond the envelope)

Reported because the manuscript's protocol uses momentum 0.9; **excluded from
every envelope statement**, since S2's recursion has no momentum state.

| objective | A2 falsified, plain SGD | with momentum 0.9 | `α_path_min` p50 plain → momentum |
|---|---|---|---|
| entropy | 23.3 % | 24.0 % | 0.9991 → 0.9986 |
| rotation | 49.0 % | **64.0 %** | 0.0048 → **−0.0545** |

Momentum leaves entropy essentially unchanged and makes rotation markedly
worse: the median rotation trajectory's minimum alignment goes negative.

## 11. Verification

`all_routes_clean = True`.

| route | check | result |
|---|---|---|
| 1 | RHS by the theorem's printed form `sign((p−½)(q−p))` vs the stable `sign(s(q−p))` | **0 mismatches** in 358 709 rows |
| 2 | reproduce-from-record: reload model, redo episode from scratch | **200 / 200**, worst `|Δα|` = 2.2e-7, `Δp = Δs = 0` |
| 3 | violation count by sorting/scanning instead of accumulators | **0 violations / 358 709**, 91 excluded |
| 4 | `μ_J` by bisection instead of Schur complement, on **120 real Gram matrices** (cond p50 8.2e9) | max rel. err **4.4e-2** in `μ²` = **2.2 %** in `κ_J`, within the 10 % threshold |
| — | `q`-sweep flips re-located by an independent scan | 675/675 one flip, `max|q_flip−p| = 0.0` |

**Two verification caveats, stated rather than buried.**

1. *Route 1 logit-vs-`s`*: 9 900 rows have `|logit(p) − s| > 1e-4` relative —
   all float32, all saturated (`p > 0.9999`), where recomputing log-odds from a
   rounded probability loses the fourth digit. The **sign** is never affected
   (0 RHS mismatches), which is exactly why the design evaluates the RHS as
   `sign(s(q−p))` and never recomputes `logit(p)`. This is quantified evidence
   for that design choice, not a defect.
2. *Route 4 is not exact and is not claimed to be.* Bisection is itself
   ill-conditioned near the critical `λ` at `cond(A) ~ 1e10`. A synthetic sweep
   characterizes the cross-check tool's own limits — agreement 2.0e-10 at
   `cond~1e2`, 1.1e-5 at `cond~1e6`, breaking down at synthetic `cond~1e10` —
   so the **gating** comparison is run on the real measured matrices, where it
   is 4.4e-2. The residual 2.2 % uncertainty in `κ_J` is ~40× below the margin
   that matters: the certificate needs `κ_J ≈ 1` against a measured 4–6, so no
   conclusion can flip. An initial implementation of this harness used an
   absolute bisection tolerance and reported a 4 607× disagreement *next to a green
   `all_routes_clean`*, because route 4's numerical agreement was not in the
   gate. It now is.

## 12. Scope caveats

* **The P2 source models pass the project's operative criterion. An initial
  draft of this file recorded a scope caveat here; it was wrong and is
  withdrawn.** The `gate_pass=False` flag in the training JSONs is asserted
  against the training script's `≥0.93` constant, which the manuscript's own
  appendix calls **"the training script's aspirational threshold"** and which
  **no published model has ever met**: the released seed-0/1/2
  ResNet-26+GroupNorm records are `0.9203 / 0.9152 / 0.9216`, every one of them
  `gate_pass: false` (`experiments/results/m0/`). The project formally restated
  the requirement as *comparability with the published E2 source models* —
  **rotation accuracy ≥ 0.85 and clean test accuracy ≥ 0.905**, one point below
  the weakest published model (`paper/is/paper/appendix/experimental_details.tex`,
  "Architecture-matched entropy run"; precedent record
  `experiments/results/is_fresh/e2_gn/f15_source_gate.json`).

  Against that criterion all three P2 source models **pass**, and their clean
  accuracies fall **inside** the published range:

  | seed | clean acc | rotation acc | ≥0.905 & ≥0.85 | aspirational ≥0.93 |
  |---|---|---|---|---|
  | 20260921 | 0.9163 | 0.8985 | **pass** | false |
  | 20260922 | 0.9202 | 0.8964 | **pass** | false |
  | 20260923 | 0.9160 | 0.9055 | **pass** | false |
  | *published s0/s1/s2* | *0.9203 / 0.9152 / 0.9216* | *0.9121 / 0.9061 / 0.9064* | *pass* | *false* |

  The audit record is `json/P2_SOURCE_GATE.json`, in the same schema as the
  precedent `f15_source_gate.json`.

  **Retraining was considered and rejected on evidence, not on cost.** The
  decisive test: the manuscript-era 200-epoch checkpoint
  (`cifar10_resnet26ttt_s20260806`, trained with the unchanged original recipe)
  was re-evaluated through this suite's pipeline and scores **0.9165** clean /
  0.9046 rotation — reproducing the value recorded for it at the time (0.9165)
  exactly, and statistically indistinguishable from the 100-epoch models here.
  Doubling the training budget therefore does not move this architecture toward
  0.93; the ≥0.93 constant is unsatisfiable for ResNet-26+GroupNorm with joint
  rotation training, which is why it was restated in the first place. A retrain
  would have cost ≈8.6 GPU-h and produced models indistinguishable from these.
* **P1 Tier-1 is a controlled theorem instantiation** on a real network under an
  exactly specified target distribution. It is not, and must not be written as,
  a demonstration that natural CIFAR's unobservable pointwise `q` has any
  property.
* **Tier 2 falsifies; it does not verify.** A trajectory, and a finite direction
  sample around it, can only exhibit counterexamples. Path extrema bound A2's
  region constants and are never estimates of them.
* **T3.1/T3.2 are beyond-theorem.** The finite-step arm is a *finite
  displacement along the entropy-gradient direction* with a norm-normalized
  step; it says nothing about Tent at `lr = 1e-3`.

## 13. Suggested claim language

> On a trained binary network the entropy-alignment identity holds exactly:
> zero sign violations in 358 709 measurements across ten models, with the
> alignment magnitude equal to 1 to machine precision and both vector
> factorizations reproduced to 1e-15. The sign is governed by the calibration
> gap `q − p`, not by predictive correctness — sweeping `q` alone, with the
> prediction held fixed, flips the alignment exactly at `q = p` in 675 of 675
> sweeps while the predicted class never changes, and on 81 % of instances under
> a non-degenerate target law the correctness reading gives the wrong answer
> where the identity gives the right one. The identity is exactly a
> single-instance statement: collinearity is exact at `N = 1` and is lost
> immediately at `N ≥ 2`.
>
> The assumptions the nonlinear extension needs do not transfer. Along real
> single-instance trajectories, persistent alignment (A2) is falsified on 23 %
> of entropy episodes and 49 % of rotation episodes, and a preregistered
> neighbourhood search falsifies a further 14 % of rotation episodes whose own
> path looks favourable — persistent alignment is not locally robust for that
> objective. The logit Jacobian is ill-conditioned (`κ_J` median 4.4–5.8,
> `cond(J Jᵀ) ~ 1e10`), and the multiclass certificate of Proposition 5.5,
> though its calibration bracket is favourable on 76 % of instances, fires on
> **none** of 3 900 instances at any step: it requires an essentially isometric
> pullback (`κ_crit` median 1.000). The sufficient bound is mathematically valid
> but numerically inactive on the networks we run, and the obstruction is
> Jacobian anisotropy rather than logit-space miscalibration.
