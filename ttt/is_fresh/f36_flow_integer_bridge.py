"""F36 -- the flow curve is not the exact curve: the integer clause needs
the exact criterion, and sigma = 0 is a value of the exact model's noise.

WHY THIS SCRIPT EXISTS
----------------------
Two separate claims about the exact model were argued from the wrong
object, and this script certifies the defect and the repair for each.

DEFECT A -- THE FLOW COROLLARY'S INTEGER CLAUSE.
    The gradient-flow corollary states, for 2 alpha^2 delta^2 <= eta
    sigma^2, that the flow curve

        F_eta(tau) = (delta(1-a2) + delta a2 e^{-tau})^2
                     + eta[ a2 sigma^2 (1 - e^{-2tau})/2
                           + (1-a2) sigma^2 tau ],      a2 = alpha^2,

    is nondecreasing, "so no deterministic choice of real time -- and A
    FORTIORI no choice of integer step -- gains".  The conclusion is TRUE
    but the argument is not: F_eta is an APPROXIMATION of the exact curve

        Exc(t) = (delta(1-a2) + delta a2 (1-eta)^t)^2
                 + a2 nu (1 - (1-eta)^{2t}) + (1-a2) eta^2 sigma^2 t,

    valid only up to the sandwich error eta^2 sigma^2 (1+tau), and
    nondecrease of one function is not nondecrease of the other.  There is
    no "a fortiori" step between two different curves.

    THIS IS NOT A PEDANTIC OBJECTION, and the script proves it is not: at
    eta = 0.2, alpha = 0.4, sigma = 1, delta = 0.78 the corollary's own
    hypothesis 2 alpha^2 delta^2 <= eta sigma^2 holds -- so F_eta IS
    nondecreasing on [0, infinity) -- while the EXACT interpolated curve
    strictly decreases on (0, t*) with t* about 0.2545 and a positive
    interpolated gain of about 2.4e-4.  The implication "F_eta
    nondecreasing => Exc nondecreasing" is therefore FALSE at an instance
    inside the corollary's own hypotheses.

    THE REPAIR IS THE EXACT CRITERION, not the flow curve.  Since
    eta alpha^4 delta^2 >= 0,

        2 a2 delta^2 <= eta sigma^2
          =>  a2 delta^2 (2 - eta a2) = 2 a2 delta^2 - eta a2^2 delta^2
                                      <= 2 a2 delta^2 <= eta sigma^2,

    so the exact integer criterion (I): a2 delta^2 (2 - eta a2) > eta
    sigma^2 FAILS, and the integer theorem's own conclusion gives
    Exc(t) >= delta^2 at every integer t >= 0.

DEFECT B -- "ZERO IS NOT A VALUE OF sigma^2".
    Four passages separated the entropy result from the exact model by
    saying that entropy's auxiliary noise is identically zero and that
    zero is "not a small value of sigma^2 but no value of it at all".
    The exact model's own definition admits sigma = 0, the flow corollary
    analyses that boundary explicitly, and the exact one-step gain there
    is nontrivial: at eta = 0.1, alpha = 0.5, delta = 1, sigma = 0,
    G(1) = eta[a2 delta^2 (2 - eta a2)] = 0.049375 > 0.  What is undefined
    at sigma = 0 is the RATIO alpha^2 delta^2/sigma^2 in which the flow
    boundary is usually written -- not the recursion, and not the raw
    signal-against-noise inequality.

WHAT IS CHECKED
  A. THE TWO CURVES ARE DIFFERENT FUNCTIONS.  The sandwich error bound
     |Exc(tau/lambda) - F_eta(tau)| <= eta^2 sigma^2 (1+tau) is re-verified
     over an admissible grid, together with the fact that the difference is
     not identically zero.
  B. THE "A FORTIORI" IMPLICATION IS FALSE.
     B1. The worked instance above, evaluated on a dense grid: F_eta
         nondecreasing, Exc strictly below Exc(0) somewhere, with the
         interpolated minimizer and gain reported.
     B2. A SEARCH over parameters inside the corollary's hypotheses
         (sigma > 0, eta in (0,1/2], alpha in (0,1), delta > 0, and
         2 alpha^2 delta^2 <= eta sigma^2) counting how many admit a real
         t with Exc(t) < delta^2 while F_eta is nondecreasing.
  C. THE REPAIR IS SOUND.  Over the same search:
     C1. the algebraic implication 2 a2 d2 <= eta s2  =>  a2 d2 (2 - eta a2)
         <= eta s2, so criterion (I) fails, with zero violations;
     C2. the conclusion it licenses, Exc(t) >= delta^2 at every integer
         0 <= t <= T, with zero violations -- including at the instance of
         B1, where the flow argument cannot reach it;
     C3. the endpoints alpha in {0, 1} are covered by the same implication
         and are checked separately, since the corollary's dichotomy is
         stated on the open interval.
  D. sigma = 0 IS A VALUE OF THE EXACT MODEL'S NOISE SCALE.
     D1. The worked instance eta = 0.1, alpha = 0.5, delta = 1, sigma = 0
         gives G(1) = 0.049375 exactly, recomputed from the closed form and
         independently from the curve.
     D2. Over a zero-noise search, the exact curve is well defined, the
         one-step gain is positive whenever alpha, delta > 0, and criterion
         (I) reduces to a2 delta^2 (2 - eta a2) > 0.
     D3. What IS undefined at sigma = 0 is the ratio alpha^2 delta^2 /
         sigma^2 -- counted as a zero denominator, not asserted.

Nothing is simulated and no record is read: this is a closed-form audit of
the exact model's own algebra.

Usage: python f36_flow_integer_bridge.py
Writes experiments/results/is_fresh/f36_flow_integer_bridge.json
"""
from __future__ import annotations

