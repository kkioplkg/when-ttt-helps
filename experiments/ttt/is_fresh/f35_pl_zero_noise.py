"""F35 -- the local-PL envelope at ZERO NOISE: what is defined, what is not.

WHY THIS SCRIPT EXISTS
----------------------
A3 bounds the gradient-noise second moment by sigtot^2 and permits
sigtot = 0.  Three statements of the local-PL section behaved badly there
and this script certifies each defect and each repair.

The constants are c1 = eta mu alpha c_g in (0,1], c2 = L eta^2 sigtot^2/2,
the noise floor c5 = c2/c1, the phase ratio Phi = c1 delta^2/c2, and the
displayed envelope

    B(t) = (1 - c1)^t delta^2 + c2 min{t, 1/c1}   >=   E Exc(theta_t).

DEFECT A -- THE ENVELOPE'S CLAUSES (ii)-(iii) ARE NOT DEFINED AT sigtot=0.
    Those clauses are written in terms of Phi = c1 delta^2/c2, which is
    formally introduced only in the certified-horizon corollary, under the
    ADDITIONAL hypothesis sigtot > 0.  At sigtot = 0 one has c2 = 0, so
    Phi has a zero denominator and ln Phi is not a real number, while the
    clauses containing them carry no local hypothesis excluding that case.
    An admissible instance realizing it is exhibited: R(theta) =
    theta^2/2, g(theta, xi) = theta (no stochastic noise), Theta_loc = R,
    L = mu = alpha = c_g = C_g = 1, eta = 1/2, theta_0 = sqrt(2).  A1-A4
    all hold and delta^2 = 1, c1 = 1/2, c2 = c5 = 0.

DEFECT B -- c5 IS NOT UNDEFINED AT sigtot = 0.  The corollary's boundary
    paragraph said c2, Phi, c5 and ln Phi are ALL undefined there.  That is
    wrong for c5: c1 > 0 always (it is eta mu alpha c_g with every factor
    positive), so c5 = c2/c1 = 0/c1 = 0 is a perfectly defined noise floor
    that happens to vanish.  What genuinely leaves the definitions is the
    RATIO Phi and its logarithm.

DEFECT C -- THE ZERO-NOISE REMARK'S STRICT INEQUALITY IS FALSE.  It said
    the envelope is BELOW a target epsilon at every integer t with
        t >= ln(delta^2/epsilon) / ln(1/(1-c1)).
    The displayed threshold yields (1-c1)^t delta^2 <= epsilon and not
    < epsilon.  Counterexample: c1 = 1/2, delta^2 = 1, epsilon = 1/2,
    t = 1.  The threshold is exactly 1, t = 1 meets it, and the bound
    equals epsilon.

WHAT IS CHECKED
  A. ZERO NOISE IS ADMISSIBLE, AND THE Phi-CLAUSES ARE NOT DEFINED THERE.
     A1. The exhibited quadratic instance is checked against A1-A4 and the
         step cap directly, from the definitions and not by assertion:
         L-Lipschitz gradient, the PL inequality, the alignment and
         relative-scale bounds of A2, the A3 noise bound with sigtot = 0,
         and eta <= eta_max.
     A2. Its constants give c2 = c5 = 0 and a zero-denominator Phi.
  B. c5 IS DEFINED AND EQUALS ZERO, over an admissible random search
     restricted to sigtot = 0: c1 > 0 at every draw, c5 = 0 at every draw.
  C. RESTRICTING (ii)-(iii) TO sigtot > 0 LOSES NOTHING.  At sigtot = 0
     with delta^2 > 0:
     C1. the early-branch criterion (1-c1)^t delta^2 > c5 holds at EVERY
         t, so B strictly decreases at every early-branch step -- which is
         what the zero-noise remark already says, in its own words;
     C2. the hypothesis Phi <= 1 of clause (iii) is equivalent to
         delta^2 <= c5 = 0, which delta^2 > 0 excludes, so clause (iii)
         has no zero-noise instance to lose;
     C3. the whole envelope collapses to B(t) = (1-c1)^t delta^2, checked
         against the general formula over a dense grid.
  D. THE STRICT-INEQUALITY DEFECT AND ITS REPAIR.
     D1. The counterexample above is reproduced exactly, and realized by
         admissible constants (eta = 1/2 with L = mu = alpha = c_g = C_g
         = 1 gives c1 = 1/2 under eta_max = 1).
     D2. THE REPAIRED NON-STRICT FORM, over an admissible random search:
         t >= ln(delta^2/epsilon)/ln(1/(1-c1))  =>  B(t) <= epsilon,
         with zero violations.
     D3. THE STRICT FORM UNDER A STRICT THRESHOLD:
         t >  ln(delta^2/epsilon)/ln(1/(1-c1))  =>  B(t) <  epsilon,
         with zero violations.  Both candidate repairs are therefore
         sound and either may be taken; the manuscript takes D2.
     D4. The equality case is not a measure-zero curiosity that only the
         worked instance reaches: the search counts how many admissible
         draws admit an integer t meeting the non-strict threshold with
         equality.
  E. THE c1 = 1 ENDPOINT, which the step cap permits (mu = L is admissible
     under A1).  There (1-c1)^t delta^2 = 0 for every t >= 1, so the bound
     is 0 <= epsilon at every t >= 1 for every epsilon > 0, and the
     remark's separate c1 = 1 sentence is checked to be the correct one.

Nothing is simulated and no record is read: this is a closed-form audit of
the envelope's own algebra at the boundary its assumptions permit.

Usage: python f35_pl_zero_noise.py
Writes experiments/results/is_fresh/f35_pl_zero_noise.json
"""
from __future__ import annotations

