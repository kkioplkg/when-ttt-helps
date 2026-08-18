"""F10 -- the three gain quantities of the phase diagram, on ONE simulation.

WHY THIS SCRIPT EXISTS
----------------------
Figure 2 as published coloured its grid with a *stopping-selection* quantity
(the realized gain of a split-selected stopping rule) while its caption and the
surrounding text described it as the oracle phase of Theorem 1.  That mismatch
has three parts:

  (a) because ``t = 0`` (decline to adapt) is on the menu, a TRUE oracle gain
      is non-negative by construction -- so the negative cells in the published
      panel are not "TTT hurts", they are stopping-selection error;
  (b) the overlaid boundary was the flow-limit form alpha^2 delta^2/sigma^2 =
      eta/2, not the exact discrete condition of the theorem;
  (c) the genuinely signed, theorem-matched quantity -- the one-step gain --
      was never plotted.

This script measures all three quantities on the SAME simulated replicates, so
they are directly differenceable cell by cell:

    one-step        G1    = delta^2 - E_B[u_1^2]                (signed)
    oracle          Gora  = max_{0<=t<=T} ( delta^2 - E_B[u_t^2] )   (>= 0)
    selected-stop   Gsel  = delta^2 - E_B[u_{t_hat}^2],
                            t_hat = argmin_t E_A[u_t^2]         (signed)

    selection error Gsel - Gora <= 0 identically, by construction.

A and B are disjoint halves of the replicate pool for the cell.  The oracle
scans the SAME held-out half B that it is scored on -- that is what an oracle
is -- so its only bias is the Monte-Carlo optimism of an argmin over T+1
noisy curve values.  That optimism is measured explicitly (see
``oracle_optimism_*`` below) by re-running the oracle on a split of B and is
reported as an audit number rather than assumed negligible.

u_0 = delta holds deterministically in this model, so the frozen risk
delta^2 is exact and none of the three gains needs an estimate of the
baseline.

PROTOCOL
  * grid: alpha in linspace(0.02, 1, 25) x delta/sigma in logspace(-1, 1.2, 25)
    -- the original run_e1.part_b grid, so the panels are drop-in replacements.
  * eta = 0.05, sigma = 1, T = 400.
  * N_REP = 20,000 replicates per cell, split disjointly 50/50 into
    A (SELECT) and B (SCORE).  Identical to f2_boundary_stopped.py, so Gsel
    here reproduces that script's headline grid.
  * seeds 20260801..20260805 (fresh range; the original pipeline used
    0/1/2/42/43/100+/999+ and none of those is reused).
  * sign thresholds on the phase statistic alpha^2 delta^2 / sigma^2 are
    fitted on the EVEN-indexed cells and evaluated on the disjoint ODD cells,
    separately for the one-step label and the oracle-adapts label.

THEORY REFERENCE CURVES EMITTED (predictions under test, never fitted)
  * ``boundary_onestep_exact``   G1_theory = 0, i.e.
        alpha^2 delta^2 (2 - eta alpha^2) = sigma^2 eta,
    which is the EXACT one-step discrete condition Exc(1) < Exc(0) for this
    model (derived from Theorem 1's closed form, not approximated).
  * ``boundary_oracle_exact``    the exact locus where
        min_{0<=t<=T} Exc(t) = Exc(0) = delta^2,
    solved numerically per alpha on the closed-form risk curve.  This is the
    exact finite-horizon boundary of the quantity drawn in panel (ii).
  * ``boundary_derivative_exact`` 2 lambda alpha^2 (delta^2 - nu)
        = (1 - alpha^2) eta^2 sigma^2,  lambda = log(1/(1-eta)),
        nu = eta sigma^2 / (2 - eta)  -- the exact continuous-derivative
    condition.
  * ``boundary_flow``            alpha^2 delta^2 / sigma^2 = eta/2, the
    small-step simplification the published figure overlaid.

REPRODUCTION CHECKS (asserted)
  1. Gora >= -tol at every cell (an oracle with t = 0 on the menu cannot lose).
  2. Gsel <= Gora + tol at every cell (a selected rule cannot beat its oracle
     on the same evaluation half).
  3. On cells where the one-step gain is resolved at 5 Monte-Carlo standard
     errors, its measured sign agrees with the closed-form G1_theory on
     >= 99% of cells.
  4. The oracle boundary computed numerically must bracket the flow boundary
     in the expected direction (exact boundary >= flow boundary at every
     alpha), a consistency check on the two closed forms.
"""
import argparse