import argparse

import numpy as np

import common as C

SEED = 20260809


# --------------------------------------------------------------- the curves

def exc(t, eta, alpha, sigma, delta):
    """The exact expected excess risk, interpolated to real t >= 0."""
    t = np.asarray(t, dtype=float)
    a2 = alpha ** 2
    nu = eta * sigma ** 2 / (2.0 - eta)
    return ((delta * (1.0 - a2) + delta * a2 * (1.0 - eta) ** t) ** 2
            + a2 * nu * (1.0 - (1.0 - eta) ** (2.0 * t))
            + (1.0 - a2) * eta ** 2 * sigma ** 2 * t)


def flow(tau, eta, alpha, sigma, delta):
    """The gradient-flow curve F_eta(tau)."""
    tau = np.asarray(tau, dtype=float)
    a2 = alpha ** 2
    return ((delta * (1.0 - a2) + delta * a2 * np.exp(-tau)) ** 2
            + eta * (a2 * sigma ** 2 / 2.0 * (1.0 - np.exp(-2.0 * tau))
                     + (1.0 - a2) * sigma ** 2 * tau))


def one_step_gain(eta, alpha, sigma, delta):
    """G(1) = eta[alpha^2 delta^2 (2 - eta alpha^2) - eta sigma^2]."""
    a2 = alpha ** 2
    return eta * (a2 * delta ** 2 * (2.0 - eta * a2) - eta * sigma ** 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=400000)
    ap.add_argument("--horizon", type=int, default=400)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    T = args.horizon

    # ---------------- A. the two curves are different functions
    g_eta = np.array([0.02, 0.05, 0.1, 0.2, 0.35, 0.5])
    g_al = np.array([0.05, 0.2, 0.4, 0.6, 0.8, 0.95])
    g_sig = np.array([0.25, 1.0, 4.0])
    g_del = np.array([0.1, 0.5, 1.0, 3.0])
    taus = np.linspace(0.0, 12.0, 4801)
    worst_excess = -np.inf
    worst_abs_diff = 0.0
    n_grid = 0
    for eta in g_eta:
        lam = np.log(1.0 / (1.0 - eta))
        for al in g_al:
            for sg in g_sig:
                for dl in g_del:
                    d = np.abs(exc(taus / lam, eta, al, sg, dl)
                               - flow(taus, eta, al, sg, dl))
                    cap = eta ** 2 * sg ** 2 * (1.0 + taus)
                    worst_excess = max(worst_excess, float(np.max(d - cap)))
                    worst_abs_diff = max(worst_abs_diff, float(np.max(d)))
                    n_grid += d.size
    sandwich = {
        "claim": ("|Exc(tau/lambda) - F_eta(tau)| <= eta^2 sigma^2 (1+tau) "
                  "on eta in (0,1/2]"),
        "n_grid_points": n_grid,
        "worst_signed_excess_over_the_bound": worst_excess,
        "largest_absolute_difference_between_the_two_curves": worst_abs_diff,
        "note": ("the bound holds and the difference is not identically "
                 "zero, which is exactly why nondecrease of one curve is "
                 "not nondecrease of the other"),
    }

    # ---------------- B1. the worked instance
    P = {"eta": 0.2, "alpha": 0.4, "sigma": 1.0, "delta": 0.78}
    a2 = P["alpha"] ** 2
    w = dict(P)
    w["2_alpha2_delta2"] = 2.0 * a2 * P["delta"] ** 2
    w["eta_sigma2"] = P["eta"] * P["sigma"] ** 2
    w["flow_part_b_hypothesis_holds"] = bool(
        w["2_alpha2_delta2"] <= w["eta_sigma2"])
    wt = np.linspace(0.0, 40.0, 4000001)
    Fv = flow(wt, **P)
    w["flow_is_nondecreasing"] = bool(np.all(np.diff(Fv) >= -1e-15))
    w["flow_min_minus_F0"] = float(Fv.min() - flow(0.0, **P))
    et = np.linspace(0.0, 3.0, 3000001)
    Ev = exc(et, **P)
    imin = int(Ev.argmin())
    w["exact_Exc_0"] = float(exc(0.0, **P))
    w["exact_interpolated_minimizer_t_star"] = float(et[imin])
    w["exact_interpolated_minimum"] = float(Ev[imin])
    w["exact_interpolated_gain"] = float(w["exact_Exc_0"] - Ev[imin])
    w["EXACT_CURVE_DIPS_BELOW_Exc0"] = bool(w["exact_interpolated_gain"] > 0.0)
    w["G_1"] = float(one_step_gain(**P))
    w["criterion_I_lhs"] = float(a2 * P["delta"] ** 2
                                 * (2.0 - P["eta"] * a2))
    w["criterion_I_holds"] = bool(w["criterion_I_lhs"] > w["eta_sigma2"])
    ints = np.arange(0, T + 1)
    w["min_integer_Exc_minus_Exc0"] = float(
        np.min(exc(ints, **P)) - w["exact_Exc_0"])
    w["no_integer_step_gains"] = bool(w["min_integer_Exc_minus_Exc0"] >= 0.0)
    w["reading"] = ("F_eta is nondecreasing here and the exact curve is NOT: "
                    "the a fortiori step is invalid.  The conclusion survives "
                    "only through the exact criterion (I), which fails here")

    # ---------------- B2/C. the search inside the corollary's hypotheses
    n = args.draws
    eta = rng.uniform(1e-4, 0.5, n)
    alpha = rng.uniform(1e-4, 1.0 - 1e-4, n)
    sigma = 10.0 ** rng.uniform(-2.0, 2.0, n)
    delta = 10.0 ** rng.uniform(-3.0, 2.0, n)
    a2 = alpha ** 2
    hyp = 2.0 * a2 * delta ** 2 <= eta * sigma ** 2      # part (b)'s hypothesis
    e, al, sg, dl, a2b = eta[hyp], alpha[hyp], sigma[hyp], delta[hyp], a2[hyp]
    m = int(e.size)

    lam = np.log(1.0 / (1.0 - e))
    tau_grid = np.linspace(0.0, 30.0, 601)
    Fm = ((dl * (1.0 - a2b))[:, None]
          + (dl * a2b)[:, None] * np.exp(-tau_grid[None, :])) ** 2 \
        + e[:, None] * ((a2b * sg ** 2 / 2.0)[:, None]
                        * (1.0 - np.exp(-2.0 * tau_grid[None, :]))
                        + ((1.0 - a2b) * sg ** 2)[:, None]
                        * tau_grid[None, :])
    flow_nondecreasing = np.all(np.diff(Fm, axis=1) >= -1e-12
                                * np.maximum(np.abs(Fm[:, :-1]), 1.0), axis=1)

    # the exact interpolated curve on the same real times t = tau/lambda
    t_real = tau_grid[None, :] / lam[:, None]
    nu = e * sg ** 2 / (2.0 - e)
    Em = ((dl * (1.0 - a2b))[:, None]
          + (dl * a2b)[:, None] * (1.0 - e)[:, None] ** t_real) ** 2 \
        + (a2b * nu)[:, None] * (1.0 - (1.0 - e)[:, None] ** (2.0 * t_real)) \
        + ((1.0 - a2b) * e ** 2 * sg ** 2)[:, None] * t_real
    E0 = (dl ** 2)
    exact_dips = np.any(Em < E0[:, None] * (1.0 - 1e-12), axis=1)

    # C1. the algebraic implication
    lhs = a2b * dl ** 2 * (2.0 - e * a2b)
    rhs = e * sg ** 2
    impl_violations = int((lhs > rhs).sum())

    # C2. the conclusion at integer steps
    ti = np.arange(0, T + 1, dtype=float)
    Ei = ((dl * (1.0 - a2b))[:, None]
          + (dl * a2b)[:, None] * (1.0 - e)[:, None] ** ti[None, :]) ** 2 \
        + (a2b * nu)[:, None] * (1.0 - (1.0 - e)[:, None] ** (2.0 * ti[None, :])) \
        + ((1.0 - a2b) * e ** 2 * sg ** 2)[:, None] * ti[None, :]
    slack = Ei - E0[:, None]
    int_violations = int((slack < -1e-12
                          * np.maximum(E0[:, None], 1.0)).sum())

    search = {
        "hypotheses": ("sigma > 0, eta in (0,1/2], alpha in (0,1), delta > 0, "
                       "and the corollary's part-(b) hypothesis "
                       "2 alpha^2 delta^2 <= eta sigma^2"),
        "n_drawn": n,
        "n_inside_part_b": m,
        "B2_n_with_flow_nondecreasing": int(flow_nondecreasing.sum()),
        "B2_n_where_the_EXACT_curve_dips_below_delta2":
            int(exact_dips.sum()),
        "B2_n_where_flow_is_nondecreasing_AND_exact_dips":
            int((flow_nondecreasing & exact_dips).sum()),
        "B2_note": ("every draw in the last count refutes the a fortiori "
                    "step: the flow curve is nondecreasing there and the "
                    "exact curve is not"),
        "C1_claim": ("2 a2 d2 <= eta s2  =>  a2 d2 (2 - eta a2) <= eta s2, "
                     "so criterion (I) fails"),
        "C1_n_violations": impl_violations,
        "C1_worst_signed_lhs_minus_rhs": float(np.max(lhs - rhs)),
        "C2_claim": "Exc(t) >= delta^2 at every integer 0 <= t <= T",
        "C2_n_pairs_checked": int(slack.size),
        "C2_n_violations": int_violations,
        "C2_worst_signed_slack": float(slack.min()),
    }

    # C3. the endpoints, where the corollary's dichotomy is not stated
    ends = {}
    for name, aa in (("alpha_0", 0.0), ("alpha_1", 1.0)):
        ee = rng.uniform(1e-4, 0.5, 50000)
        ss = 10.0 ** rng.uniform(-2.0, 2.0, 50000)
        dd = 10.0 ** rng.uniform(-3.0, 2.0, 50000)
        aa2 = aa ** 2
        h = 2.0 * aa2 * dd ** 2 <= ee * ss ** 2
        ee, ss, dd = ee[h], ss[h], dd[h]
        l = aa2 * dd ** 2 * (2.0 - ee * aa2)
        r = ee * ss ** 2
        nuu = ee * ss ** 2 / (2.0 - ee)
        Ee = ((dd * (1.0 - aa2))[:, None]
              + (dd * aa2)[:, None] * (1.0 - ee)[:, None] ** ti[None, :]) ** 2 \
            + (aa2 * nuu)[:, None] * (1.0 - (1.0 - ee)[:, None]
                                      ** (2.0 * ti[None, :])) \
            + ((1.0 - aa2) * ee ** 2 * ss ** 2)[:, None] * ti[None, :]
        sl = Ee - (dd ** 2)[:, None]
        ends[name] = {
            "n_inside_part_b_hypothesis": int(ee.size),
            "n_implication_violations": int((l > r).sum()),
            "n_integer_violations": int(
                (sl < -1e-12 * np.maximum((dd ** 2)[:, None], 1.0)).sum()),
            "worst_signed_slack": float(sl.min()),
        }

    # ---------------- D. sigma = 0 is a value of the exact model's noise
    ZP = {"eta": 0.1, "alpha": 0.5, "delta": 1.0, "sigma": 0.0}
    z = dict(ZP)
    za2 = ZP["alpha"] ** 2
    z["G_1_closed_form"] = float(one_step_gain(**ZP))
    z["G_1_from_the_curve"] = float(exc(0.0, **ZP) - exc(1.0, **ZP))
    z["G_1_exact_rational"] = float(ZP["eta"] * za2 * ZP["delta"] ** 2
                                    * (2.0 - ZP["eta"] * za2))
    z["is_strictly_positive"] = bool(z["G_1_closed_form"] > 0.0)
    z["ratio_alpha2delta2_over_sigma2_denominator"] = float(ZP["sigma"] ** 2)
    z["ratio_is_a_real_number"] = bool(ZP["sigma"] ** 2 > 0.0)

    ze = rng.uniform(1e-4, 0.5, 200000)
    za = rng.uniform(1e-4, 1.0, 200000)
    zd = 10.0 ** rng.uniform(-3.0, 2.0, 200000)
    zg = one_step_gain(ze, za, 0.0, zd)
    zlhs = za ** 2 * zd ** 2 * (2.0 - ze * za ** 2)
    zero_noise = {
        "worked_instance": z,
        "n_zero_noise_draws": int(ze.size),
        "n_with_finite_exact_curve": int(
            np.isfinite(exc(np.ones_like(ze), ze, za, 0.0, zd)).sum()),
        "n_with_strictly_positive_one_step_gain": int((zg > 0.0).sum()),
        "n_with_criterion_I_satisfied": int((zlhs > 0.0).sum()),
        "n_with_undefined_ratio_alpha2delta2_over_sigma2": int(ze.size),
        "reading": ("sigma = 0 is an admissible value of the exact model's "
                    "noise scale: the recursion, the curve and the one-step "
                    "gain are all defined and nontrivial there.  Only the "
                    "RATIO alpha^2 delta^2/sigma^2 in which the flow boundary "
                    "is written has a zero denominator"),
    }

    out = {
        "script": "f36_flow_integer_bridge.py",
        "kind": ("closed-form audit of the exact model's algebra; nothing "
                 "simulated, no record read"),
        "finding": ("(A) the flow corollary's integer clause is TRUE but does "
                    "not follow 'a fortiori' from the monotonicity of the "
                    "flow curve, and an instance inside the corollary's own "
                    "hypotheses shows the implication is false; it follows "
                    "from the exact integer criterion instead.  (B) sigma = 0 "
                    "is a value of the exact model's noise scale, so the "
                    "entropy result must be separated from the exact model "
                    "structurally and not by calling zero 'no value at all'"),
        "A_the_two_curves_are_different": sandwich,
        "B_a_fortiori_is_false": {"worked_instance": w, "search": search},
        "C_endpoints": ends,
        "D_zero_noise_is_a_value_of_sigma": zero_noise,
    }

    # ---------------- assertions
    assert sandwich["worst_signed_excess_over_the_bound"] <= 0.0, (
        "the sandwich error bound of the flow corollary is violated")
    assert sandwich["largest_absolute_difference_between_the_two_curves"] > 0, (
        "the two curves coincide on the grid -- the a fortiori step would "
        "then be harmless and there would be nothing to repair")
    assert w["flow_part_b_hypothesis_holds"], (
        "the worked instance is not inside the corollary's part (b)")
    assert w["flow_is_nondecreasing"], (
        "the flow curve is not nondecreasing at the worked instance, so it "
        "would not witness the failure of the implication")
    assert w["EXACT_CURVE_DIPS_BELOW_Exc0"], (
        "the exact curve does not dip below delta^2 at the worked instance -- "
        "the a fortiori step would then not be refuted there")
    assert not w["criterion_I_holds"] and w["G_1"] <= 0.0, (
        "criterion (I) does not fail at the worked instance, so the repair "
        "would not license the conclusion there")
    assert w["no_integer_step_gains"], (
        "an integer step gains at the worked instance, which would refute the "
        "corollary's conclusion and not merely its argument")
    assert search["B2_n_where_flow_is_nondecreasing_AND_exact_dips"] > 0, (
        "no admissible draw separates the two curves' monotonicity -- if this "
        "fires, the a fortiori step might be sound after all")
    assert search["C1_n_violations"] == 0, (
        "the algebraic implication that makes criterion (I) fail is wrong")
    assert search["C2_n_violations"] == 0, (
        "Exc(t) < delta^2 at an integer step inside part (b): the corollary's "
        "CONCLUSION, not merely its argument, would be false")
    for name, r in ends.items():
        assert r["n_implication_violations"] == 0, (
            f"the implication fails at the endpoint {name}")
        assert r["n_integer_violations"] == 0, (
            f"an integer step gains at the endpoint {name}")
    assert abs(z["G_1_closed_form"] - 0.049375) < 1e-12, (
        "the zero-noise one-step gain is not 0.049375")
    assert abs(z["G_1_from_the_curve"] - z["G_1_closed_form"]) < 1e-12, (
        "the closed-form gain and the curve disagree at sigma = 0")
    assert zero_noise["n_with_strictly_positive_one_step_gain"] \
        == zero_noise["n_zero_noise_draws"], (
        "the one-step gain is not positive at some zero-noise draw with "
        "alpha, delta > 0")
    assert zero_noise["n_with_finite_exact_curve"] \
        == zero_noise["n_zero_noise_draws"], (
        "the exact curve is not finite at some zero-noise draw")

    C.save(out, "f36_flow_integer_bridge.json")

    print(f"[f36] 1/4 THE TWO CURVES DIFFER: the sandwich bound holds at all "
          f"{sandwich['n_grid_points']} grid points (worst signed excess "
          f"{sandwich['worst_signed_excess_over_the_bound']:.3e}) and the "
          f"largest difference between them is "
          f"{sandwich['largest_absolute_difference_between_the_two_curves']:.4g} "
          f"-- so nondecrease of one is not nondecrease of the other.")
    print(f"[f36] 2/4 'A FORTIORI' REFUTED at eta=0.2, alpha=0.4, sigma=1, "
          f"delta=0.78: the part-(b) hypothesis holds "
          f"({w['2_alpha2_delta2']:.6g} <= {w['eta_sigma2']:.6g}), F_eta is "
          f"nondecreasing, yet the EXACT interpolated curve falls to "
          f"{w['exact_interpolated_minimum']:.9g} at t*="
          f"{w['exact_interpolated_minimizer_t_star']:.5g}, a gain of "
          f"{w['exact_interpolated_gain']:.4g} below "
          f"Exc(0)={w['exact_Exc_0']:.9g}.  Over "
          f"{search['n_inside_part_b']} draws inside part (b), "
          f"{search['B2_n_where_flow_is_nondecreasing_AND_exact_dips']} "
          f"separate the two curves the same way.")
    print(f"[f36] 3/4 THE REPAIR IS SOUND: 2a2d2 <= eta s2 forces "
          f"a2 d2 (2 - eta a2) <= eta s2 at all {search['n_inside_part_b']} "
          f"draws ({search['C1_n_violations']} violations, worst signed "
          f"lhs-rhs {search['C1_worst_signed_lhs_minus_rhs']:.3e}), so (I) "
          f"fails and the integer theorem gives Exc(t) >= delta^2: "
          f"{search['C2_n_violations']} violations over "
          f"{search['C2_n_pairs_checked']} integer evaluations (worst signed "
          f"slack {search['C2_worst_signed_slack']:.3e}), and 0 at either "
          f"endpoint alpha in {{0,1}}.  At the instance of 2/4, G(1)="
          f"{w['G_1']:.6g} <= 0 and no integer step gains.")
    print(f"[f36] 4/4 sigma=0 IS A VALUE OF sigma: at eta=0.1, alpha=0.5, "
          f"delta=1, sigma=0 the exact one-step gain is "
          f"{z['G_1_closed_form']:.6g} > 0, identical from the closed form "
          f"and from the curve.  Over "
          f"{zero_noise['n_zero_noise_draws']} zero-noise draws the curve is "
          f"finite at all of them and G(1) > 0 at "
          f"{zero_noise['n_with_strictly_positive_one_step_gain']}.  What is "
          f"undefined is the ratio alpha^2 delta^2/sigma^2, whose denominator "
          f"is zero at all of them.")
    print("[f36] DONE", flush=True)


if __name__ == "__main__":
    main()
