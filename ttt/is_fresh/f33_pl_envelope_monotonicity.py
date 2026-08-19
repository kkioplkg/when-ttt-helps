"""F33 -- the local-PL envelope's monotonicity, stated correctly.

WHY THIS SCRIPT EXISTS
----------------------
The local-PL envelope proves the valid inequality

    B(t) := (1 - c1)^t delta^2 + c2 * min{t, 1/c1}   >=   E Exc(theta_t)

with c1 = eta mu alpha c_g in (0, 1], c2 = L eta^2 sigtot^2 / 2 and the
noise floor c5 = c2/c1.  The statement of the envelope additionally
asserted that for 0 < c1 < 1 this bound *decreases* toward c5 as t
increases over the whole range 0 <= t <= T, and the paragraph after it
asserted that past the certified horizon t_Phi the bound "keeps
decreasing toward c5".

BOTH ASSERTIONS ARE FALSE, and this script certifies that.  The early
branch is

    B(t) = (1 - c1)^t delta^2 + c2 t      (t <= 1/c1),

whose linear noise-accumulation term can dominate the decay of the
initial-error term.  The proof never established the claim: it
establishes strict approach to the floor only once the LATE branch
t >= 1/c1 is active.  Nothing downstream needed the false claim --
Corollary "certified improvement horizon" evaluates the VALID bound at
one selected horizon -- so the repair is confined to the statement.

WHAT IS CHECKED
  A. THE DISPLAYED BOUND IS STILL A VALID RELAXATION OF THE RECURSION.
     The one-step descent lemma gives E_{t+1} <= (1-c1) E_t + c2, hence
     E_t <= (1-c1)^t delta^2 + c2 * S_t with the exact geometric sum
     S_t = (1 - (1-c1)^t)/c1.  The displayed bound replaces S_t by
     min{t, 1/c1}.  That replacement is checked to be an over-estimate,
     S_t <= min{t, 1/c1}, over a dense admissible grid -- i.e. the
     inequality the theorem displays is sound, and only the monotonicity
     sentence attached to it is not.

  B. REFUTATION OF THE GLOBAL MONOTONICITY CLAIM.
     (i) The worked counterexample c1 = 0.1, c2 = 1, delta^2 = 11:
         B(1) = 10.9 < B(0) = 11 but B(2) = 10.91 > B(1).
     (ii) The starker small-initial-error case delta^2 = 0.1:
         B(0) = 0.1 but B(1) = 1.09.
     (iii) A RANDOM SEARCH over parameters drawn from the assumptions
         themselves -- 0 < mu <= L, alpha in (0,1], 0 < c_g <= C_g,
         sigtot >= 0, eta in (0, alpha c_g/(L C_g^2)] (the step cap),
         delta^2 >= 0 -- counting how often B fails to be nonincreasing
         on 0 <= t <= T.  Every reported violation is realized by an
         admissible parameter tuple, so the refutation is not an artifact
         of choosing c1, c2, delta^2 freely.

  C. THE CORRECTED STATEMENT, CERTIFIED.
     C1. Exact increment identity, for every t >= 0:
             B(t+1) - B(t)
               = -c1 (1-c1)^t delta^2
                 + c2 (min{t+1, 1/c1} - min{t, 1/c1}).
     C2. LATE BRANCH.  For 0 < c1 < 1, delta^2 > 0 and t >= 1/c1,
         B(t) = (1-c1)^t delta^2 + c5 is strictly decreasing and
         converges to c5 from above, equalling it at no finite t.
     C3. EARLY BRANCH.  For t, t+1 <= 1/c1 the increment is exactly
         c2 - c1 (1-c1)^t delta^2, so B strictly decreases at step t
             IF AND ONLY IF   (1-c1)^t delta^2 > c5,
         equivalently t < ln(Phi)/ln(1/(1-c1)) with the phase ratio
         Phi = c1 delta^2/c2 = delta^2/c5.  In particular when Phi <= 1
         the bound is nondecreasing ON THE EARLY BRANCH.
     C4. The SUFFICIENT half of C3 holds on the whole range, crossing
         step included: (1-c1)^t delta^2 > c5 implies B(t+1) < B(t) for
         every t >= 0, because capping the noise term can only shrink
         the increment.

  D. THE CERTIFIED HORIZON SITS ON THE LATE BRANCH WHEN Phi >= e.
     t_Phi = ceil(ln(Phi)/c1) satisfies t_Phi >= 1/c1 exactly when
     ln Phi >= 1.  So under the corollary's own headline hypothesis
     Phi >= 10 the certified horizon is always in the regime where the
     bound IS monotone -- which is why the corollary's conclusions are
     untouched by the repair.  Checked over the random admissible draws.

  E. THE CERTIFIED-HORIZON COROLLARY IS UNAFFECTED.
     For every admissible draw with Phi > 1 and t_Phi <= T, the two
     inequalities the corollary states are re-checked numerically:
         B(t_Phi) <= c5 (1 + ln Phi) + c2 <= delta^2 (2 + ln Phi)/Phi,
     together with the Phi >= 10 consequence B(t_Phi) <= 0.44 delta^2.
     The corollary evaluates a valid upper bound at one horizon and
     never appeals to monotonicity, so it stands as written.

  F. WHAT Phi <= 1 DOES AND DOES NOT GIVE.  The envelope's statement
     used to read, at Phi <= 1, "the bound is nondecreasing from t = 0
     onward".  THAT IS FALSE, for the same reason as B: the late branch
     is strictly decreasing whatever Phi is, and the crossing step can
     already decrease.  Its conclusion nevertheless survives, and this
     block separates the two:
     F1. REFUTATION.  c1 = c2 = 0.25, delta^2 = 1 gives Phi = 1 exactly,
         yet B(4) = 1.31640625 > B(5) = 1.2373046875 -- a decrease at
         Phi <= 1.  Realized by admissible constants
         (L = mu = alpha = c_g = C_g = 1, eta = 0.25 <= eta_max = 1,
         sigtot^2 = 8), and searched for over the admissible draws.
     F2. THE EARLY BRANCH IS STILL NONDECREASING under Phi <= 1: the
         increment c2 - c1 (1-c1)^t delta^2 >= c1 delta^2 (1-(1-c1)^t)
         >= 0 there.
     F3. THE SURVIVING GLOBAL STATEMENT: under Phi <= 1,
         B(t) >= delta^2 = B(0) at every integer 0 <= t <= T, so t = 0
         minimizes the displayed envelope.  Late branch: B(t) > c5 >=
         delta^2.  Early branch: c2 t >= c1 delta^2 t >= delta^2
         (1-(1-c1)^t) by Bernoulli, valid for t >= 1 -- and t indexes
         iterates, so t >= 1 is every step but t = 0 itself.  The
         Bernoulli step is exactly why the statement is made at integer
         step counts: on the REAL interval (0,1) the displayed
         expression can and does dip below delta^2, which F3 also
         exhibits rather than leaving implicit.

Nothing is simulated and no record is read: this is a closed-form audit
of the envelope's own algebra.

Usage: python f33_pl_envelope_monotonicity.py
Writes experiments/results/is_fresh/f33_pl_envelope_monotonicity.json
"""
from __future__ import annotations

