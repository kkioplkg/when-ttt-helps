"""F18 -- measured verification of the INTEGER one-step criterion.

WHY THIS SCRIPT EXISTS
----------------------
The manuscript's headline "if and only if" is a statement about the
*continuous interpolation* of the risk curve to real t, while the stated
protocol executes only integer SGD steps.  Condition (P)

    2 lambda alpha^2 (delta^2 - nu) > (1 - alpha^2) eta^2 sigma^2,
    lambda = log(1/(1-eta)),  nu = eta sigma^2 / (2 - eta)

is exactly "the derivative of the interpolated curve at t = 0 is negative".
It guarantees a beneficial *fractional* minimiser t^star, not a beneficial
executable step.  The replacement criterion is the exact one-step
condition the paper already displays in Figure 2,

    alpha^2 delta^2 (2 - eta alpha^2) > eta sigma^2          [G(1) > 0]

together with the claim that, given the proved unimodality of the interpolated
curve, an integer stopping time improves on freezing IF AND ONLY IF the first
integer step does.

Everything needed to check that claim against measurement is already in the
f10 records; this script re-analyses them and adds no simulation.

WHAT IS CHECKED
  A. CURVE EQUALITY (closed form, both curves emitted by f10 itself).
     f10 emits `boundary_onestep_exact` (the closed-form G(1) = 0 locus) and
     `boundary_oracle_exact` (the locus where min_{t=0..T} Exc(t) = Exc(0),
     found by numerical bisection on the exact risk curve over INTEGER t).
     The integer-criterion theorem predicts these are the SAME
     curve.  Their agreement is quantified here, on f10's own alpha grid and
     on an independently recomputed (eta, alpha) grid that covers step sizes
     f10 never ran.  This is the theorem's own prediction tested against a
     numerical optimisation that knows nothing about the one-step formula.

  B. MEASURED INTEGER CRITERION (the point of the script).
     For every cell of every f10 seed, two labels are formed from MEASURED
     quantities only:
         onestep_positive   delta^2 - E_B[u_1^2]      > 0
         oracle_adapts      argmin_t E_B[u_t^2] > 0 and its gain > tol
     The theorem says these labels coincide.  Agreement is reported over all
     625 cells and, separately, over the cells where the one-step gain is
     resolved at 3 Monte-Carlo standard errors -- the disagreements are
     expected to be confined to the unresolved cells, where the oracle's
     argmin over T+1 noisy curve values wins by chance (the optimism f10
     already measures).

  C. FITTED-THRESHOLD RATIOS AGAINST EACH CURVE.
     f10 fits a 1-D sign threshold on the phase statistic
     alpha^2 delta^2 / sigma^2 (fit on even cells, scored on the disjoint odd
     cells) and reports its ratio to the FLOW boundary eta/2.  The exact
     one-step boundary is not a constant in that statistic -- it is
     eta / (2 - eta alpha^2) -- so the same fit is repeated here on the
     exact-corrected statistic

         S = alpha^2 delta^2 (2 - eta alpha^2) / sigma^2,

     whose exact one-step boundary IS the constant eta.  Both ratios are
     reported per seed, with the two fixed (unfitted) criteria scored on the
     measured signs so the reader can see whether the data can tell them
     apart at all.

  D. THE SLIVER.
     The set where the continuous criterion (P) fires but the integer
     criterion does not is the region in which the manuscript's "if and only
     if" is false.  Its size is reported (i) as a count of f10 grid cells,
     (ii) as the relative width in delta/sigma at fixed alpha, and (iii) as a
     function of eta, since the sliver closes as eta -> 0 (the flow limit) and
     opens at the large step sizes real TTT uses.  The measured gains at the
     sliver cells are printed with their z-scores, because the honest
     statement at eta = 0.05 is that the sliver is real but far below the
     Monte-Carlo resolution of the 20,000-replicate grid.

  E. COUNTEREXAMPLE AUDIT.
     The worked counterexample (eta = 0.2, alpha = 0.4, sigma = 1,
     delta = 0.78) is re-evaluated with the pipeline's OWN closed-form risk
     (`run_e1.excess_risk`, imported through common.py), reporting (P), the
     continuous minimiser and its gain, and the gain at every small integer
     step.  This certifies the counterexample against the repository's code
     rather than against a re-derivation.

DATA (re-analysis only; nothing is simulated)
    experiments/results/is_fresh/f10_oracle_grid_summary.json
    experiments/results/is_fresh/f10_oracle_grid_seed{20260801..20260805}.json

Usage: python f18_integer_boundary_check.py
Writes experiments/results/is_fresh/f18_integer_boundary_check.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import common as C
import f10_oracle_grid as F10

RES = C.RESULTS_DIR
SEEDS = C.SEEDS
ETA_GRID = [0.01, 0.02, 0.05, 0.1, 0.2, 0.4]


# ------------------------------------------------------------------ helpers

def load(name):
    with open(os.path.join(RES, name), encoding="utf-8") as fh:
        return json.load(fh)


def curve_map(curve):
    return {round(p["alpha"], 12): p["delta_over_sigma"] for p in curve}


def p_condition_ratio(alpha, sigma, eta):
    """delta/sigma at which the CONTINUOUS condition (P) turns on."""
    return F10.derivative_boundary_ratio(alpha, sigma, eta)


def onestep_ratio(alpha, sigma, eta):
    return F10.onestep_boundary_ratio(alpha, sigma, eta)


# ------------------------------------------------------- A. curve equality

def curve_equality_from_f10(summ):
    tb = summ["theory_boundaries"]
    one = curve_map(tb["boundary_onestep_exact"])
    ora = curve_map(tb["boundary_oracle_exact"])
    dev = [(a, ora[a], one[a], abs(ora[a] - one[a]), abs(ora[a] - one[a]) / one[a])
           for a in sorted(one) if a in ora]
    return {
        "n_alphas": len(dev),
        "max_abs_deviation": max(d[3] for d in dev),
        "max_rel_deviation": max(d[4] for d in dev),
        "note": ("boundary_oracle_exact is found by bisection on "
                 "min_{t=0..T} Exc(t) = Exc(0) and never uses the one-step "
                 "formula; boundary_onestep_exact is the closed-form G(1)=0 "
                 "locus.  Equality is the integer-criterion theorem."),
    }


def curve_equality_recomputed(sigma, T, eta_grid=ETA_GRID, n_alpha=40):
    """Independent recomputation over step sizes f10 never simulated."""
    alphas = np.linspace(0.05, 1.0, n_alpha)
    out = {}
    for eta in eta_grid:
        rows = []
        for a in alphas:
            r_one = onestep_ratio(float(a), sigma, eta)
            r_ora = F10.oracle_boundary_ratio(float(a), sigma, eta, T)
            r_p = p_condition_ratio(float(a), sigma, eta)
            if not (np.isfinite(r_one) and np.isfinite(r_ora)):
                continue
            rows.append({"alpha": float(a), "r_onestep": r_one,
                         "r_integer_oracle": r_ora, "r_condition_P": r_p})
        rel = [abs(x["r_integer_oracle"] - x["r_onestep"]) / x["r_onestep"]
               for x in rows]
        sliver = [x["r_onestep"] / x["r_condition_P"] - 1.0 for x in rows]
        out[f"eta={eta}"] = {
            "eta": eta, "n_alphas": len(rows),
            "max_rel_deviation_integer_oracle_vs_onestep": float(np.max(rel)),
            "sliver_rel_width_delta_over_sigma": {
                "min": float(np.min(sliver)), "max": float(np.max(sliver)),
                "at_alpha_min": sliver[0], "at_alpha_1": sliver[-1]},
        }
    return out


# ------------------------------------------- B/C/D. measured re-analysis

def grid_arrays(rec):
    alphas = np.asarray(rec["alphas"], float)
    ratios = np.asarray(rec["ratios"], float)
    A = alphas[:, None] * np.ones((1, len(ratios)))
    R = np.ones((len(alphas), 1)) * ratios[None, :]
    return alphas, ratios, A, R


def criteria(A, R, eta):
    """Three closed-form sign criteria on the grid (predictions, not fits)."""
    phase = (A * R) ** 2                      # alpha^2 delta^2 / sigma^2
    s_exact = phase * (2.0 - eta * A ** 2)    # exact one-step statistic
    lam = np.log(1.0 / (1.0 - eta))
    nu = eta / (2.0 - eta)
    p_lhs = 2.0 * lam * A ** 2 * (R ** 2 - nu)
    p_rhs = (1.0 - A ** 2) * eta ** 2
    return {
        "phase": phase, "s_exact": s_exact,
        "onestep": s_exact > eta,
        "flow": phase > eta / 2.0,
        "condition_P": p_lhs > p_rhs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=SEEDS)
    args = ap.parse_args()

    summ = load("f10_oracle_grid_summary.json")
    eta, sigma, T = summ["eta"], summ["sigma"], summ["T"]
    per_seed = [load(f"f10_oracle_grid_seed{s}.json") for s in args.seeds]
    ref = per_seed[0]
    alphas, ratios, A, R = grid_arrays(ref)
    cr = criteria(A, R, eta)
    n_cells = cr["phase"].size

    # ---------------- D. sliver geometry on f10's own grid
    sliver_P = cr["condition_P"] & ~cr["onestep"]
    disagree_flow = cr["onestep"] != cr["flow"]
    sliver_cells = [{"i": int(i), "j": int(j),
                     "alpha": float(alphas[i]), "delta_over_sigma": float(ratios[j]),
                     "phase": float(cr["phase"][i, j]),
                     "condition_P": bool(cr["condition_P"][i, j]),
                     "onestep": bool(cr["onestep"][i, j]),
                     "flow": bool(cr["flow"][i, j])}
                    for i, j in np.argwhere(sliver_P | disagree_flow)]

    # measured gains at those cells, all seeds
    for c in sliver_cells:
        zs, gs = [], []
        for rec in per_seed:
            g = np.asarray(rec["gain_onestep"], float)[c["i"], c["j"]]
            se = np.asarray(rec["gain_onestep_se"], float)[c["i"], c["j"]]
            gs.append(float(g))
            zs.append(float(g / se) if se > 0 else float("nan"))
        th = np.asarray(ref["gain_onestep_theory_reference"], float)[c["i"], c["j"]]
        c["measured_gain_by_seed"] = gs
        c["measured_z_by_seed"] = zs
        c["max_abs_z"] = float(np.nanmax(np.abs(zs)))
        c["closed_form_gain"] = float(th)
        c["resolved_at_3se_in_any_seed"] = bool(np.nanmax(np.abs(zs)) > 3.0)

    # ---------------- B. measured integer criterion, per seed
    integer_criterion = []
    for rec in per_seed:
        g1 = np.asarray(rec["gain_onestep"], float)
        se1 = np.asarray(rec["gain_onestep_se"], float)
        go = np.asarray(rec["gain_oracle"], float)
        to = np.asarray(rec["t_oracle"], int)
        scale = (ratios ** 2)[None, :] * np.ones(g1.shape)
        tol = 1e-9 * np.maximum(scale, 1.0)
        lab_one = g1 > 0
        lab_ora = (go > tol) & (to > 0)
        res = np.abs(g1) > 3.0 * se1
        dis = lab_one != lab_ora
        integer_criterion.append({
            "seed": rec["seed"],
            "n_cells": int(g1.size),
            "n_onestep_positive": int(lab_one.sum()),
            "n_oracle_adapts": int(lab_ora.sum()),
            "n_disagree": int(dis.sum()),
            "agreement_all_cells": float((~dis).mean()),
            "n_cells_resolved_3se": int(res.sum()),
            "n_disagree_resolved_3se": int((dis & res).sum()),
            "agreement_resolved_3se": float((~dis[res]).mean()),
            "max_abs_z_among_disagreements": (
                float(np.abs(g1[dis] / se1[dis]).max()) if dis.any() else 0.0),
            "disagreements_all_have_oracle_adapt_and_onestep_negative": bool(
                (lab_ora[dis] & ~lab_one[dis]).all()) if dis.any() else True,
        })

    # ---------------- C. fitted thresholds against each curve
    thr_rows = []
    for rec in per_seed:
        g1 = np.asarray(rec["gain_onestep"], float)
        se1 = np.asarray(rec["gain_onestep_se"], float)
        lab = (g1.ravel() > 0).astype(int)
        ph = cr["phase"].ravel()
        sx = cr["s_exact"].ravel()
        res = (np.abs(g1) > 3.0 * se1).ravel()

        fit_ph, thr_ph = C.fit_sign_threshold(ph[::2], lab[::2])
        hold_ph, _ = C.eval_sign_threshold(ph[1::2], lab[1::2], thr_ph)
        fit_sx, thr_sx = C.fit_sign_threshold(sx[::2], lab[::2])
        hold_sx, _ = C.eval_sign_threshold(sx[1::2], lab[1::2], thr_sx)
        hold_ph_res, n_r = C.eval_sign_threshold(
            ph[1::2][res[1::2]], lab[1::2][res[1::2]], thr_ph)
        hold_sx_res, _ = C.eval_sign_threshold(
            sx[1::2][res[1::2]], lab[1::2][res[1::2]], thr_sx)

        # fixed (unfitted) criteria scored on the measured signs
        acc_flow = float(((ph > eta / 2.0).astype(int) == lab).mean())
        acc_exact = float(((sx > eta).astype(int) == lab).mean())
        acc_flow_res = float(((ph[res] > eta / 2.0).astype(int) == lab[res]).mean())
        acc_exact_res = float(((sx[res] > eta).astype(int) == lab[res]).mean())

        thr_rows.append({
            "seed": rec["seed"],
            "fitted_threshold_phase_stat": thr_ph,
            "ratio_vs_flow_boundary_eta_over_2": thr_ph / (eta / 2.0),
            "fit_accuracy_even_phase": fit_ph,
            "holdout_accuracy_odd_phase": hold_ph,
            "holdout_accuracy_odd_phase_resolved": hold_ph_res,
            "fitted_threshold_exact_statistic": thr_sx,
            "ratio_vs_exact_onestep_boundary_eta": thr_sx / eta,
            "fit_accuracy_even_exact": fit_sx,
            "holdout_accuracy_odd_exact": hold_sx,
            "holdout_accuracy_odd_exact_resolved": hold_sx_res,
            "n_holdout_resolved": int(n_r),
            "fixed_criterion_accuracy_flow": acc_flow,
            "fixed_criterion_accuracy_exact_onestep": acc_exact,
            "fixed_criterion_accuracy_flow_resolved": acc_flow_res,
            "fixed_criterion_accuracy_exact_onestep_resolved": acc_exact_res,
        })

    # exact one-step boundary expressed in the plain phase statistic is
    # alpha-dependent; report its range over the grid so the ratio above is
    # interpretable next to f10's flow ratio
    exact_phase_thr = eta / (2.0 - eta * alphas ** 2)

    # ---------------- E. counterexample audit with the repo's closed form
    ce = {"eta": 0.2, "alpha": 0.4, "sigma": 1.0, "delta": 0.78}
    a, d, sg, et = ce["alpha"], ce["delta"], ce["sigma"], ce["eta"]
    lam = np.log(1.0 / (1.0 - et))
    nu = et * sg ** 2 / (2.0 - et)
    ts = np.arange(0, 21)
    risks = C.excess_risk(ts, a, d, sg, et)
    tt = np.linspace(0.0, 3.0, 30001)
    riskc = C.excess_risk(tt, a, d, sg, et)
    k = int(np.argmin(riskc))
    ce.update({
        "condition_P_lhs_2lam_a2_(d2-nu)": float(2 * lam * a ** 2 * (d ** 2 - nu)),
        "condition_P_rhs_(1-a2)eta2sigma2": float((1 - a ** 2) * et ** 2 * sg ** 2),
        "condition_P_holds": bool(2 * lam * a ** 2 * (d ** 2 - nu)
                                  > (1 - a ** 2) * et ** 2 * sg ** 2),
        "onestep_statistic_a2d2(2-eta a2)": float(a ** 2 * d ** 2
                                                  * (2 - et * a ** 2)),
        "onestep_boundary_eta_sigma2": float(et * sg ** 2),
        "onestep_criterion_holds": bool(a ** 2 * d ** 2 * (2 - et * a ** 2)
                                        > et * sg ** 2),
        "t_star_continuous": float(tt[k]),
        "gain_at_t_star_continuous": float(d ** 2 - riskc[k]),
        "gain_at_integer_steps_0_to_20": [float(d ** 2 - r) for r in risks],
        "gain_at_t_equals_0_is_exactly_zero": float(d ** 2 - risks[0]),
        "best_gain_over_integer_steps_ge_1": float(d ** 2 - risks[1:].min()),
        "argmin_integer_step_ge_1": int(1 + np.argmin(risks[1:])),
    })

    # ---------------- F. is the containment {P and not I} subset {t*<1} STRICT?
    # The theorem proves only one direction: disagreement forces t* < 1.  The
    # converse -- that every (P)-firing point with t* < 1 disagrees -- is not
    # proved and is FALSE.  Certify that by exhibiting a parameter point at
    # which (P) holds, t* < 1, and the exact one-step gain is nonetheless
    # POSITIVE, so (I) holds too and the two criteria agree.
    #
    # Construction (no magic constants): fix eta, alpha, sigma on the grid the
    # paper uses and bracket delta^2 between two bisected boundaries --
    #   d2_I   the (I) boundary, the smallest delta^2 at which G(1) > 0, and
    #   d2_t1  the delta^2 at which the continuous minimiser reaches t* = 1.
    # In delta^2 the ordering is  (P) boundary  <  (I) boundary  <  d2_t1:
    # the sliver is the band between the first two, and the band between the
    # LAST two is a whole interval on which (P) holds, (I) holds -- so the
    # criteria agree -- and t* is still below 1.  Every point of that interval
    # refutes the set-equality.  We report the interval and take the witness
    # at its midpoint.
    def _tstar_continuous(a, d2, sg, et):
        lm = np.log(1.0 / (1.0 - et))
        nn = et * sg ** 2 / (2.0 - et)
        A = 2 * lm * a ** 2 * (a ** 2 * d2 - nn)
        Bq = 2 * lm * d2 * a ** 2 * (1 - a ** 2)
        Cq = (1 - a ** 2) * et ** 2 * sg ** 2
        xo = 2 * Cq / (Bq + np.sqrt(Bq * Bq + 4 * A * Cq))
        return float(np.log(1.0 / xo) / lm)

    def _P(a, d2, sg, et):
        lm = np.log(1.0 / (1.0 - et))
        nn = et * sg ** 2 / (2.0 - et)
        return (2 * lm * a ** 2 * (d2 - nn)
                - (1 - a ** 2) * et ** 2 * sg ** 2)

    def _G1(a, d2, sg, et):
        return et * (a ** 2 * d2 * (2 - et * a ** 2) - et * sg ** 2)

    def _bisect(pred, lo, hi, n=300):
        """Smallest x in [lo, hi] with pred(x) true (pred monotone in x)."""
        for _ in range(n):
            mid = 0.5 * (lo + hi)
            if pred(mid):
                hi = mid
            else:
                lo = mid
        return hi

    w_eta, w_alpha, w_sigma = 0.05, 0.05, 1.0
    d2_P = _bisect(lambda x: _P(w_alpha, x, w_sigma, w_eta) > 0, 0.0, 1e6)
    d2_I = _bisect(lambda x: _G1(w_alpha, x, w_sigma, w_eta) > 0, 0.0, 1e6)
    d2_t1 = _bisect(
        lambda x: _tstar_continuous(w_alpha, x, w_sigma, w_eta) >= 1.0,
        d2_P * (1 + 1e-12), 1e6)
    w_d2 = 0.5 * (d2_I + d2_t1)                   # midpoint of the window
    witness = {
        "purpose": ("certifies that the containment {(P) and not (I)} subset "
                    "{t* < 1} is STRICT: on the whole interval reported below "
                    "(P) holds, t* < 1, and the exact one-step gain is "
                    "positive, so (I) holds as well and the two criteria "
                    "AGREE -- which the withdrawn set-equality forbids"),
        "construction": ("three bisections at fixed (eta, alpha, sigma): the "
                         "(P) boundary, the (I) boundary, and the delta^2 at "
                         "which t* reaches 1.  The witness is the midpoint of "
                         "[(I) boundary, t*=1 boundary].  No constant is "
                         "chosen by hand."),
        "eta": w_eta, "alpha": w_alpha, "sigma": w_sigma,
        "boundary_delta2_P": float(d2_P),
        "boundary_delta2_I": float(d2_I),
        "boundary_delta2_where_tstar_eq_1": float(d2_t1),
        "sliver_delta2_interval_P_and_not_I": [float(d2_P), float(d2_I)],
        "agreement_window_delta2_with_tstar_lt_1": [float(d2_I), float(d2_t1)],
        "agreement_window_is_nonempty": bool(d2_I < d2_t1),
        "delta2": float(w_d2),
        "condition_P_margin": float(_P(w_alpha, w_d2, w_sigma, w_eta)),
        "condition_P_holds": bool(_P(w_alpha, w_d2, w_sigma, w_eta) > 0),
        "t_star_continuous": _tstar_continuous(w_alpha, w_d2, w_sigma, w_eta),
        "onestep_gain_G1": float(_G1(w_alpha, w_d2, w_sigma, w_eta)),
        "onestep_criterion_I_holds": bool(
            _G1(w_alpha, w_d2, w_sigma, w_eta) > 0),
        "criteria_agree_here": bool(
            _P(w_alpha, w_d2, w_sigma, w_eta) > 0
            and _G1(w_alpha, w_d2, w_sigma, w_eta) > 0),
        "gain_at_t_star_continuous_closed_form": float(
            w_d2 - C.excess_risk(
                np.array([_tstar_continuous(w_alpha, w_d2, w_sigma, w_eta)]),
                w_alpha, float(np.sqrt(w_d2)), w_sigma, w_eta)[0]),
    }
    out = {
        "script": "f18_integer_boundary_check.py",
        "finding": ("the exact 'if and only "
                    "if' is a statement about the continuous interpolation; "
                    "the executable criterion is the integer one-step "
                    "condition alpha^2 delta^2 (2 - eta alpha^2) > eta sigma^2"),
        "kind": "re-analysis of existing f10 records; no simulation was run",
        "source_records": [
            "experiments/results/is_fresh/f10_oracle_grid_summary.json",
            "experiments/results/is_fresh/f10_oracle_grid_seed{20260801..05}.json"],
        "grid": {"n_alpha": len(alphas), "n_ratio": len(ratios),
                 "n_cells": int(n_cells), "eta": eta, "sigma": sigma, "T": T,
                 "n_rep_per_cell": ref["n_rep"], "seeds": args.seeds},

        "A_curve_equality_f10_emitted": curve_equality_from_f10(summ),
        "A_curve_equality_recomputed_over_eta": curve_equality_recomputed(
            sigma, T),

        "B_measured_integer_criterion": {
            "labels": {
                "onestep_positive": "delta^2 - E_B[u_1^2] > 0 (measured)",
                "oracle_adapts": ("argmin_{0<=t<=T} E_B[u_t^2] > 0 and its "
                                  "gain > 1e-9 relative floor (measured)")},
            "per_seed": integer_criterion,
            "agreement_all_cells": C.mean_range(
                [r["agreement_all_cells"] for r in integer_criterion]),
            "agreement_resolved_3se": C.mean_range(
                [r["agreement_resolved_3se"] for r in integer_criterion]),
            "n_disagree": C.mean_range(
                [r["n_disagree"] for r in integer_criterion]),
            "n_disagree_resolved_3se": C.mean_range(
                [r["n_disagree_resolved_3se"] for r in integer_criterion]),
            "max_abs_z_among_disagreements": C.mean_range(
                [r["max_abs_z_among_disagreements"] for r in integer_criterion]),
        },

        "C_fitted_thresholds": {
            "protocol": ("threshold fitted on the EVEN-indexed cells and "
                         "scored on the disjoint ODD-indexed cells, labels "
                         "from the measured one-step gain; identical to f10"),
            "exact_onestep_boundary_in_phase_units": {
                "expression": "eta / (2 - eta alpha^2)",
                "min": float(exact_phase_thr.min()),
                "max": float(exact_phase_thr.max()),
                "flow_boundary": eta / 2.0,
                "max_relative_gap_vs_flow": float(
                    exact_phase_thr.max() / (eta / 2.0) - 1.0)},
            "per_seed": thr_rows,
            "ratio_vs_flow_boundary": C.mean_range(
                [r["ratio_vs_flow_boundary_eta_over_2"] for r in thr_rows]),
            "ratio_vs_exact_onestep_boundary": C.mean_range(
                [r["ratio_vs_exact_onestep_boundary_eta"] for r in thr_rows]),
            "holdout_accuracy_phase": C.mean_range(
                [r["holdout_accuracy_odd_phase"] for r in thr_rows]),
            "holdout_accuracy_exact": C.mean_range(
                [r["holdout_accuracy_odd_exact"] for r in thr_rows]),
            "holdout_accuracy_phase_resolved": C.mean_range(
                [r["holdout_accuracy_odd_phase_resolved"] for r in thr_rows]),
            "holdout_accuracy_exact_resolved": C.mean_range(
                [r["holdout_accuracy_odd_exact_resolved"] for r in thr_rows]),
            "fixed_criterion_accuracy_flow": C.mean_range(
                [r["fixed_criterion_accuracy_flow"] for r in thr_rows]),
            "fixed_criterion_accuracy_exact_onestep": C.mean_range(
                [r["fixed_criterion_accuracy_exact_onestep"] for r in thr_rows]),
        },

        "D_sliver": {
            "definition": ("cells where the continuous condition (P) fires "
                           "but the integer one-step criterion does not -- the "
                           "region in which 'TTT helps iff (P)' is false"),
            "n_cells_total": int(n_cells),
            "n_cells_condition_P_true": int(cr["condition_P"].sum()),
            "n_cells_onestep_true": int(cr["onestep"].sum()),
            "n_cells_flow_true": int(cr["flow"].sum()),
            "n_cells_sliver_P_and_not_onestep": int(sliver_P.sum()),
            "n_cells_onestep_vs_flow_disagree": int(disagree_flow.sum()),
            "n_sliver_cells_resolved_at_3se_any_seed": int(sum(
                1 for c in sliver_cells if c["resolved_at_3se_in_any_seed"])),
            "cells": sliver_cells,
            "geometry_note": (
                "in delta/sigma the sliver is the band between the (P) curve "
                "and the one-step curve; its relative width is reported per "
                "eta in A_curve_equality_recomputed_over_eta"),
        },

        "E_counterexample_audit": ce,
        "F_containment_strictness_witness": witness,
    }

    # ---------------- assertions (the checks this script is worth having)
    assert out["A_curve_equality_f10_emitted"]["max_rel_deviation"] < 1e-6, (
        "the integer-oracle boundary and the one-step boundary emitted by f10 "
        "are not the same curve")
    for k, v in out["A_curve_equality_recomputed_over_eta"].items():
        assert v["max_rel_deviation_integer_oracle_vs_onestep"] < 1e-5, (
            f"integer-oracle vs one-step boundary disagree at {k}")
    assert all(r["n_disagree_resolved_3se"] == 0 for r in integer_criterion), (
        "the measured integer criterion fails on a Monte-Carlo-resolved cell")
    assert ce["condition_P_holds"] and not ce["onestep_criterion_holds"], (
        "the worked counterexample does not reproduce with the repository's "
        "own closed-form risk")
    assert (ce["best_gain_over_integer_steps_ge_1"] < 0
            < ce["gain_at_t_star_continuous"]), (
        "counterexample: an integer step is not harmful after all")
    w = out["F_containment_strictness_witness"]
    assert w["condition_P_holds"] and w["t_star_continuous"] < 1.0 \
        and w["onestep_criterion_I_holds"], (
        "the strictness witness does not witness: it must have (P) true, "
        "t* < 1 and a POSITIVE one-step gain simultaneously, which is what "
        "refutes the withdrawn set-equality 'the disagreement set is exactly "
        "{t* < 1}'")
    assert w["agreement_window_is_nonempty"], (
        "the agreement window is empty, so the containment could not be shown "
        "strict at this (eta, alpha, sigma)")

    C.save(out, "f18_integer_boundary_check.json")

    ic = out["B_measured_integer_criterion"]
    tc = out["C_fitted_thresholds"]
    print(f"[f18] 1/3 integer criterion: measured oracle-adapts and measured "
          f"one-step-positive labels agree on "
          f"{ic['agreement_all_cells']['mean']*100:.1f}% of 625 cells "
          f"({int(ic['n_disagree']['min'])}-{int(ic['n_disagree']['max'])} "
          f"disagreements per seed) and on 100.0% of the "
          f"{int(min(r['n_cells_resolved_3se'] for r in integer_criterion))}-"
          f"{int(max(r['n_cells_resolved_3se'] for r in integer_criterion))} "
          f"cells resolved at 3 SE "
          f"(0 disagreements in all 5 seeds; every disagreement has "
          f"|z| <= {ic['max_abs_z_among_disagreements']['max']:.1f}).")
    print(f"[f18] 2/3 boundaries: the integer-oracle boundary and the exact "
          f"one-step boundary coincide to "
          f"{out['A_curve_equality_f10_emitted']['max_rel_deviation']:.1e} "
          f"relative on f10's alphas and to <1e-5 over eta in "
          f"{ETA_GRID}; fitted threshold / flow boundary = "
          f"{tc['ratio_vs_flow_boundary']['mean']:.3f} "
          f"[{tc['ratio_vs_flow_boundary']['min']:.3f}, "
          f"{tc['ratio_vs_flow_boundary']['max']:.3f}], fitted threshold / "
          f"exact one-step boundary = "
          f"{tc['ratio_vs_exact_onestep_boundary']['mean']:.3f} "
          f"[{tc['ratio_vs_exact_onestep_boundary']['min']:.3f}, "
          f"{tc['ratio_vs_exact_onestep_boundary']['max']:.3f}].")
    sl = out["D_sliver"]
    wid = out["A_curve_equality_recomputed_over_eta"]
    print(f"[f18] 3/3 sliver: (P) fires without the integer criterion on "
          f"{sl['n_cells_sliver_P_and_not_onestep']}/{sl['n_cells_total']} "
          f"cells at eta=0.05 (none resolved at 3 SE, |z| <= "
          f"{max(c['max_abs_z'] for c in sliver_cells):.1f}); the band is "
          f"{wid['eta=0.05']['sliver_rel_width_delta_over_sigma']['max']*100:.2f}% "
          f"wide in delta/sigma at eta=0.05 but "
          f"{wid['eta=0.4']['sliver_rel_width_delta_over_sigma']['max']*100:.1f}% "
          f"at eta=0.4, and the worked counterexample (eta=0.2) reproduces "
          f"with the repository's closed form: continuous gain "
          f"{ce['gain_at_t_star_continuous']:+.2e} at t*={ce['t_star_continuous']:.3f}, "
          f"best gain over integer steps >= 1 "
          f"{ce['best_gain_over_integer_steps_ge_1']:+.2e}.")
    print(f"[f18] strictness witness: eta={w['eta']}, alpha={w['alpha']}, "
          f"sigma={w['sigma']}; sliver (P and not I) is delta^2 in "
          f"[{w['boundary_delta2_P']:.6f}, {w['boundary_delta2_I']:.6f}], but "
          f"t* < 1 persists up to delta^2 = "
          f"{w['boundary_delta2_where_tstar_eq_1']:.6f}, so on "
          f"[{w['boundary_delta2_I']:.6f}, "
          f"{w['boundary_delta2_where_tstar_eq_1']:.6f}] both criteria hold "
          f"with t* < 1.  At the midpoint delta^2={w['delta2']:.7f}: (P) by "
          f"{w['condition_P_margin']:.3e}, t*={w['t_star_continuous']:.4f} < 1, "
          f"G(1)={w['onestep_gain_G1']:+.3e} > 0.  The "
          f"disagreement set is therefore STRICTLY inside {{t* < 1}}.")
    print("[f18] DONE", flush=True)


if __name__ == "__main__":
    main()
