# Theory-closure experiments: designs

**DESIGN v2** — revised after an adversarial audit of v1 by an independent
model (verdict MAJOR-REDESIGN, 5 blockers).  The audit transcripts are
author-side working notes and are not distributed with this archive; the
changes they forced are listed in `§7 Changelog` and are the substance.  No
measurement code was run against the estimands below before this version was
frozen.

---

## 0. The one rule

Every measured quantity must be a quantity that appears in the **statement** of
the theorem or assumption being closed, computed by a route **independent** of
the one the theorem uses.  The failure mode being guarded against is the one the
earlier E2 alignment measurement fell into: measuring something adjacent to the
theory's phase quantity and reporting it as the theory's quantity.

The review's single most important finding, and the foundation of v2:

> **`q` is never read off a dataset label.**  The theorem's `q` is a pointwise
> conditional probability under a target distribution `Q`.  An observed CIFAR
> label is not that object.  Every arm of every experiment therefore **declares
> its target distribution `Q` explicitly**, and `q` is the declared law's own
> conditional — exactly known, never estimated, never sampled.

Stated once, binding everywhere:

> **Protocol invariant Q.** Every occurrence of `R`, `∇R`, `ΔR`, `PCD`, `Δ` and
> `mar` in this suite uses the conditional expected cross-entropy under the
> **declared** `q`.  Sampled labels are never used to construct a theorem
> estimand.

### The declared target distributions

Let `D_test` be the CIFAR-10 test split restricted to a class pair, `c(·)` a
fixed corruption at a fixed severity, and `y_clean(x_0)` the clean class of the
source image.  For `ε ∈ [0, 1/2)` define the target distribution

```
Q_ε :   x  =  c(x_0),   x_0 ~ Uniform(D_test),
        Q_ε(y = 1 | x)  =  1 - ε   if y_clean(x_0) = 1
                        =  ε       otherwise.
```

`Q_0` is a **constructed realizable target distribution** — the deterministic
label law — and `q = 1{y_clean = 1}` holds by that construction, not because
"CIFAR labels are effectively deterministic".  `Q_ε` for `ε > 0` is an equally
legitimate target distribution with non-degenerate `q`.  Theorem 5.2 places no
condition on `Q`, so it applies verbatim to every `Q_ε`.

What this buys and what it does not: the experiment is a **controlled theorem
instantiation on a real network under an exactly specified test distribution**.
It is not, and is never described as, a demonstration that natural CIFAR's
unobservable pointwise `q` has any particular property.  The words
"validation of the theorem on natural data" do not appear.

---

## 1. The statements being closed

### Theorem 5.2 (`thm:entropy`) — binary entropy-alignment identity

`K = 2`; `p := p_1 = (1+e^{-s})^{-1}`; `q := q_1 = Q(y* = 1 | x*)`;
`R(θ; x*) = E_{y* ~ q}[ℓ_CE(z(θ), y*)] = -q log p - (1-q) log(1-p)`;
`L_ent(θ) = H(p(θ))`; `θ` = the adapted parameter subset;
`α_ent = ⟨∇_θ L_ent, ∇_θ R⟩ / (‖∇_θ L_ent‖‖∇_θ R‖)`, `0` if either vanishes.

1. `∇_θ H = -p(1-p) logit(p) ∇_θ s`
2. `∇_θ R = (p - q) ∇_θ s`
3. `⟨∇_θ H, ∇_θ R⟩ = -p(1-p) logit(p)(p-q)‖∇_θ s‖²`
4. `α_ent = sign(-logit(p)(p-q)) = sign((p-1/2)(q-p)) ∈ {-1,+1}`
5. Realizable reading (`q ∈ {0,1}`): `α_ent = +1 ⟺ argmax p = y*`.

Hypotheses: `p ≠ 1/2`, `q ≠ p`, `∇_θ s ≠ 0`.