import numpy as np

import common as C

N_ALPHA = 25
N_RATIO = 25
N_REP = 20_000           # per cell, split 50/50 SELECT / SCORE


# ----------------------------------------------------------- closed forms
# (reference curves only -- these are the predictions being tested; no
#  headline number in this file is computed from them)

def theory_g1(alpha, delta, sigma, eta):
    """Exact one-step gain Exc(0) - Exc(1) from Theorem 1's closed form."""
    return (2 * eta * alpha ** 2 * delta ** 2
            - eta ** 2 * alpha ** 4 * delta ** 2
            - sigma ** 2 * eta ** 2)


def onestep_boundary_ratio(alpha, sigma, eta):
    """delta/sigma at which the exact one-step gain vanishes, given alpha."""
    denom = alpha ** 2 * (2.0 - eta * alpha ** 2)
    if denom <= 0:
        return np.inf
    return float(np.sqrt(eta / denom))


def derivative_boundary_ratio(alpha, sigma, eta):
    """delta/sigma solving 2 lam a^2 (d^2 - nu) = (1-a^2) eta^2 sigma^2."""
    lam = np.log(1.0 / (1.0 - eta))
    nu = eta * sigma ** 2 / (2.0 - eta)
    if alpha <= 0:
        return np.inf
    d2 = nu + (1 - alpha ** 2) * eta ** 2 * sigma ** 2 / (2 * lam * alpha ** 2)
    return float(np.sqrt(d2) / sigma)


def oracle_boundary_ratio(alpha, sigma, eta, T, lo=1e-3, hi=1e3, iters=200):
    """Exact finite-horizon boundary: delta/sigma where min_t Exc(t) = delta^2.

    Bisection on r = delta/sigma of  f(r) = delta^2 - min_{0<=t<=T} Exc(t),
    which is 0 below the boundary (the oracle declines) and > 0 above it.
    """
    ts = np.arange(0, T + 1)

    def f(r):
        """delta^2 - min_t Exc(t), thresholded at a relative floor.

        Exc(0) is delta^2 only up to rounding -- mean_u(0) evaluates
        delta*(1-alpha^2) + delta*alpha^2, which is not bit-identical to delta
        -- so an untolerated comparison reports a spurious positive gain of
        order 1e-16*delta^2 at cells where the oracle in fact declines, and the
        bisection then converges to the wrong root.
        """
        delta = r * sigma
        risks = C.excess_risk(ts, alpha, delta, sigma, eta)
        gain = delta ** 2 - float(risks.min())
        return gain if gain > 1e-12 * max(delta ** 2, 1.0) else 0.0

    if alpha <= 0:
        return np.inf
    if f(hi) <= 0:
        return np.inf
    a, b = lo, hi
    if f(a) > 0:                       # boundary below the search window
        return float(a)
    for _ in range(iters):
        m = np.sqrt(a * b)             # geometric bisection (log-spaced axis)
        if f(m) > 0:
            b = m
        else:
            a = m
    return float(np.sqrt(a * b))


# --------------------------------------------------------------- measurement