import argparse

import numpy as np

import common as C

SEED = 20260807


# ------------------------------------------------------------------ the bound

def bound(t, c1, c2, d2):
    """The displayed envelope B(t) = (1-c1)^t d2 + c2 min{t, 1/c1}."""
    t = np.asarray(t, dtype=float)
    return (1.0 - c1) ** t * d2 + c2 * np.minimum(t, 1.0 / c1)


def geometric_partial_sum(t, c1):
    """S_t = sum_{j=0}^{t-1} (1-c1)^j, the exact noise accumulation."""
    t = np.asarray(t, dtype=float)
    return (1.0 - (1.0 - c1) ** t) / c1


# ----------------------------------------------------- admissible sampling

def draw_admissible(rng, n):
    """Draw n parameter tuples satisfying A1-A3 and the step-size cap.

    The constants are exactly those of the envelope: 0 < mu <= L,
    alpha in (0,1], 0 < c_g <= C_g < infinity, sigtot >= 0, and
    0 < eta <= eta_max = alpha c_g / (L C_g^2).  delta^2 = Exc(theta_0)
    is a free nonnegative initial excess risk -- A1-A4 do not constrain
    it.  Note c1 = eta mu alpha c_g <= alpha^2 (mu/L) (c_g/C_g)^2 <= 1
    automatically, which is why the theorem may write c1 in (0,1].
    """
    L = 10.0 ** rng.uniform(-2.0, 2.0, n)
    mu = L * rng.uniform(1e-3, 1.0, n)
    alpha = rng.uniform(1e-3, 1.0, n)
    c_g = 10.0 ** rng.uniform(-2.0, 1.0, n)
    C_g = c_g * (1.0 + 10.0 ** rng.uniform(-3.0, 1.0, n))
    sigtot = 10.0 ** rng.uniform(-3.0, 2.0, n)
    eta_max = alpha * c_g / (L * C_g ** 2)
    eta = eta_max * rng.uniform(1e-4, 1.0, n)
    d2 = 10.0 ** rng.uniform(-3.0, 3.0, n)

    c1 = eta * mu * alpha * c_g
    c2 = L * eta ** 2 * sigtot ** 2 / 2.0
    return {"L": L, "mu": mu, "alpha": alpha, "c_g": c_g, "C_g": C_g,
            "sigtot": sigtot, "eta_max": eta_max, "eta": eta, "d2": d2,
            "c1": c1, "c2": c2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200000)
    ap.add_argument("--horizon", type=int, default=200)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    T = args.horizon
    ts = np.arange(0, T + 1)

    # ---------------- A. the displayed bound relaxes the exact recursion
    a_c1 = np.concatenate([np.linspace(1e-4, 1.0, 4000)])
    worst_gap = np.inf
    n_relax_violations = 0
    for c1 in a_c1:
        S = geometric_partial_sum(ts, c1)
        cap = np.minimum(ts.astype(float), 1.0 / c1)
        gap = cap - S
        n_relax_violations += int((gap < -1e-12).sum())
        worst_gap = min(worst_gap, float(gap.min()))
    relaxation = {
        "claim": ("S_t = (1-(1-c1)^t)/c1 <= min{t, 1/c1}, so the DISPLAYED "
                  "bound over-estimates the exact geometric noise "
                  "accumulation and the inequality the theorem prints is "
                  "sound"),
        "n_c1_values": int(len(a_c1)),
        "n_t_values": int(len(ts)),
        "n_violations": int(n_relax_violations),
        "worst_signed_gap_min_minus_S": worst_gap,
    }

    # ---------------- B(i)/(ii). the worked counterexamples
    ce1 = {"c1": 0.1, "c2": 1.0, "d2": 11.0}
    b1 = bound(ts[:6], ce1["c1"], ce1["c2"], ce1["d2"])
    ce1.update({
        "B_0_to_5": [float(x) for x in b1],
        "B0": float(b1[0]), "B1": float(b1[1]), "B2": float(b1[2]),
        "decreases_at_t0": bool(b1[1] < b1[0]),
        "INCREASES_at_t1": bool(b1[2] > b1[1]),
        "increment_B2_minus_B1": float(b1[2] - b1[1]),
        "c5_noise_floor": ce1["c2"] / ce1["c1"],
        "phase_ratio_Phi": ce1["c1"] * ce1["d2"] / ce1["c2"],
    })
    ce2 = {"c1": 0.1, "c2": 1.0, "d2": 0.1}
    b2 = bound(ts[:6], ce2["c1"], ce2["c2"], ce2["d2"])
    ce2.update({
        "B_0_to_5": [float(x) for x in b2],
        "B0": float(b2[0]), "B1": float(b2[1]),
        "INCREASES_at_t0": bool(b2[1] > b2[0]),
        "c5_noise_floor": ce2["c2"] / ce2["c1"],
        "phase_ratio_Phi": ce2["c1"] * ce2["d2"] / ce2["c2"],
    })

    # a witness that the counterexample is REALIZED by admissible constants,
    # not merely by free choice of (c1, c2, delta^2):
    #   L = mu = alpha = c_g = C_g = 1  =>  eta_max = 1; take eta = 0.1, so
    #   c1 = 0.1; c2 = L eta^2 sigtot^2/2 = 1 needs sigtot^2 = 200.
    wit = {"L": 1.0, "mu": 1.0, "alpha": 1.0, "c_g": 1.0, "C_g": 1.0,
           "eta": 0.1, "sigtot": float(np.sqrt(200.0)), "d2": 11.0}
    wit["eta_max"] = wit["alpha"] * wit["c_g"] / (wit["L"] * wit["C_g"] ** 2)
    wit["step_condition_holds"] = bool(0 < wit["eta"] <= wit["eta_max"])
    wit["c1"] = wit["eta"] * wit["mu"] * wit["alpha"] * wit["c_g"]
    wit["c2"] = wit["L"] * wit["eta"] ** 2 * wit["sigtot"] ** 2 / 2.0
    wit["c1_in_open_unit_interval"] = bool(0 < wit["c1"] < 1)
    wb = bound(ts[:3], wit["c1"], wit["c2"], wit["d2"])
    wit["B_0_1_2"] = [float(x) for x in wb]
    wit["INCREASES_at_t1"] = bool(wb[2] > wb[1])

    # ---------------- B(iii). random search over admissible parameters
    P = draw_admissible(rng, args.draws)
    c1, c2, d2 = P["c1"], P["c2"], P["d2"]
    ok = (c1 > 0) & (c1 < 1)                    # the claim's own hypothesis
    c1, c2, d2 = c1[ok], c2[ok], d2[ok]
    n = int(c1.size)

    Bm = ((1.0 - c1)[:, None] ** ts[None, :] * d2[:, None]
          + c2[:, None] * np.minimum(ts[None, :].astype(float),
                                     (1.0 / c1)[:, None]))
    diffs = np.diff(Bm, axis=1)
    any_increase = (diffs > 0).any(axis=1)
    c5 = c2 / c1
    Phi = c1 * d2 / c2

    search = {
        "n_admissible_draws": n,
        "horizon_T": T,
        "hypotheses": "0 < c1 < 1, step cap eta <= alpha c_g/(L C_g^2)",
        "n_with_a_strictly_increasing_step": int(any_increase.sum()),
        "fraction_with_a_strictly_increasing_step": float(any_increase.mean()),
        "n_monotone_nonincreasing_throughout": int((~any_increase).sum()),
        "note": ("the claim was that EVERY admissible draw is nonincreasing "
                 "over 0<=t<=T; a single increasing step refutes it"),
    }

    # ---------------- C1. exact increment identity
    cap = np.minimum(ts[None, :].astype(float), (1.0 / c1)[:, None])
    pred = (-c1[:, None] * (1.0 - c1)[:, None] ** ts[None, :-1] * d2[:, None]
            + c2[:, None] * (cap[:, 1:] - cap[:, :-1]))
    # The identity is exact in exact arithmetic.  Comparing it in ABSOLUTE
    # terms would measure floating point, not algebra: B(t+1) - B(t) is the
    # difference of two nearly equal numbers of size up to delta^2 = 1e3, so
    # at c1 ~ 1e-8 the subtraction discards most of the mantissa while the
    # right-hand side is computed without cancellation.  The scale against
    # which agreement is meaningful is therefore the size of the terms being
    # differenced, not the size of the difference.
    incr_scale = np.maximum(
        (1.0 - c1)[:, None] ** ts[None, :-1] * d2[:, None],
        c2[:, None] * np.maximum(cap[:, 1:], 1.0))
    incr_err = float(np.max(np.abs(pred - diffs) / np.maximum(incr_scale, 1e-300)))

    # ---------------- C2. late branch strictly decreasing
    late = ts[None, :] >= (1.0 / c1)[:, None]
    late_pair = late[:, :-1] & late[:, 1:]
    pos_d2 = d2 > 0
    late_mask = late_pair & pos_d2[:, None]
    # NO INCREASE anywhere on the late branch -- this is the part double
    # precision can represent everywhere.
    late_bad = int((diffs[late_mask] > 0).sum())
    # STRICT decrease is a statement about (1-c1)^t delta^2 > 0, which for
    # large t falls below the double-precision resolution of the floor c5:
    # once the geometric term is smaller than eps*c5 the sum B(t) = geo + c5
    # rounds to c5 exactly and the differenced floats report 0.  That is
    # underflow in the evaluation, not a failure of the statement, so strict
    # decrease is checked only where the geometric term is still resolvable
    # against the floor, and the unresolvable pairs are counted and reported
    # rather than silently dropped.
    geo_late = (1.0 - c1)[:, None] ** ts[None, :-1] * d2[:, None]
    # What must be representable is the DIFFERENCE, not the term: on the late
    # branch B(t) = geo_t + c5, so the step is -c1*geo_t, and the subtraction
    # can only be seen when that is above the rounding granularity of the
    # summands.  A margin of 4 ulps keeps the criterion conservative.
    resolvable = (c1[:, None] * geo_late
                  > 4.0 * np.finfo(float).eps
                  * np.maximum(Bm[:, :-1], 1e-300))
    late_strict_mask = late_mask & resolvable
    late_not_strict = int((diffs[late_strict_mask] >= 0).sum())
    late_underflowed = int((late_mask & ~resolvable).sum())
    # and never equals the floor at finite t, again where representable
    late_eq_floor = int(
        (Bm[:, :-1] <= c5[:, None])[late_strict_mask].sum())

    # ---------------- C3. early-branch iff-criterion
    early_pair = (ts[None, :-1] + 1.0) <= (1.0 / c1)[:, None]
    geo = (1.0 - c1)[:, None] ** ts[None, :-1] * d2[:, None]
    pred_dec = geo > c5[:, None]
    obs_dec = diffs < 0
    # strict equality of the two predicates on the early branch, excluding
    # the measure-zero tie geo == c5 where the increment is exactly 0
    tie = np.isclose(geo, c5[:, None], rtol=1e-12, atol=0.0)
    mask = early_pair & ~tie
    iff_mismatch = int((pred_dec[mask] != obs_dec[mask]).sum())
    iff_checked = int(mask.sum())

    # ---------------- C4. sufficient half on the whole range
    suff_mask = pred_dec & ~tie
    suff_violations = int((diffs[suff_mask] >= 0).sum())
    suff_checked = int(suff_mask.sum())

    # ---------------- D. certified horizon on the late branch when Phi >= e
    has_phi = Phi > 1.0
    t_phi = np.where(has_phi, np.ceil(np.log(np.maximum(Phi, 1.0 + 1e-16))
                                      / c1), np.nan)
    phi_ge_e = has_phi & (Phi >= np.e)
    late_horizon_ok = int((t_phi[phi_ge_e] >= (1.0 / c1)[phi_ge_e]).sum())
    phi_ge_10 = has_phi & (Phi >= 10.0)
    late_horizon_ok10 = int((t_phi[phi_ge_10] >= (1.0 / c1)[phi_ge_10]).sum())
    # the converse edge: below e the horizon may sit on the early branch
    phi_lt_e = has_phi & (Phi < np.e)
    early_horizon_cases = int((t_phi[phi_lt_e] < (1.0 / c1)[phi_lt_e]).sum())

    horizon = {
        "claim": ("t_Phi = ceil(ln(Phi)/c1) >= 1/c1 exactly when ln Phi >= 1, "
                  "i.e. Phi >= e; so under the corollary's Phi >= 10 the "
                  "certified horizon always lies on the LATE branch, where "
                  "the bound is monotone"),
        "n_with_Phi_gt_1": int(has_phi.sum()),
        "n_with_Phi_ge_e": int(phi_ge_e.sum()),
        "n_with_Phi_ge_e_and_t_Phi_ge_1_over_c1": late_horizon_ok,
        "n_with_Phi_ge_10": int(phi_ge_10.sum()),
        "n_with_Phi_ge_10_and_t_Phi_ge_1_over_c1": late_horizon_ok10,
        "n_with_Phi_lt_e": int(phi_lt_e.sum()),
        "n_with_Phi_lt_e_whose_t_Phi_is_on_the_EARLY_branch":
            early_horizon_cases,
        "why_it_matters": ("the withdrawn prose said the bound keeps "
                           "decreasing past t_Phi; that needs t_Phi >= 1/c1, "
                           "which does NOT follow from t_Phi's definition"),
    }

    # ---------------- E. the certified-horizon corollary is unaffected
    use = has_phi & (t_phi <= T) & (d2 > 0) & (c2 > 0)
    tp = t_phi[use].astype(int)
    Bt = bound(tp, c1[use], c2[use], d2[use])
    first = c5[use] * (1.0 + np.log(Phi[use])) + c2[use]
    second = d2[use] * (2.0 + np.log(Phi[use])) / Phi[use]
    corollary = {
        "n_checked": int(use.sum()),
        "n_violations_B_le_first_bound": int((Bt > first * (1 + 1e-12)).sum()),
        "n_violations_first_le_second": int(
            (first > second * (1 + 1e-12)).sum()),
        "worst_relative_slack_B_vs_first": float(
            np.max(Bt / first) if use.any() else 0.0),
        "note": ("the corollary evaluates the VALID bound at one horizon; it "
                 "never invokes monotonicity, so the repaired statement "
                 "leaves it untouched"),
    }
    u10 = use & (Phi >= 10.0)
    if u10.any():
        tp10 = t_phi[u10].astype(int)
        B10 = bound(tp10, c1[u10], c2[u10], d2[u10])
        corollary["n_checked_Phi_ge_10"] = int(u10.sum())
        corollary["n_violations_B_le_0p44_delta2"] = int(
            (B10 > 0.44 * d2[u10] * (1 + 1e-12)).sum())
        corollary["worst_ratio_B_over_delta2_at_Phi_ge_10"] = float(
            np.max(B10 / d2[u10]))
    # the printed constant itself: sup over Phi >= 10 of (2 + ln Phi)/Phi is
    # attained at Phi = 10 because (2 + ln x)/x is decreasing for x > e^{-1}
    grid = np.linspace(10.0, 1e6, 2000001)
    corollary["sup_over_Phi_ge_10_of_(2+lnPhi)_over_Phi"] = float(
        np.max((2.0 + np.log(grid)) / grid))

    # ---------------- F. what Phi <= 1 does and does not give
    # F1.  the refutation of "nondecreasing from t = 0 onward".
    f1 = {"c1": 0.25, "c2": 0.25, "d2": 1.0}
    fb = bound(ts[:7], f1["c1"], f1["c2"], f1["d2"])
    f1.update({
        "phase_ratio_Phi": f1["c1"] * f1["d2"] / f1["c2"],
        "c5_noise_floor": f1["c2"] / f1["c1"],
        "one_over_c1": 1.0 / f1["c1"],
        "B_0_to_6": [float(x) for x in fb],
        "B4": float(fb[4]), "B5": float(fb[5]),
        "DECREASES_at_t4": bool(fb[5] < fb[4]),
        "increment_B5_minus_B4": float(fb[5] - fb[4]),
        "min_over_grid_is_at_t0": bool(float(fb.min()) >= f1["d2"] - 1e-15),
    })
    # realized by admissible constants: L=mu=alpha=c_g=C_g=1 => eta_max=1;
    # eta=0.25 gives c1=0.25, and c2 = L eta^2 sigtot^2/2 = 0.25 needs
    # sigtot^2 = 8.
    f1w = {"L": 1.0, "mu": 1.0, "alpha": 1.0, "c_g": 1.0, "C_g": 1.0,
           "eta": 0.25, "sigtot": float(np.sqrt(8.0)), "d2": 1.0}
    f1w["eta_max"] = f1w["alpha"] * f1w["c_g"] / (f1w["L"] * f1w["C_g"] ** 2)
    f1w["step_condition_holds"] = bool(0 < f1w["eta"] <= f1w["eta_max"])
    f1w["c1"] = f1w["eta"] * f1w["mu"] * f1w["alpha"] * f1w["c_g"]
    f1w["c2"] = f1w["L"] * f1w["eta"] ** 2 * f1w["sigtot"] ** 2 / 2.0
    f1w["Phi"] = f1w["c1"] * f1w["d2"] / f1w["c2"]
    f1w["reproduces_the_refutation"] = bool(
        f1w["Phi"] <= 1.0
        and bound(5, f1w["c1"], f1w["c2"], f1w["d2"])
        < bound(4, f1w["c1"], f1w["c2"], f1w["d2"]))

    # the same refutation over the admissible draws
    lowphi = Phi <= 1.0
    n_lowphi = int(lowphi.sum())
    lowphi_increase = int((diffs[lowphi] > 0).sum())
    lowphi_decrease_somewhere = int((diffs[lowphi] < -1e-15).any(axis=1).sum())

    # F2.  the early branch is nondecreasing under Phi <= 1
    early_low = early_pair & lowphi[:, None]
    f2_violations = int((diffs[early_low] < -1e-12
                         * np.maximum(np.abs(Bm[:, :-1][early_low]), 1.0)).sum())

    # F3.  the surviving global statement B(t) >= B(0) = delta^2
    # (integer step counts only; the real-t dip on (0,1) is exhibited below)
    slack = Bm[lowphi] - d2[lowphi][:, None]
    f3_violations = int(
        (slack < -1e-12 * np.maximum(d2[lowphi][:, None], 1.0)).sum())
    f3_worst = float(slack.min()) if n_lowphi else 0.0
    # and the real-t dip that makes "integer step counts" load-bearing:
    # at c1 = 0.25, c2 = 0.25, delta^2 = 1 the displayed expression at
    # t = 0.5 is below delta^2, which is why Bernoulli (t >= 1) is invoked.
    real_t = np.linspace(0.0, 1.0, 10001)
    real_B = bound(real_t, f1["c1"], f1["c2"], f1["d2"])
    f3_real_dip = float(real_B.min() - f1["d2"])

    phi_le_one = {
        "withdrawn_claim": ("at Phi <= 1 the bound is nondecreasing from "
                            "t = 0 onward"),
        "F1_refutation": f1,
        "F1_admissible_constants_witness": f1w,
        "F1_n_admissible_draws_with_Phi_le_1": n_lowphi,
        "F1_n_increasing_steps_among_them": lowphi_increase,
        "F1_n_draws_with_a_strictly_DECREASING_step": lowphi_decrease_somewhere,
        "F2_early_branch_nondecreasing_violations": f2_violations,
        "F2_n_early_pairs_checked": int(early_low.sum()),
        "F3_surviving_claim": ("B(t) >= B(0) = delta^2 at every integer "
                               "0 <= t <= T, so t = 0 minimizes the "
                               "displayed envelope"),
        "F3_n_violations": f3_violations,
        "F3_worst_signed_slack_B_minus_delta2": f3_worst,
        "F3_real_t_dip_below_delta2_on_the_unit_interval": f3_real_dip,
        "F3_note": ("the real-t dip is why F3 is stated at integer step "
                    "counts: Bernoulli's (1-c1)^t >= 1 - c1 t needs t >= 1, "
                    "and t indexes iterates"),
    }

    out = {
        "script": "f33_pl_envelope_monotonicity.py",
        "kind": "closed-form audit of the envelope's algebra; nothing simulated",
        "finding": ("the displayed local-PL bound is valid but NOT globally "
                    "nonincreasing on 0 <= t <= T; the early branch "
                    "(1-c1)^t delta^2 + c2 t can increase because the linear "
                    "noise accumulation outruns the geometric decay.  The "
                    "correct statements are: strict decrease on the late "
                    "branch t >= 1/c1, and, on the early branch, strict "
                    "decrease at step t IF AND ONLY IF (1-c1)^t delta^2 > c5"),
        "A_displayed_bound_relaxes_the_recursion": relaxation,
        "B_refutation": {
            "worked_counterexample_delta2_11": ce1,
            "worked_counterexample_delta2_0p1": ce2,
            "admissible_constants_witness": wit,
            "random_search": search,
        },
        "C_corrected_statement": {
            "C1_increment_identity_max_relative_error": incr_err,
            "C2_late_branch": {
                "n_late_pairs_checked": int(late_mask.sum()),
                "n_increasing_steps": late_bad,
                "n_pairs_with_resolvable_geometric_term":
                    int(late_strict_mask.sum()),
                "n_resolvable_pairs_not_strictly_decreasing": late_not_strict,
                "n_pairs_where_geometric_term_underflows_the_floor":
                    late_underflowed,
                "n_times_bound_reaches_or_crosses_floor_when_resolvable":
                    late_eq_floor,
            },
            "C3_early_branch_iff": {
                "criterion": "(1-c1)^t delta^2 > c5  <=>  B(t+1) < B(t)",
                "equivalently": "t < ln(Phi)/ln(1/(1-c1)),  Phi = c1 delta^2/c2",
                "n_pairs_checked": iff_checked,
                "n_mismatches": iff_mismatch,
            },
            "C4_sufficient_half_on_whole_range": {
                "n_checked": suff_checked,
                "n_violations": suff_violations,
            },
        },
        "D_certified_horizon_branch": horizon,
        "E_corollary_unaffected": corollary,
        "F_what_Phi_le_1_gives": phi_le_one,
    }

    # ---------------- assertions
    assert relaxation["n_violations"] == 0, (
        "the displayed bound does NOT over-estimate the exact geometric "
        "accumulation -- the printed inequality would itself be wrong")
    assert ce1["decreases_at_t0"] and ce1["INCREASES_at_t1"], (
        "the worked counterexample does not reproduce")
    assert ce2["INCREASES_at_t0"], (
        "the small-initial-error counterexample does not reproduce")
    assert wit["step_condition_holds"] and wit["c1_in_open_unit_interval"] \
        and wit["INCREASES_at_t1"], (
        "the counterexample is not realized by admissible A1-A3 constants "
        "under the step cap, so the refutation would not bind")
    assert search["n_with_a_strictly_increasing_step"] > 0, (
        "no admissible draw refutes global monotonicity -- if this fires the "
        "claim may be true on the admissible region after all")
    assert incr_err < 1e-12, "the increment identity is wrong"
    assert late_bad == 0, "the late branch increases somewhere"
    assert late_not_strict == 0, (
        "the late branch is not strictly decreasing where the geometric term "
        "is still resolvable against the floor")
    assert late_eq_floor == 0, "the bound attains its floor at a finite t"
    assert iff_mismatch == 0, "the early-branch iff-criterion fails"
    assert suff_violations == 0, "the sufficient criterion fails"
    assert late_horizon_ok == int(phi_ge_e.sum()), (
        "Phi >= e does not put the certified horizon on the late branch")
    assert late_horizon_ok10 == int(phi_ge_10.sum()), (
        "the corollary's Phi >= 10 does not put t_Phi on the late branch")
    assert corollary["n_violations_B_le_first_bound"] == 0, (
        "the certified-horizon corollary's first inequality fails")
    assert corollary["n_violations_first_le_second"] == 0, (
        "the certified-horizon corollary's second inequality fails")
    assert corollary.get("n_violations_B_le_0p44_delta2", 0) == 0, (
        "the corollary's 0.44 delta^2 conclusion fails at Phi >= 10")
    assert corollary["sup_over_Phi_ge_10_of_(2+lnPhi)_over_Phi"] < 0.44, (
        "the printed constant 0.44 is not an upper bound for Phi >= 10")
    assert f1["phase_ratio_Phi"] <= 1.0 and f1["DECREASES_at_t4"], (
        "the Phi <= 1 counterexample does not reproduce, so 'nondecreasing "
        "from t = 0 onward' would not be refuted")
    assert f1w["step_condition_holds"] and f1w["reproduces_the_refutation"], (
        "the Phi <= 1 counterexample is not realized by admissible "
        "constants under the step cap")
    assert lowphi_decrease_somewhere > 0, (
        "no admissible draw with Phi <= 1 has a decreasing step -- if this "
        "fires, the withdrawn claim may hold on the admissible region")
    assert f2_violations == 0, (
        "the early branch is NOT nondecreasing under Phi <= 1, so the "
        "surviving early-branch half of (ii) is wrong too")
    assert f3_violations == 0, (
        "B(t) < delta^2 at some integer t with Phi <= 1: the surviving "
        "global-minimum-at-0 conclusion would be wrong")
    assert f3_real_dip < 0.0, (
        "the real-t dip below delta^2 does not occur, so stating F3 at "
        "integer step counts would be an unnecessary restriction")

    C.save(out, "f33_pl_envelope_monotonicity.json")

    print(f"[f33] 1/5 the displayed bound is a VALID relaxation: "
          f"S_t <= min(t,1/c1) at all "
          f"{relaxation['n_c1_values']}x{relaxation['n_t_values']} grid "
          f"points, 0 violations.")
    print(f"[f33] 2/5 global monotonicity REFUTED: at c1=0.1, c2=1, "
          f"delta^2=11 the bound goes {ce1['B0']:.4g} -> {ce1['B1']:.4g} -> "
          f"{ce1['B2']:.4g} (up by {ce1['increment_B2_minus_B1']:.3g} at "
          f"t=1); at delta^2=0.1 it goes {ce2['B0']:.4g} -> {ce2['B1']:.4g} "
          f"immediately.  Both are realized by admissible constants "
          f"(L=mu=alpha=c_g=C_g=1, eta=0.1 <= eta_max="
          f"{wit['eta_max']:.3g}, sigtot^2=200).  Over "
          f"{search['n_admissible_draws']} admissible draws, "
          f"{search['n_with_a_strictly_increasing_step']} "
          f"({search['fraction_with_a_strictly_increasing_step']*100:.1f}%) "
          f"have a strictly increasing step within t <= {T}.")
    print(f"[f33] 3/5 corrected statement certified: increment identity to "
          f"{incr_err:.1e}; late branch strictly decreasing on "
          f"{int(late_mask.sum())} "
          f"pairs with 0 increases ({int(late_strict_mask.sum())} strictly "
          f"decreasing where the geometric term is resolvable against the "
          f"floor, {late_underflowed} underflowing it) and never attaining "
          f"c5; the early-branch "
          f"iff-criterion (1-c1)^t delta^2 > c5 matches the observed sign on "
          f"{iff_checked} pairs with {iff_mismatch} mismatches.")
    print(f"[f33] 4/5 the certified-horizon corollary is UNAFFECTED: "
          f"Phi >= e puts t_Phi on the late branch in "
          f"{late_horizon_ok}/{int(phi_ge_e.sum())} cases (and "
          f"{late_horizon_ok10}/{int(phi_ge_10.sum())} at the corollary's "
          f"Phi >= 10), while {early_horizon_cases} draws with Phi < e put it "
          f"on the EARLY branch -- which is exactly why the withdrawn "
          f"'keeps decreasing past t_Phi' does not follow.  Both corollary "
          f"inequalities hold on {corollary['n_checked']} draws with 0 "
          f"violations, and sup_{{Phi>=10}} (2+lnPhi)/Phi = "
          f"{corollary['sup_over_Phi_ge_10_of_(2+lnPhi)_over_Phi']:.4f} "
          f"< 0.44.")
    print(f"[f33] 5/5 Phi <= 1 does NOT give global monotonicity: at "
          f"c1=c2=0.25, delta^2=1 (Phi=1, admissible with eta=0.25, "
          f"sigtot^2=8) the bound goes B(4)={f1['B4']:.9g} -> "
          f"B(5)={f1['B5']:.9g}, and {lowphi_decrease_somewhere} of "
          f"{n_lowphi} admissible draws with Phi<=1 have a decreasing step.  "
          f"What survives, certified here: the early branch is nondecreasing "
          f"({f2_violations} violations over {int(early_low.sum())} pairs) "
          f"and B(t) >= delta^2 = B(0) at every integer t "
          f"({f3_violations} violations, worst signed slack "
          f"{f3_worst:.3e}), while on the REAL unit interval the same "
          f"expression dips {f3_real_dip:.4g} below delta^2 -- which is why "
          f"the surviving statement is made at integer step counts.")
    print("[f33] DONE", flush=True)


if __name__ == "__main__":
    main()