**The 2-logit head is exactly equivalent to the paper's one-logit gauge**, and
the review re-derived this independently rather than accepting our claim: any
`(z_1, z_2)` decomposes as `(s/2, -s/2) + c(θ)(1,1)` with `s = z_1 - z_2`, and
softmax, `H` and CE are invariant to the common shift, so `H = H(s)`,
`R = R(s)` and both θ-gradients are multiples of `∇_θ s`.  Under temperature
`T` the theorem's scalar is `s_T := (z_1 - z_2)/T`, and **`g_s` must be
`∇_θ s_T`, not `∇_θ (z_1 - z_2)`** — one symbol, one meaning, at every `T`.

**Numerical form of the RHS.** `logit(p) = s` identically, so the sign law is
evaluated as `sign(s·(q-p))`, never by recomputing `logit(p)` from a `p` that
has already saturated.  Recomputing the log-odds from `p` would manufacture the
very numerical catastrophe the boundary analysis is trying to characterize.

### (A2) persistent alignment and relative scale (Supplement §S2, verbatim)

On `Θ_loc`: `⟨ḡ(θ), ∇R(θ)⟩ ≥ α‖ḡ(θ)‖‖∇R(θ)‖` and
`c_g‖∇R(θ)‖ ≤ ‖ḡ(θ)‖ ≤ C_g‖∇R(θ)‖`, for `α ∈ (0,1]`, `0 < c_g ≤ C_g < ∞`.
The recursion S2 assumes is `θ_{t+1} = θ_t - η g(θ_t, ξ_t)` — **plain SGD, no
momentum state**.

### Assumption 5.4 (`ass:jacobian`) — well-conditioned logit Jacobian

`J J^⊤ ⪰ μ_J² Π`, `‖J‖_op ≤ L_J`, `κ_J = L_J/μ_J`, `Π` the orthogonal
projector onto `S = span{∇_z H, p-q} ⊂ R^K`.

**The literal meaning, which v1 got wrong.** `J J^⊤ ⪰ μ_J² Π` is a Loewner
inequality on all of `R^K`:

```
∀ v ∈ R^K :   v^⊤ J J^⊤ v  ≥  μ_J² ‖Π v‖² .
```

This is *not* the same as `u^⊤ J J^⊤ u ≥ μ_J²‖u‖²` for `u ∈ S` only: a general
`v` has components in both `S` and `S^⊥`, and the cross terms of `J J^⊤` can
lower the quadratic form.  Writing `A := J J^⊤` in a basis whose first two
coordinates span `S`,

```
A = [[A_SS, A_SR], [A_RS, A_RR]],
μ_J²(literal) = λ_min( A_SS - A_SR A_RR^+ A_RS )   (Schur complement),
μ_J²(restricted) = λ_min(A_SS)  ≥  μ_J²(literal).
```

Using the restricted value would report `κ_J` **too small** and make
Proposition 5.5 look artificially less vacuous — an error in the flattering
direction, which is why it is a blocker.  `κ_J` is therefore always computed
from the **literal** (Schur-complement) `μ_J`; `μ_J(restricted)` is reported
alongside purely to quantify the gap.  `A` is `K×K` with `K = 10`, so both are
exact and cost nothing.

`L_J = sqrt(λ_max(J J^⊤))` over all of `R^K` as stated — also from the same
`K×K` matrix; no SVD of the full `K×d` Jacobian is needed.

*Note to the manuscript owner (not an edit request): if the proof only needs
`J^⊤` to be well conditioned on `S`, the assumption's intended form is
`Π J J^⊤ Π ⪰ μ_J² Π`, which is the restricted reading.  The experiment reports
both so the manuscript can say which it means.  This suite assumes the literal
Loewner form as written.*

---

## 2. Evidence tiers

The review's structural finding: v1 put three logically different kinds of
evidence under one "closed-loop verification" heading, which invites the charge
of claim inflation.  v2 separates them and never mixes them in one table.