import argparse

import numpy as np

import common as C

SEED = 20260808


# ------------------------------------------------------------------ the bound

def bound(t, c1, c2, d2):
    """The displayed envelope B(t) = (1-c1)^t d2 + c2 min{t, 1/c1}."""
    t = np.asarray(t, dtype=float)
    return (1.0 - c1) ** t * d2 + c2 * np.minimum(t, 1.0 / c1)


# ------------------------------------------------- the admissible zero-noise
#                                                    instance, checked directly

def quadratic_instance():
    """R(theta) = theta^2/2 on R, g(theta, xi) = theta, no noise.

    A1-A4 are verified from their definitions rather than asserted: the
    point of the instance is that the theorem's hypotheses genuinely admit
    sigtot = 0, so the verification must not itself assume it.
    """
    L = mu = alpha = c_g = C_g = 1.0
    eta = 0.5
    sigtot = 0.0
    th0 = np.sqrt(2.0)

    grid = np.linspace(-50.0, 50.0, 2000001)
    R = 0.5 * grid ** 2
    gradR = grid                       # R'(theta) = theta
    gbar = grid                        # E_xi g(theta, xi) = theta
    Rstar = 0.0                        # inf over Theta_loc = R
    Exc = R - Rstar

    # A1 smoothness: |R'(a) - R'(b)| = |a - b| <= L|a - b|, with equality.
    lip = float(np.max(np.abs(np.diff(gradR)) / np.diff(grid)))
    # A1 PL: |R'|^2 = theta^2 >= 2 mu (R - R*) = theta^2.
    pl_slack = float(np.min(gradR ** 2 - 2.0 * mu * Exc))
    # A2 alignment: <gbar, gradR> = theta^2 = alpha |gbar||gradR|.
    align_slack = float(np.min(gbar * gradR
                               - alpha * np.abs(gbar) * np.abs(gradR)))
    # A2 relative scale: c_g|gradR| <= |gbar| <= C_g|gradR|, both equalities.
    lo_slack = float(np.min(np.abs(gbar) - c_g * np.abs(gradR)))
    hi_slack = float(np.min(C_g * np.abs(gradR) - np.abs(gbar)))
    # A3: g is deterministic given theta, so the noise second moment is 0.
    a3_slack = float(sigtot ** 2 - 0.0)
    # A4: theta_{t+1} = theta_t - eta theta_t = (1-eta) theta_t stays in R.
    eta_max = alpha * c_g / (L * C_g ** 2)

    d2 = float(0.5 * th0 ** 2 - Rstar)
    c1 = eta * mu * alpha * c_g
    c2 = L * eta ** 2 * sigtot ** 2 / 2.0

    inst = {
        "R": "theta^2/2 on Theta_loc = R", "g": "g(theta, xi) = theta",
        "L": L, "mu": mu, "alpha": alpha, "c_g": c_g, "C_g": C_g,
        "eta": eta, "eta_max": eta_max, "sigtot": sigtot, "theta_0": float(th0),
        "A1_measured_gradient_Lipschitz_constant": lip,
        "A1_holds": bool(lip <= L * (1.0 + 1e-12)),
        "A1_PL_worst_slack": pl_slack, "A1_PL_holds": bool(pl_slack >= -1e-9),
        "A2_alignment_worst_slack": align_slack,
        "A2_relative_scale_worst_slacks": [lo_slack, hi_slack],
        "A2_holds": bool(min(align_slack, lo_slack, hi_slack) >= -1e-9),
        "A3_slack_sigtot2_minus_noise": a3_slack, "A3_holds": True,
        "A4_holds": True,
        "A4_why": ("theta_{t+1} = (1-eta) theta_t and Theta_loc = R, so the "
                   "whole path is contained by construction"),
        "step_condition_holds": bool(0 < eta <= eta_max),
        "delta2": d2, "c1": c1, "c2": c2,
        "c5_noise_floor": c2 / c1,
        "Phi_denominator_c2": c2,
        "Phi_is_a_real_number": bool(c2 > 0),
    }
    return inst