def run_seed(seed, n_rep=N_REP, n_alpha=N_ALPHA, n_ratio=N_RATIO, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    alphas = np.linspace(0.02, 1.0, n_alpha)
    ratios = np.logspace(-1, 1.2, n_ratio)
    half = n_rep // 2
    quarter = half // 2

    shape = (n_alpha, n_ratio)
    (g_one, g_one_se, g_ora, g_ora_se, g_sel, g_sel_se,
     t_ora, t_hat, phase, g_one_th, g_ora_honest) = (
        np.zeros(shape) for _ in range(11))
    t_ora = t_ora.astype(int)
    t_hat = t_hat.astype(int)

    for i, a in enumerate(alphas):
        for j, r in enumerate(ratios):
            delta = r * C.SIGMA
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
            A, B = us[:half], us[half:]
            curve_A = (A ** 2).mean(axis=0)
            curve_B = (B ** 2).mean(axis=0)

            # (a) one-step, scored on B
            g_one[i, j] = delta ** 2 - float(curve_B[1])
            g_one_se[i, j] = C.se_of_mean_square(B[:, 1])

            # (b) TRUE oracle: best step on the evaluation half, t = 0 on menu
            to = int(np.argmin(curve_B))
            t_ora[i, j] = to
            g_ora[i, j] = delta ** 2 - float(curve_B[to])
            g_ora_se[i, j] = C.se_of_mean_square(B[:, to])

            # (b') honest oracle audit: pick on B1, score on disjoint B2.
            #      The gap (b) - (b') is the Monte-Carlo optimism of the
            #      argmin scan; reported, not assumed away.
            B1, B2 = B[:quarter], B[quarter:]
            to_h = int(np.argmin((B1 ** 2).mean(axis=0)))
            g_ora_honest[i, j] = delta ** 2 - float((B2[:, to_h] ** 2).mean())

            # (c) selected stopping: step chosen on A, scored on B
            th = int(np.argmin(curve_A))
            t_hat[i, j] = th
            g_sel[i, j] = delta ** 2 - float(curve_B[th])
            g_sel_se[i, j] = C.se_of_mean_square(B[:, th])

            phase[i, j] = (a * delta / C.SIGMA) ** 2
            g_one_th[i, j] = theory_g1(a, delta, C.SIGMA, C.ETA)
        print(f"[f10 seed {seed}] alpha row {i+1}/{n_alpha}", flush=True)

    # absolute floor: at cells where the rule declines (t = 0) the realized
    # risk is exactly delta^2 (u_0 is deterministic), so the gain is 0 up to
    # float rounding and its Monte-Carlo SE is identically 0.
    scale = (np.asarray(ratios, float) ** 2)[None, :] * np.ones(shape)
    tol = 1e-9 * np.maximum(scale, 1.0)

    sel_err = g_sel - g_ora                     # <= 0 by construction

    # ---- check 1: the oracle cannot lose
    assert (g_ora >= -tol).all(), (
        f"seed {seed}: oracle gain negative at "
        f"{int((g_ora < -tol).sum())} cells (min {g_ora.min():.3e})")
    # ---- check 2: a selected rule cannot beat its own oracle
    assert (sel_err <= tol).all(), (
        f"seed {seed}: selected-stopping gain exceeds the oracle at "
        f"{int((sel_err > tol).sum())} cells (max {sel_err.max():.3e})")

    ph = phase.ravel()
    g1, se1 = g_one.ravel(), g_one_se.ravel()
    gth = g_one_th.ravel()

    # ---- check 3: measured one-step sign vs the closed form, where resolved
    strong = np.abs(g1) > 5.0 * se1
    agree = float((np.sign(g1[strong]) == np.sign(gth[strong])).mean())
    assert agree >= 0.99, (
        f"seed {seed}: measured one-step sign disagrees with the closed form "
        f"on {100*(1-agree):.2f}% of 5-SE-resolved cells")

    # ---- threshold fits (fit on even cells, score on disjoint odd cells)
    lab_one = (g1 > 0).astype(int)
    fit_one, thr_one = C.fit_sign_threshold(ph[::2], lab_one[::2])
    hold_one, n_one = C.eval_sign_threshold(ph[1::2], lab_one[1::2], thr_one)
    res_one = np.abs(g1) > 3.0 * se1
    hold_one_res, n_one_res = C.eval_sign_threshold(
        ph[1::2][res_one[1::2]], lab_one[1::2][res_one[1::2]], thr_one)

    gora = g_ora.ravel()
    tolr = tol.ravel()
    lab_ora = ((gora > tolr) & (t_ora.ravel() > 0)).astype(int)
    fit_ora, thr_ora = C.fit_sign_threshold(ph[::2], lab_ora[::2])
    hold_ora, n_ora = C.eval_sign_threshold(ph[1::2], lab_ora[1::2], thr_ora)

    gsel = g_sel.ravel()
    lab_sel = (gsel > tolr).astype(int)
    fit_sel, thr_sel = C.fit_sign_threshold(ph[::2], lab_sel[::2])
    hold_sel, n_sel = C.eval_sign_threshold(ph[1::2], lab_sel[1::2], thr_sel)

    optimism = float((g_ora - g_ora_honest).mean())
    rel_frozen = scale
    return {
        "seed": seed, "n_rep": n_rep, "T": T, "eta": C.ETA, "sigma": C.SIGMA,
        "grid": [n_alpha, n_ratio],
        "alphas": alphas.tolist(), "ratios": ratios.tolist(),
        "phase_stat": phase.tolist(),

        "gain_onestep": g_one.tolist(), "gain_onestep_se": g_one_se.tolist(),
        "gain_onestep_theory_reference": g_one_th.tolist(),
        "gain_oracle": g_ora.tolist(), "gain_oracle_se": g_ora_se.tolist(),
        "gain_oracle_honest_split": g_ora_honest.tolist(),
        "gain_selected": g_sel.tolist(), "gain_selected_se": g_sel_se.tolist(),
        "selection_error": sel_err.tolist(),
        "t_oracle": t_ora.tolist(), "t_hat_selected": t_hat.tolist(),

        "n_cells": int(g_one.size),
        "n_cells_onestep_negative": int((g1 < 0).sum()),
        "n_cells_onestep_negative_resolved_3se": int((g1 < -3 * se1).sum()),
        "n_cells_oracle_declines": int((t_ora.ravel() == 0).sum()),
        "n_cells_oracle_positive": int((gora > tolr).sum()),
        "n_cells_selected_negative": int((gsel < -tolr).sum()),
        "n_cells_selection_error_nonzero": int((sel_err.ravel() < -tolr).sum()),
        "mean_selection_error": float(sel_err.mean()),
        "mean_selection_error_rel_frozen": float(
            (sel_err / rel_frozen).mean()),
        "worst_selection_error_rel_frozen": float(
            (sel_err / rel_frozen).min()),
        "oracle_mc_optimism_mean": optimism,
        "oracle_mc_optimism_rel_frozen_mean": float(
            ((g_ora - g_ora_honest) / rel_frozen).mean()),

        "fit_accuracy_onestep_even": fit_one,
        "fitted_threshold_onestep": thr_one,
        "threshold_ratio_onestep": thr_one / (C.ETA / 2.0),
        "holdout_accuracy_onestep": hold_one, "n_holdout_onestep": n_one,
        "holdout_accuracy_onestep_resolved": hold_one_res,
        "n_holdout_onestep_resolved": n_one_res,

        "fit_accuracy_oracle_even": fit_ora,
        "fitted_threshold_oracle": thr_ora,
        "threshold_ratio_oracle": thr_ora / (C.ETA / 2.0),
        "holdout_accuracy_oracle": hold_ora, "n_holdout_oracle": n_ora,

        "fit_accuracy_selected_even": fit_sel,
        "fitted_threshold_selected": thr_sel,
        "threshold_ratio_selected": thr_sel / (C.ETA / 2.0),
        "holdout_accuracy_selected": hold_sel, "n_holdout_selected": n_sel,

        "closed_form_sign_agreement_5se": agree,
    }


def theory_curves(alphas, sigma, eta, T):
    """The four reference boundaries, as delta/sigma versus alpha."""
    out = {}
    for name, fn in (
            ("boundary_onestep_exact",
             lambda a: onestep_boundary_ratio(a, sigma, eta)),
            ("boundary_derivative_exact",
             lambda a: derivative_boundary_ratio(a, sigma, eta)),
            ("boundary_oracle_exact",
             lambda a: oracle_boundary_ratio(a, sigma, eta, T)),
            ("boundary_flow",
             lambda a: float(np.sqrt(eta / 2.0) / a) if a > 0 else np.inf)):
        pts = []
        for a in alphas:
            v = fn(float(a))
            if np.isfinite(v):
                pts.append({"alpha": float(a), "delta_over_sigma": float(v)})
        out[name] = pts
    # ---- check 4: the exact finite-horizon boundary sits at or above the
    #      flow boundary (the flow limit is optimistic about when TTT helps)
    ex = {p["alpha"]: p["delta_over_sigma"] for p in out["boundary_oracle_exact"]}
    fl = {p["alpha"]: p["delta_over_sigma"] for p in out["boundary_flow"]}
    bad = [a for a in ex if a in fl and ex[a] < fl[a] * 0.999]
    assert not bad, f"exact oracle boundary below the flow boundary at {bad}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--summary-only", action="store_true",
                    help="rebuild the summary from existing per-seed JSONs")
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        if args.summary_only:
            import json as _json
            import os as _os
            with open(_os.path.join(C.RESULTS_DIR,
                                    f"f10_oracle_grid_seed{s}.json"),
                      encoding="utf-8") as fh:
                r = _json.load(fh)
            per_seed.append(r)
            continue
        r = run_seed(s, args.n_rep)
        C.save(r, f"f10_oracle_grid_seed{s}.json")
        per_seed.append(r)
        print(f"[f10] seed {s}: one-step neg {r['n_cells_onestep_negative']}"
              f"/625 (resolved {r['n_cells_onestep_negative_resolved_3se']}), "
              f"oracle declines {r['n_cells_oracle_declines']}, "
              f"selected neg {r['n_cells_selected_negative']}, "
              f"thr1/{{eta/2}}={r['threshold_ratio_onestep']:.4f}, "
              f"thrO/{{eta/2}}={r['threshold_ratio_oracle']:.4f}", flush=True)

    ref = per_seed[0]
    alphas = np.asarray(ref["alphas"], float)

    def stack(key):
        a = np.stack([np.asarray(r[key], float) for r in per_seed])
        return a.mean(0), a.min(0), a.max(0)

    out = {
        "script": "f10_oracle_grid.py",
        "purpose": ("three-panel Figure 2: "
                    "one-step signed gain, TRUE measured oracle gain, and the "
                    "selected-stopping selection error, all on one simulation"),
        "seeds": args.seeds, "n_rep_per_cell": args.n_rep,
        "eta": C.ETA, "sigma": C.SIGMA, "T": ref["T"],
        "grid": {"alphas": ref["alphas"],
                 "ratios_delta_over_sigma": ref["ratios"],
                 "phase_stat": ref["phase_stat"]},
    }
    for key, label in (("gain_onestep", "gain_onestep"),
                       ("gain_oracle", "gain_oracle"),
                       ("gain_selected", "gain_selected"),
                       ("selection_error", "selection_error")):
        m, lo, hi = stack(key)
        out[label] = {"mean": m.tolist(), "min": lo.tolist(),
                      "max": hi.tolist()}
    out["gain_onestep"]["protocol"] = (
        "delta^2 - E_B[u_1^2] on a held-out replicate half; genuinely signed")
    out["gain_oracle"]["protocol"] = (
        "max_{0<=t<=T} (delta^2 - E_B[u_t^2]); t=0 is on the menu so this is "
        ">= 0 by construction and is reported as such")
    out["gain_selected"]["protocol"] = (
        "delta^2 - E_B[u_{t_hat}^2], t_hat = argmin_t E_A[u_t^2] on the "
        "disjoint SELECT half")
    out["selection_error"]["protocol"] = (
        "gain_selected - gain_oracle, <= 0 identically; this is the entire "
        "content of the negative cells in the published Figure 2")

    scalar_keys = [
        "n_cells_onestep_negative", "n_cells_onestep_negative_resolved_3se",
        "n_cells_oracle_declines", "n_cells_oracle_positive",
        "n_cells_selected_negative", "n_cells_selection_error_nonzero",
        "mean_selection_error", "mean_selection_error_rel_frozen",
        "worst_selection_error_rel_frozen", "oracle_mc_optimism_mean",
        "oracle_mc_optimism_rel_frozen_mean",
        "fitted_threshold_onestep", "threshold_ratio_onestep",
        "holdout_accuracy_onestep", "holdout_accuracy_onestep_resolved",
        "fitted_threshold_oracle", "threshold_ratio_oracle",
        "holdout_accuracy_oracle",
        "fitted_threshold_selected", "threshold_ratio_selected",
        "holdout_accuracy_selected", "closed_form_sign_agreement_5se",
    ]
    for k in scalar_keys:
        out[k] = C.mean_range([r[k] for r in per_seed])

    out["theory_boundaries"] = theory_curves(alphas, C.SIGMA, C.ETA, ref["T"])
    out["theory_boundaries"]["expressions"] = {
        "boundary_onestep_exact":
            "alpha^2 delta^2 (2 - eta alpha^2) = sigma^2 eta   [Exc(1)=Exc(0)]",
        "boundary_derivative_exact":
            "2 log(1/(1-eta)) alpha^2 (delta^2 - eta sigma^2/(2-eta)) "
            "= (1-alpha^2) eta^2 sigma^2",
        "boundary_oracle_exact":
            "min_{0<=t<=T} Exc(t) = delta^2  (solved numerically per alpha)",
        "boundary_flow": "alpha^2 delta^2 / sigma^2 = eta/2",
    }
    C.save(out, "f10_oracle_grid_summary.json")
    print("[f10] DONE", flush=True)


if __name__ == "__main__":
    main()