| Tier | What it is | Contents |
|---|---|---|
| **T1** | **Theorem-exact implementation closure.** `N=1`, declared `q`, quantities the theorem names. A failure here is a bug or a false theorem. | T1.1 sign law; T1.2 zero-point directional derivative; T1.3 factorization by finite differences; T1.4 the `q`-sweep |
| **T2** | **Scope and falsification diagnostics.** Quantities the theorem/assumption names, in regimes where the statement is silent or can be falsified. | T2.1 `N>1` collinearity loss; T2.2 A2 along trajectories; T2.3 Jacobian conditioning; T2.4 Proposition 5.5 certificate funnel |
| **T3** | **Beyond-theorem empirical behaviour.** Interesting, reported, never called closure. | T3.1 finite-step risk change; T3.2 momentum trajectories |

---

## 3. P1 — the binary sign law (Tier 1, plus T2.1)

### Common setup

* **Task.** Three CIFAR-10 pairs, fixed a priori: `auto_frog` (1 vs 6, easy),
  `plane_ship` (0 vs 8, medium), `cat_dog` (3 vs 5, hard).  Binary label 1 = the
  second class of the tuple, so `p := p_1` is that class's probability.
* **Models.** `ResNet26GN` (the manuscript's ResNet-26 main path, GroupNorm),
  `num_classes = 2`, 3 seeds per pair — 9 trained models.  GroupNorm makes the
  `N = 1` forward map a function of the single instance.  Robustness arm:
  `WRN2810` with BatchNorm in **eval** mode (frozen running statistics),
  1 pair × 1 seed.
  *Trained, source accuracies: 0.991/0.987/0.986, 0.953/0.951/0.952,
  0.865/0.869/0.875 — an a-priori difficulty spread realized.*
* **Adapted subset θ.** Normalization-layer affine parameters (Tent's protocol,
  the subset Section 5 names).  `all` and `encoder` get a **smoke test only**:
  the identity is subset-invariant by construction, so a large sweep over
  subsets buys no additional test of the theorem (review, MAJOR).
* **Shift.** Clean + CIFAR-10-C {`gaussian_noise`, `fog`, `contrast`,
  `jpeg_compression`} × severities {1,3,5} = 13 cells.
* **Temperature.** `T = 1` is the primary network and the only one entering a
  headline number.  `T ∈ {2,4}` is a **controlled boundary intervention**,
  reported separately and never pooled with `T = 1`.
* **Target law.** `ε ∈ {0, 0.1, 0.25, 0.4}` (the declared `Q_ε` of §0).

### T1.1 — the sign identity

Per episode (one instance, one `T`, one `ε`):

```
A := 1{ sign(cos(g_H, g_R)) == sign(s·(q-p)) },   |α_ent| := |cos(g_H, g_R)|
```

`g_H`, `g_R` by independent autograd on `H = -Σ_k p_k log p_k` (Tent's own
objective, written K-class so the code does not presuppose `K=2`) and on
`R = -q log p - (1-q) log(1-p)`.

**Reporting.** The theorem asserts a deterministic identity, so a proportion
with a Wald interval is the wrong instrument (review, MAJOR).  The headline is

```
V / N violations under the preregistered numerical criterion,
```

with the **complete dump of every violating episode**, plus `min |α_ent|`,
`max` and quantiles of the residuals.  The nine per-model estimates are all
printed; no inferential CI is attached to a quantity theory pins at 1.  CIs are
reserved for the genuinely stochastic T3 outcomes.

**The discriminating comparison** (this is what makes T1.1 a test rather than a
tautology).  The naive reading is *modal-label correctness*, a deterministic
quantity under the declared law:

```
h_naive := +1  ⟺  argmax p == argmax q .
```

Under `Q_0` the theorem and `h_naive` coincide.  Under `Q_ε`, `ε > 0`, they
disagree exactly when `p` overshoots `q` on the modal class — the model predicts
the modal class correctly and the theorem still says `α_ent = -1`.  We report
the **disagreement rate** and confirm the theorem is right on every disagreeing
episode.  *No sampled noisy labels appear anywhere*; a sampled label is a random
event, the theorem's sign is a function of the full `q`, and comparing them
would confuse two different objects (review, MAJOR).

**Stratification.** Frozen before any sweep, never re-cut afterwards, empty
cells reported as `n = 0`:
`|p - 1/2| ∈ [0,1e-6), [1e-6,1e-4), [1e-4,1e-2), [1e-2,0.1), [0.1,0.4), [0.4,0.5]`
and `|q - p| ∈ [0,1e-6), [1e-6,1e-4), [1e-4,1e-2), [1e-2,0.1), [0.1,1]`.

**Numerical attribution hierarchy.** "float64 fixed it" is evidence, not proof
(review, MAJOR).  A disagreement is attributed to finite precision only if it
climbs the whole ladder: (1) float32 network+autograd; (2) same weights in
float64; (3) a high-precision scalar reference `p = σ(s)`, `q - p`, `s(q-p)`
computed from the raw logit difference; (4) random-direction finite differences
(T1.3); (5) residual magnitudes compared against machine epsilon times the
gradient norms.  Only if the disagreement vanishes with precision *and* the
residual shrinks with precision is it numerical.

### T1.2 — zero-point directional derivative (replaces v1's E3)

The theorem's first-order content is a derivative **at zero**, not the sign of a
finite-step risk change (review, MAJOR — v1 conflated them).  With
`v := -g_H/‖g_H‖`,

```
d/dη R(θ + ηv) |_{η=0}  =  -α_ent ‖g_R‖ .
```

Measured by central difference, an independent numerical route that never
touches the `⟨g_H, g_R⟩` dot product:

```
D_h := [ R(θ + hv) - R(θ - hv) ] / (2h),      h ∈ {1e-5, 1e-4, 1e-3}
```

Estimand: the relative error `|D_h + α_ent‖g_R‖| / (α_ent‖g_R‖)` and its
behaviour as `h → 0` (a clean `O(h²)` decay is the closure; anything else is a
finding).  `R` at the displaced parameters is evaluated from the displaced `p`
through the *definition* of `R`, which is a definition, not the theorem.

### T1.3 — factorization by finite differences (replaces v1's full-scale E1)

v1's residuals `r_H`, `r_R` compare two autograd calls on one computational
graph: they catch a wrong loss or a wrong subset, but they are not an
independent numerical route (review, MAJOR).  On a preregistered **subsample**
(500 episodes, seeded), draw random unit directions `v` in the adapted subset
and check the theorem's factorizations as scalar finite differences:

```
D_v H  ≈  -p(1-p)·s·D_v s ,        D_v R  ≈  (p-q)·D_v s .
```

Residuals `r_H`, `r_R` are still recorded on every episode — they cost one extra
vector norm each — but they are diagnostic, not headline.

### T1.4 — the `q`-sweep (new; the review's own suggestion, and the cleanest test)

Fix a model, an instance, `θ` and hence `p`.  Sweep `q` over a dense grid
(`q ∈ {0.01,…,0.99}` plus a fine grid around `p`), recomputing `g_R` by
independent autograd at each `q`.  The theorem predicts `α_ent` flips sign
**exactly at `q = p`**, while `argmax p` — the modal prediction — never changes.

This exhibits, in one figure, that Theorem 5.2 is a **calibration law and not a
correctness law**, which four `ε` points can only gesture at.  It is the
cheapest and sharpest instrument in P1 and is a headline result, not an
appendix.  Estimand: the measured flip location `q_flip` and `|q_flip - p|`,
across 200 (model, instance) pairs spanning the `p` range.

### T1.5 — adversarial boundary-resolution sweep (added in v3)

Fixed bins tell you where agreement degrades on the episodes the data happens to
supply.  A **direct** construction is sharper: fix a network and an instance,
hence `s` and `p`, and set the declared conditional to

```
q = p ± δ ,    δ ∈ {1e-1, 1e-2, …, 1e-12} ,
```

so the theorem's exact distance-to-degeneracy `|q - p|` is a *controlled input*
rather than an observed covariate; then sweep `|s|` over decades with the
temperature knob.  Estimand: the **numerical sign-resolution boundary** — the
smallest `|q - p|` (and the smallest `|s|`) at which `sign(α_ent)` still
reproduces `sign(s(q-p))`, in float32 and in float64 separately.

This measures the thing the fixed-bin table only gestures at, and it makes the
numerical attribution testable rather than rhetorical: the boundary should move
by roughly the ratio of the two machine epsilons when precision changes, and
should not move at all if the failure were the theorem's rather than the
arithmetic's.

### T2.1 — where the theorem stops (`N > 1`)

Batch gradients are `g_H^B = (1/N)Σ a_i ∇s_i`, `g_R^B = (1/N)Σ b_i ∇s_i`, which
are **not** collinear in general, and there is no batch scalar RHS that
Theorem 5.2 defines.  Reporting `Pr[A=1]` at `N>1` would therefore be reporting
agreement with a quantity the theorem does not define (review, BLOCKER).  v2
reports **only** `|cos(g_H^B, g_R^B)|` and its departure from 1, as a function
of `N ∈ {1,2,4,8,16}`.  No agreement rate.

### P1 episode budget

`9 models × 13 shift cells × 200 instances × 3 temperatures = 70 200` base
episodes, each evaluated at 4 declared laws.  `T = 1` alone is the primary
`23 400`.  Plus the `q`-sweep (200 instances × ~130 grid points), the finite-
difference subsample (500), the `N>1` arm, the float64 10 % recomputation, and
the subset/architecture smoke tests.

---

## 4. P2 — A2 persistence and Jacobian conditioning (Tier 2)

### Scope statement (this *is* the estimand)

A2 constrains **every point of a region** `Θ_loc`; a trajectory is a measure-zero
sample of it.  Therefore:

* Trajectory measurements **can falsify** A2-with-`α > 0`.  The criterion must
  be stated on the inner product, not on a cosine that the vanishing-gradient
  convention sets to 0 (review, MAJOR):

  ```
  falsifies A2 at θ_t  ⟺  ‖ḡ_t‖ > 0 ∧ ‖∇R_t‖ > 0 ∧ ⟨ḡ_t, ∇R_t⟩ ≤ 0 ,
  ```
  and then, *given A4*, no `Θ_loc` containing the realized path satisfies A2
  with any `α > 0`.
* Trajectory measurements **cannot verify** A2.

**Path statistics are not region constants.**  `min_t α_t ≥ α_*`,
`min_t ρ_t ≥ c_*`, `max_t ρ_t ≤ C_*`.  They are therefore named **path minimum
alignment**, **path minimum / maximum relative scale** — never "empirical
`c_g`, `C_g`" (review, MAJOR).

**`Θ_loc` is predefined**, so that A4 and the region constants refer to
something: `Θ_loc := {θ : ‖θ - θ_0‖ ≤ r}` with `r` fixed before the sweep at a
value covering the realized trajectories (recorded; trajectories that leave it
are counted).

### Protocol

* **Recursion.** **Plain SGD, no momentum** — S2's recursion has no momentum
  state, and a momentum trajectory is simply not the trajectory A4 constrains
  (review, BLOCKER).  `θ_{t+1} = θ_t - η g(θ_t, ξ_t)`, `η = 1e-3`, 20 steps,
  `N = 1`, episodic snapshot/restore.  The manuscript's momentum-0.9 trajectory
  is run as **T3.2**, a practice-trajectory stress test, and is never used for
  envelope closure.
* **Target law.** The declared deterministic `Q_0` (§0), so `∇R` is the
  conditional expected cross-entropy under a declared law, not the loss at an
  observed label (review, BLOCKER).
* **Model.** The manuscript's 10-class `ResNet26TTT` source checkpoint, 3 seeds.
* **Objectives.** `tent` (entropy; adapted subset = norm affine) and `ttt_rot`
  (rotation; adapted subset = encoder).
* **`ḡ` for rotation is computed by EXACT ENUMERATION, not Monte Carlo**
  (review, BLOCKER).  The objective's randomness `ξ` is the rotation index,
  drawn uniformly from `{0,1,2,3}`; by linearity of expectation
  `ḡ(θ) = (1/4) Σ_{k=0}^{3} ∇_θ CE(f_ssl(rot_k(x)), k)` exactly, in 4 backward
  passes.  With `ḡ` exact, `⟨ḡ_t, ∇R_t⟩ ≤ 0` is a fact and not a Monte-Carlo
  event, and the falsification claim needs no confidence bound.
* **Conditions.** clean + 4 corruptions × 3 severities; 100 instances per
  (cell, seed, objective).

### T2.2 estimands — persistence

Per step `t = 0..20`: `α_t = cos(ḡ_t, ∇R_t)`, `m_t = ⟨ḡ_t, ∇R_t⟩`,
`ρ_t = ‖ḡ_t‖/‖∇R_t‖`, `R_t`, `‖θ_t - θ_0‖`.
Per trajectory: **path minimum alignment** `min_t α_t`, **path min/max relative
scale**, `T_flip = min{t : m_t ≤ 0}` (∞ if never), and the A2-falsification
indicator above.  Population: `Pr[falsified]`, decay curve `E[α_t]` vs `t`,
stratified by severity and objective.

`sign_stable` is **removed from the closure estimands** — A2 asks for
`α(θ) ≥ α_0 > 0`, never for a constant sign, and a trajectory pinned at `-0.8`
has a perfectly stable sign while failing A2 outright (review, MAJOR).  It
survives only as an exploratory visualization, labelled as such.

Local Lipschitz witness `L̂ = max_t ‖∇R_{t+1} - ∇R_t‖ / ‖θ_{t+1} - θ_t‖`, a
**lower** bound on `L_*`.  Then

```
η̂ := (min_t α_t)(min_t ρ_t) / ( L̂ · (max_t ρ_t)² )   ≥   η_* = α_* c_* /(L_* C_*²).
```

`η̂` is therefore a **trajectory-derived optimistic upper bound on the maximal
admissible step cap**, not a certified cap — and only one direction is
informative: if `η_practical > η̂` then certainly `η_practical > η_*`; if
`η_practical < η̂`, nothing follows (review re-derived this; v1's name for it was
wrong even though the direction was right).

### T2.5 estimands — neighbourhood search for A2 counterexamples (added in v3)

A trajectory is 21 points; A2 is a statement about a region.  Falsification
power can be raised cheaply, and without pretending to verify anything, by
searching a **preregistered shell** around each trajectory point:

```
radii  r ∈ {1e-4, 1e-3, 1e-2} × ‖θ_t‖ ,   n_dir random unit directions per shell,
report  min over the sampled shell of  ⟨ḡ(θ), ∇R(θ)⟩  and of  α(θ).
```

This is a *lower bound on the region minimum* — sampling a ball can only
under-estimate how negative the alignment gets — so a negative value found
anywhere in the shell falsifies A2 on any `Θ_loc` containing that shell, while a
uniformly positive sample proves nothing.  Stated that way it is pure
falsification machinery and claims nothing else.

The interesting outcome is the asymmetric one: if the trajectory itself never
goes negative but a `1e-3`-relative perturbation does, the finding is
**"persistent alignment is not locally robust"** — considerably more
informative than 21 points along one path.

### T2.3 estimands — Jacobian conditioning

At preregistered `t ∈ {0,1,5,10,20}` (not every step — a compute decision fixed
in advance), on the adapted subset: build `A = J J^⊤ ∈ R^{K×K}` from `K = 10`
backward passes, then

* `L_J = sqrt(λ_max(A))` over all of `R^K`;
* `μ_J(literal)` from the **Schur complement** as in §1;
* `μ_J(restricted) = sqrt(λ_min(A_SS))`, reported only to size the gap;
* `κ_J = L_J / μ_J(literal)`;
* rank-deficiency of `S` (the two spanning vectors parallel) detected, handled
  as a 1-D span, and counted.

### T2.4 estimands — Proposition 5.5 certificate funnel

Report a **three-level funnel**, not a single trigger rate, so a zero at the end
still says *where* it died (review, MAJOR):

```
eligible  →  Z ≥ 0  →  LB > 0
```

* **eligible**: Definition 5.3's hypotheses hold — unique largest `p_k`,
  `p_min > 0`, `p` not uniform — and `q ≠ p`, `μ_J > 0`.
* `Z := Δ·mar - Λ_tail·(PCD - |Δ|)`, the logit-space bracket.
* `LB := (1/κ_J²)·Z / (2√K·Λ(p)) - (κ_J² - 1)`, the **full** lower bound.
  `LB > 0` certifies `α_ent > 0`; `LB = 0` certifies only non-negativity;
  `LB ≤ -1` is fully vacuous relative to the trivial `α ≥ -1`.
* **Soundness check**: on every episode with `LB > 0`, the measured `α_ent` must
  be `> 0`.  A counterexample would be a proof bug and is the highest-value
  outcome available; we look for it explicitly.
* **`κ_crit`**: the largest `κ_J` at which `LB > 0` would still hold for that
  episode.  This converts "the bound is vacuous" into a quantitative diagnosis
  of *how far* the pullback conditioning is from activating it.
* `q` here obeys the same discipline as P1: the declared `Q_0`, not a dataset
  one-hot silently promoted to a conditional law (review, MAJOR).

If `κ_J` turns out large and the certificate never fires, the finding is
reported as: *the sufficient bound is mathematically valid but numerically
inactive under the network's raw parameterization; the dominant obstruction is
Jacobian anisotropy rather than the logit-space calibration term* — supported by
the four numbers `α_ent`, `Z`, `κ_J`, `LB` and by `κ_crit`.  The pattern
`Z > 0, α_ent > 0, LB ≪ 0` says precisely that the calibration half carries
signal and the pullback kills the certificate.

---

## 5. Compute

**The v1 budget is not carried over as a promise.**  A microbenchmark runs
first — 50–100 trajectory-points and 200 P1 episodes, timed — and the sweep is
sized as `seconds/unit × planned units` from measured numbers.  Recorded in
`COMPUTE_BUDGET.json` before the sweep launches.  v1's arithmetic also
double-counted the per-`ε` backward passes (one extra `R` backward per `ε`, not
three): the per-episode cost is `H:1, s:1, R:4` = 6 backward passes plus the
central-difference and step forwards.

Order of execution, so that the highest-value evidence lands first:
T1.4 `q`-sweep → T1.5 boundary → T1.1/T1.2 primary → T2.2/T2.3/T2.4 →
T3.2 → T2.1 → T2.5 → final analysis and verification.  Each stage is a lane that
waits on the previous one's completion marker: one GPU, one lane at a time.

**Measured** (not projected): P1 ≈ 3.5 GPU-h, P2 ≈ 6 GPU-h (including 1.75 h of
source training), T1.5 ≈ 0.2 GPU-h, T2.1 ≈ 0.8 GPU-h, T2.5 ≈ 2.6 GPU-h —
**≈ 13 GPU-hours**, below the 24 GPU-hour threshold that would have required
approval before launching.

**P3 (ImageNet-C ResNet-50) was raised to the planner and dropped by decision.**
It is uncosted, would open a new experimental context for breadth alone, and the
same box time buys T2.1 and T2.5 instead — of which T2.5 is the only remaining
instrument in the suite that can *falsify* anything.  Breadth across a third
backbone is worth less to this paper than a falsification-capable check on A2.

---

## 6. Verification (house style)

Per experiment: `run_*.py` (records), `analyze_*.py` (reported numbers),
`verify_*.py` — an independently written recomputation that reloads the raw
records, recomputes every headline number by a different aggregation route, and
performs a **reproduce-from-record** check on 200 random episodes: reload the
model and the episode's seed and index, recompute `p`, `s`, `q`, `α_ent`, RHS
from scratch, and assert agreement with the stored record.  No number reaches
`RESULTS.md` that the verifier has not independently reproduced.

## 7. Changelog from v1 (what the review forced)

**Blockers.** (1) `q` in every arm now comes from an explicitly declared target
distribution `Q_ε`, in P1 *and* P2 *and* Proposition 5.5 — v1 justified arm A's
one-hot `q` by "CIFAR labels are effectively deterministic", which is the exact
observed-label-as-conditional-law error the suite exists to avoid.  (2) P2 runs
plain SGD; momentum demoted to T3.  (3) `μ_J` is the literal Loewner constant
via Schur complement, not a 2-D restricted minimum that flatters `κ_J`.
(4) `N>1` reports only batch cosine, never an agreement rate against a
single-instance RHS the theorem does not define at `N>1`.  (5) evidence split
into T1/T2/T3 so that implementation closure, scope diagnostics and
beyond-theorem behaviour are never reported under one heading.

**Majors.** Arm C (binned `q̂`) deleted outright.  Sampled noisy labels deleted;
the naive comparator is modal-label correctness.  E3 replaced by the zero-point
directional derivative; the finite-`η` sweep survives as T3.1 under its own
name.  E1 demoted and supplemented with random-direction finite differences.
`sign_stable` removed from the A2 estimands.  A2 falsification stated on the
inner product with explicit non-degeneracy.  Rotation `ḡ` computed by exact
enumeration over the 4 rotations instead of 8 Monte-Carlo draws.  Path extrema
renamed to path statistics, never A2 constants.  `η̂` renamed a
trajectory-derived optimistic upper bound.  `Θ_loc` predefined.  `T=1` never
pooled with `T>1`.  Proportion CIs replaced by violation counts plus the full
violation dump for the deterministic identities.  Subset-robustness sweep cut to
a smoke test.  `s` used in place of a recomputed `logit(p)` everywhere.  The
`q`-sweep added as a headline instrument.  Compute re-derived by microbenchmark.

## 7b. Changelog v2 → v3 (what the second review added)

The second review was a fresh cold read of v2 by the same backend.  It
**independently re-derived the `μ_J` counterexample** — `A = [[1,1],[1,1]]`,
`Π = e_1 e_1^⊤` gives `μ_restricted = 1` but `μ_literal = 0` — reaching the same
conclusion v2 had already adopted; our implementation reproduces that
counterexample exactly and agrees with an independent bisection route to
`1.4e-14` over 200 random `10×10` cases, so Assumption 5.4's measurement is now
closed and cross-verified rather than merely argued.

Its copy of DESIGN.md was truncated mid-Section 4, so several of its findings
restate v1 defects that v2 had already fixed (the `N>1` agreement rate, the
momentum recursion, arm A's wording).  Those are recorded as confirmations.
What it added, and v3 adopts:

* **T1.5**, the adversarial boundary-resolution sweep — construct `q = p ± δ`
  down to `δ = 1e-12` instead of waiting for the data to supply near-boundary
  episodes.
* **T2.5**, the neighbourhood shell search for A2 counterexamples.  Both T1.5 and
  T2.5 are implemented and queued; T2.5 was prioritized over a third-backbone
  breadth experiment precisely because it can return a negative.
* **T3.1 renamed** *finite displacement along the entropy-gradient direction*.
  The step is norm-normalized, so it is **not** a statement about Tent at
  `lr = 1e-3`; a separate actual-optimizer arm would be needed for that, and is
  not claimed.
* **Arm A wording hardened** to *deterministic-label empirical target
  distribution constructed on the fixed CIFAR image support* — never "CIFAR's
  labels are effectively deterministic", which invites the question of how we
  know the true `Q(y|x)` is deterministic.
* **`Λ(p)` must be the exact `max_k p_k|log p_k + H(p)|`**, not the
  `log(1/p_min)` upper bound the proposition also offers; using the bound would
  produce a different, looser certificate and would have to be labelled as such.
* **Bin-edge provenance**: the stratification edges are powers-of-ten
  numerical-resolution strata, not data-adaptive quantiles, and the design file's
  hash and timestamp are recorded with the results so the freeze is checkable.
* **No cluster bootstrap as primary inference** for the deterministic
  identities: all nine per-model estimates are printed, with range.

## 8. Non-negotiables

* Every occurrence of `R`, `∇R`, `ΔR`, `PCD`, `Δ`, `mar` uses the declared `q`.
  Sampled labels never construct a theorem estimand.
* Every episode record is retained; every RNG is explicitly seeded.
* No host name, address or credential appears in any file in this directory or
  in any script.