# ----------------------------------------------------- admissible sampling

def draw_admissible(rng, n, zero_noise=False):
    """Draw n tuples satisfying A1-A3 and the step cap eta <= eta_max.

    Identical in form to the admissible sampler of f33, with an option to
    pin sigtot = 0 -- the case A3 permits and the defective clauses did not
    exclude.
    """
    L = 10.0 ** rng.uniform(-2.0, 2.0, n)
    mu = L * rng.uniform(1e-3, 1.0, n)
    alpha = rng.uniform(1e-3, 1.0, n)
    c_g = 10.0 ** rng.uniform(-2.0, 1.0, n)
    C_g = c_g * (1.0 + 10.0 ** rng.uniform(-3.0, 1.0, n))
    sigtot = (np.zeros(n) if zero_noise
              else 10.0 ** rng.uniform(-3.0, 2.0, n))
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

    # ---------------- A. zero noise is admissible; the Phi-clauses are not
    inst = quadratic_instance()

    # ---------------- B. c5 is defined and equals zero at sigtot = 0
    Z = draw_admissible(rng, args.draws, zero_noise=True)
    z_c1, z_c2, z_d2 = Z["c1"], Z["c2"], Z["d2"]
    zok = (z_c1 > 0) & (z_c1 < 1)
    z_c1, z_c2, z_d2 = z_c1[zok], z_c2[zok], z_d2[zok]
    nz = int(z_c1.size)
    z_c5 = z_c2 / z_c1
    c5_defined = {
        "claim": ("at sigtot = 0 one has c2 = 0 and c1 > 0, so the noise "
                  "floor c5 = c2/c1 = 0 is DEFINED; only the ratio "
                  "Phi = c1 delta^2/c2 and its logarithm leave the "
                  "definitions"),
        "n_zero_noise_draws": nz,
        "n_with_c1_strictly_positive": int((z_c1 > 0).sum()),
        "n_with_c2_exactly_zero": int((z_c2 == 0.0).sum()),
        "n_with_c5_exactly_zero": int((z_c5 == 0.0).sum()),
        "n_with_c5_not_finite": int((~np.isfinite(z_c5)).sum()),
        "n_with_Phi_denominator_zero": int((z_c2 == 0.0).sum()),
    }

    # ---------------- C. restricting (ii)-(iii) to sigtot > 0 loses nothing
    geo0 = (1.0 - z_c1)[:, None] ** ts[None, :-1] * z_d2[:, None]
    pos = z_d2 > 0
    # C1: the early-branch decrease criterion holds at EVERY t when d2 > 0
    c1_crit_fail = int((geo0[pos] <= z_c5[pos][:, None]).sum())
    # and the bound really does strictly decrease there
    B0 = ((1.0 - z_c1)[:, None] ** ts[None, :] * z_d2[:, None]
          + z_c2[:, None] * np.minimum(ts[None, :].astype(float),
                                       (1.0 / z_c1)[:, None]))
    d0 = np.diff(B0, axis=1)
    # strict decrease is checkable only while the geometric term is above the
    # double-precision granularity of the value it sits in; below that the
    # differenced floats report 0, which is underflow and not a counterexample
    resolvable = (z_c1[:, None] * geo0
                  > 4.0 * np.finfo(float).eps
                  * np.maximum(B0[:, :-1], 1e-300))
    dec_mask = resolvable & pos[:, None]
    c1_not_strict = int((d0[dec_mask] >= 0).sum())
    # C2: Phi <= 1 is delta^2 <= c5 = 0, excluded by delta^2 > 0
    c2_instances = int((z_d2[pos] <= z_c5[pos]).sum())
    # C3: the envelope collapses to the pure geometric decay
    collapse_err = float(np.max(np.abs(
        B0[pos] - (1.0 - z_c1[pos])[:, None] ** ts[None, :]
        * z_d2[pos][:, None])))
    restriction = {
        "claim": ("clauses (ii)-(iii) may be restricted to sigtot > 0 "
                  "without losing a single zero-noise instance: at "
                  "sigtot = 0 with delta^2 > 0 the early-branch criterion "
                  "holds at every t (so (ii)'s content is the strict "
                  "decrease the zero-noise remark already states) and (iii)'s "
                  "hypothesis Phi <= 1 is unsatisfiable"),
        "C1_n_early_criterion_failures": c1_crit_fail,
        "C1_n_resolvable_pairs_checked": int(dec_mask.sum()),
        "C1_n_resolvable_pairs_not_strictly_decreasing": c1_not_strict,
        "C2_n_draws_satisfying_Phi_le_1_i_e_delta2_le_c5": c2_instances,
        "C3_max_abs_difference_from_pure_geometric_decay": collapse_err,
    }

    # ---------------- D. the strict-inequality defect and its repair
    d1 = {"c1": 0.5, "delta2": 1.0, "epsilon": 0.5, "t": 1}
    d1["threshold"] = float(np.log(d1["delta2"] / d1["epsilon"])
                            / np.log(1.0 / (1.0 - d1["c1"])))
    d1["t_meets_printed_threshold"] = bool(d1["t"] >= d1["threshold"])
    d1["bound_at_t"] = float(bound(d1["t"], d1["c1"], 0.0, d1["delta2"]))
    d1["bound_is_BELOW_epsilon"] = bool(d1["bound_at_t"] < d1["epsilon"])
    d1["bound_is_AT_MOST_epsilon"] = bool(d1["bound_at_t"] <= d1["epsilon"])
    d1["bound_equals_epsilon"] = bool(d1["bound_at_t"] == d1["epsilon"])
    # realized by admissible constants: L = mu = alpha = c_g = C_g = 1 gives
    # eta_max = 1, and eta = 1/2 gives c1 = 1/2 with sigtot = 0.
    d1w = {"L": 1.0, "mu": 1.0, "alpha": 1.0, "c_g": 1.0, "C_g": 1.0,
           "eta": 0.5, "sigtot": 0.0, "delta2": 1.0}
    d1w["eta_max"] = d1w["alpha"] * d1w["c_g"] / (d1w["L"] * d1w["C_g"] ** 2)
    d1w["step_condition_holds"] = bool(0 < d1w["eta"] <= d1w["eta_max"])
    d1w["c1"] = d1w["eta"] * d1w["mu"] * d1w["alpha"] * d1w["c_g"]
    d1w["reproduces_the_counterexample"] = bool(d1w["c1"] == d1["c1"])

    # D2/D3/D4: the two repairs over the admissible zero-noise draws
    use = pos & (z_c1 < 1.0)
    uc1, ud2 = z_c1[use], z_d2[use]
    # a target strictly inside (0, delta^2), drawn per tuple
    frac = rng.uniform(1e-6, 1.0 - 1e-6, uc1.size)
    eps = ud2 * frac
    thr = np.log(ud2 / eps) / np.log(1.0 / (1.0 - uc1))
    tgrid = ts[None, :].astype(float)
    Bg = (1.0 - uc1)[:, None] ** tgrid * ud2[:, None]
    meets_nonstrict = tgrid >= thr[:, None]
    meets_strict = tgrid > thr[:, None] * (1.0 + 1e-12)
    # a relative tolerance: the comparison is between two floats each formed
    # by a power and a product, so exact `<=' would measure rounding
    tol = 1e-12 * np.maximum(eps, 1e-300)
    hi = np.broadcast_to((eps + tol)[:, None], Bg.shape)
    lo = np.broadcast_to((eps - tol)[:, None], Bg.shape)
    d2_viol = int((Bg[meets_nonstrict] > hi[meets_nonstrict]).sum())
    d3_viol = int((Bg[meets_strict] >= lo[meets_strict]).sum())
    # D4: THE EQUALITY CASE IS REACHABLE AT EVERY ADMISSIBLE DRAW, not only
    # at the worked instance.  Randomly drawn targets never land on an
    # integer's bound value, so the equality case must be CONSTRUCTED rather
    # than sampled: for each draw take an integer t and set the target to the
    # bound's own value there, eps := (1-c1)^t delta^2, which lies strictly
    # inside (0, delta^2) whenever 0 < c1 < 1 and t >= 1.  The printed
    # threshold is then exactly t, the printed condition is met, and the bound
    # is AT eps rather than below it.
    eq_t = 1 + (np.arange(uc1.size) % 5)
    eq_eps = (1.0 - uc1) ** eq_t * ud2
    eq_inside = (eq_eps > 0.0) & (eq_eps < ud2)
    eq_thr = np.log(ud2 / eq_eps) / np.log(1.0 / (1.0 - uc1))
    # The printed threshold is the log transform of the primitive condition
    # (1-c1)^t delta^2 <= eps, which the construction satisfies with exact
    # equality in floating point.  The transform itself is not exact -- both
    # logarithms lose digits as c1 -> 0 -- so the comparison carries a
    # tolerance and the observed transform error is reported beside it rather
    # than hidden inside the predicate.
    eq_thr_gap = float(np.max(np.abs(eq_thr - eq_t)))
    eq_meets = eq_t >= eq_thr - 1e-4 * np.maximum(1.0, eq_thr)
    eq_B = (1.0 - uc1) ** eq_t * ud2
    eq_not_below = eq_B >= eq_eps * (1.0 - 1e-12)
    eq_at_most = eq_B <= eq_eps * (1.0 + 1e-12)
    repair = {
        "D1_counterexample": d1,
        "D1_admissible_constants_witness": d1w,
        "D2_claim": ("t >= ln(delta^2/eps)/ln(1/(1-c1))  =>  B(t) <= eps"),
        "D2_n_pairs_checked": int(meets_nonstrict.sum()),
        "D2_n_violations": d2_viol,
        "D3_claim": ("t >  ln(delta^2/eps)/ln(1/(1-c1))  =>  B(t) <  eps"),
        "D3_n_pairs_checked": int(meets_strict.sum()),
        "D3_n_violations": d3_viol,
        "D4_construction": ("eps := (1-c1)^t delta^2 at an integer "
                            "t in {1,...,5}, so the printed threshold is "
                            "exactly t"),
        "D4_n_draws_constructed": int(eq_inside.sum()),
        "D4_max_abs_log_transform_error_threshold_minus_t": eq_thr_gap,
        "D4_n_meeting_the_printed_threshold": int((eq_meets & eq_inside).sum()),
        "D4_n_where_the_bound_is_NOT_below_eps":
            int((eq_not_below & eq_meets & eq_inside).sum()),
        "D4_n_where_the_bound_is_at_most_eps":
            int((eq_at_most & eq_meets & eq_inside).sum()),
        "D4_note": ("the equality case is reachable at EVERY admissible "
                    "draw, so the false strict wording is not confined to "
                    "the worked instance; the repaired 'at most' holds at "
                    "all of them"),
    }

    # ---------------- E. the c1 = 1 endpoint, which the step cap permits
    e_c1, e_d2 = 1.0, 3.0
    e_vals = [float(bound(t, e_c1, 0.0, e_d2)) for t in range(0, 5)]
    endpoint = {
        "c1": e_c1, "delta2": e_d2,
        "B_0_to_4": e_vals,
        "zero_from_t_ge_1": bool(all(v == 0.0 for v in e_vals[1:])),
        "why_admissible": ("c1 = eta mu alpha c_g reaches 1 when mu = L and "
                           "alpha = c_g = C_g = 1 with eta = eta_max = 1, "
                           "which A1 and the step cap both permit"),
        "remark_clause": ("at c1 = 1 the bound is 0 <= epsilon at every "
                          "t >= 1 for every epsilon > 0, which is the "
                          "separate sentence the zero-noise remark already "
                          "carries and which needs no threshold at all"),
    }

    out = {
        "script": "f35_pl_zero_noise.py",
        "kind": ("closed-form audit of the local-PL envelope at sigtot = 0; "
                 "nothing simulated, no record read"),
        "finding": ("A3 permits sigtot = 0; there c2 = c5 = 0 and the phase "
                    "ratio Phi = c1 delta^2/c2 has a zero denominator.  The "
                    "envelope's Phi-dependent clauses therefore need a local "
                    "positive-noise hypothesis (they lose no instance by "
                    "getting one), the corollary's boundary paragraph was "
                    "wrong to call c5 undefined, and the zero-noise remark's "
                    "'below epsilon' is false at the threshold and must read "
                    "'at most epsilon'"),
        "A_zero_noise_is_admissible": inst,
        "B_c5_is_defined_and_zero": c5_defined,
        "C_restricting_to_positive_noise_loses_nothing": restriction,
        "D_strict_inequality_defect_and_repair": repair,
        "E_c1_equals_one_endpoint": endpoint,
    }

    # ---------------- assertions
    assert inst["A1_holds"] and inst["A1_PL_holds"] and inst["A2_holds"] \
        and inst["A3_holds"] and inst["A4_holds"] \
        and inst["step_condition_holds"], (
        "the exhibited zero-noise instance does not satisfy A1-A4 and the "
        "step cap, so it would not witness that the clauses admit sigtot = 0")
    assert inst["c2"] == 0.0 and inst["c5_noise_floor"] == 0.0, (
        "the exhibited instance does not have c2 = c5 = 0")
    assert not inst["Phi_is_a_real_number"], (
        "the exhibited instance has a nonzero Phi denominator, so it would "
        "not witness the defect")
    assert c5_defined["n_with_c1_strictly_positive"] == nz, (
        "c1 is not strictly positive at every admissible draw -- c5 = c2/c1 "
        "would then genuinely be undefined somewhere")
    assert c5_defined["n_with_c5_exactly_zero"] == nz, (
        "c5 is not identically zero at sigtot = 0")
    assert c5_defined["n_with_c5_not_finite"] == 0, (
        "c5 is not finite somewhere at sigtot = 0, contradicting the repair")
    assert restriction["C1_n_early_criterion_failures"] == 0, (
        "the early-branch decrease criterion fails somewhere at sigtot = 0 "
        "with delta^2 > 0, so restricting clause (ii) would lose an instance")
    assert restriction["C1_n_resolvable_pairs_not_strictly_decreasing"] == 0, (
        "the zero-noise envelope does not strictly decrease where the "
        "geometric term is resolvable")
    assert restriction[
        "C2_n_draws_satisfying_Phi_le_1_i_e_delta2_le_c5"] == 0, (
        "clause (iii)'s hypothesis IS satisfiable at sigtot = 0, so "
        "restricting it to positive noise would lose an instance")
    assert restriction[
        "C3_max_abs_difference_from_pure_geometric_decay"] == 0.0, (
        "the zero-noise envelope is not exactly (1-c1)^t delta^2")
    assert d1["t_meets_printed_threshold"], (
        "the counterexample does not meet the printed threshold, so it would "
        "not refute the printed strict wording")
    assert d1["bound_equals_epsilon"] and not d1["bound_is_BELOW_epsilon"] \
        and d1["bound_is_AT_MOST_epsilon"], (
        "the counterexample does not put the bound exactly at epsilon")
    assert d1w["step_condition_holds"] and d1w["reproduces_the_counterexample"], (
        "the counterexample is not realized by admissible constants under "
        "the step cap, so the refutation would not bind")
    assert repair["D2_n_violations"] == 0, (
        "the repaired non-strict form fails: B(t) > epsilon somewhere above "
        "the threshold")
    assert repair["D3_n_violations"] == 0, (
        "the strict form under a strict threshold fails")
    assert repair["D4_n_where_the_bound_is_NOT_below_eps"] \
        == repair["D4_n_draws_constructed"] > 0, (
        "the constructed equality case does not reproduce at every "
        "admissible draw -- if this fires the strict wording would be false "
        "only at isolated points")
    assert repair["D4_n_where_the_bound_is_at_most_eps"] \
        == repair["D4_n_draws_constructed"], (
        "the repaired 'at most epsilon' fails on the equality construction, "
        "which is the case the repair exists for")
    assert endpoint["zero_from_t_ge_1"], (
        "the c1 = 1 endpoint does not collapse the bound to zero from t = 1")

    C.save(out, "f35_pl_zero_noise.json")

    print(f"[f35] 1/4 ZERO NOISE IS ADMISSIBLE: R(theta)=theta^2/2, "
          f"g(theta,xi)=theta, L=mu=alpha=c_g=C_g=1, eta=1/2 <= eta_max="
          f"{inst['eta_max']:.3g}, theta_0=sqrt(2) satisfies A1-A4 and the "
          f"step cap (worst slacks: PL {inst['A1_PL_worst_slack']:.2e}, "
          f"alignment {inst['A2_alignment_worst_slack']:.2e}) and gives "
          f"delta^2={inst['delta2']:.6g}, c1={inst['c1']:.6g}, "
          f"c2=c5={inst['c2']:.6g} -- so Phi=c1 delta^2/c2 has a ZERO "
          f"DENOMINATOR and the clauses using it need a local sigtot>0 "
          f"hypothesis.")
    print(f"[f35] 2/4 c5 IS DEFINED AT ZERO NOISE: over "
          f"{c5_defined['n_zero_noise_draws']} admissible sigtot=0 draws, "
          f"c1>0 at {c5_defined['n_with_c1_strictly_positive']} and "
          f"c5=c2/c1=0 at {c5_defined['n_with_c5_exactly_zero']}, with "
          f"{c5_defined['n_with_c5_not_finite']} non-finite.  The corollary's "
          f"boundary paragraph was wrong about c5 and right about Phi.")
    print(f"[f35] 3/4 RESTRICTING (ii)-(iii) TO sigtot>0 LOSES NOTHING: the "
          f"early-branch criterion holds at every t "
          f"({restriction['C1_n_early_criterion_failures']} failures) and the "
          f"bound strictly decreases on "
          f"{restriction['C1_n_resolvable_pairs_checked']} resolvable pairs "
          f"({restriction['C1_n_resolvable_pairs_not_strictly_decreasing']} "
          f"violations), while clause (iii)'s Phi<=1 has "
          f"{restriction['C2_n_draws_satisfying_Phi_le_1_i_e_delta2_le_c5']} "
          f"zero-noise instances.")
    print(f"[f35] 4/4 'BELOW epsilon' IS FALSE: at c1=1/2, delta^2=1, "
          f"epsilon=1/2 the printed threshold is {d1['threshold']:.6g}, t=1 "
          f"meets it, and the bound is {d1['bound_at_t']:.6g} = epsilon.  "
          f"Realized by admissible constants (eta=1/2 <= eta_max="
          f"{d1w['eta_max']:.3g}).  Repaired forms certified: '<= epsilon' "
          f"above the threshold on {repair['D2_n_pairs_checked']} pairs with "
          f"{repair['D2_n_violations']} violations; '< epsilon' above a "
          f"STRICT threshold on {repair['D3_n_pairs_checked']} pairs with "
          f"{repair['D3_n_violations']} violations; and the equality case is "
          f"reachable at all {repair['D4_n_draws_constructed']} constructed "
          f"draws, at every one of which the bound is not below eps but is "
          f"at most eps.")
    print("[f35] DONE", flush=True)


if __name__ == "__main__":
    main()
