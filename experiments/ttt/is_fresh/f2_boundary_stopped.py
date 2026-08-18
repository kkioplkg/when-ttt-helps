"""F2 -- MEASURED phase heatmap for *optimally stopped* TTT (Figure F2's quantity).

REPLACES (analytic original): the gain heatmap of run_e1.part_b, which is
`delta^2 - t_star_theory(...)[1]`, i.e. the paper's own closed form evaluated
at its own argmin. Figure~\\ref{fig:F2}'s caption reads "Color: realized risk
improvement of optimally-stopped TTT over the frozen model" and "TTT helps
above the curve, hurts below". Neither is what part_b computed: the quantity is
analytic (bit-identical across seeds), nothing is realized, and because the
argmin scan includes t = 0 the plotted gain cannot be negative (published grid:
min -1.1e-14, 184/625 cells exactly zero).

WHAT THIS SCRIPT MEASURES INSTEAD
A *realized* optimally-stopped gain with an honest selection/evaluation split:

    SELECT half  ->  t_hat = argmin_{0<=t<=T} mean_A[u_t^2]      (empirical rule)
    SCORE  half  ->  G_stop = delta^2 - mean_B[u_{t_hat}^2]      (realized gain)

u_0 = delta deterministically in this model, so the frozen risk delta^2 is
exact and t_hat = 0 ("decline to adapt") is on the menu. G_stop is therefore
genuinely signed: a cell below the boundary, where every positive step hurts,
still yields G_stop < 0 whenever the noisy SELECT half talks the rule into
adapting. That is the real content of "helps above, hurts below".

PROTOCOL
  * grid: 25 x 25, alpha in linspace(0.02,1,25), delta/sigma in
    logspace(-1,1.2,25); eta = 0.05, sigma = 1, T = 400 (original part_b grid).
  * N_REP replicates per cell from `simulate_scalar` (original machinery),
    split disjointly 50/50 into SELECT and SCORE.
  * sign threshold on the phase statistic alpha^2 delta^2 / sigma^2 fitted on
    EVEN cells, evaluated on the disjoint ODD cells.
  * seeds 20260801..20260805; mean and range over seeds.

REPRODUCTION CHECKS (asserted)
  1. Out-of-sample optimality bound: no cell's realized gain may exceed the
     population optimum delta^2 - min_t Exc(t) by more than 5 standard errors
     (an out-of-sample stopping rule cannot beat the population argmin). This
     is asserted on >= 99% of cells.
  2. The in-sample gain (scored on the SELECT half, the biased quantity the
     original part_f-style code would report) must be >= the out-of-sample
     gain on average -- i.e. the selection bias must have the sign it is
     supposed to have.
"""
import argparse

import numpy as np

import common as C

N_ALPHA = 25
N_RATIO = 25
N_REP = 20_000           # per cell, split 50/50 SELECT / SCORE


def run_seed(seed, n_rep=N_REP, n_alpha=N_ALPHA, n_ratio=N_RATIO, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    alphas = np.linspace(0.02, 1.0, n_alpha)
    ratios = np.logspace(-1, 1.2, n_ratio)
    half = n_rep // 2

    shape = (n_alpha, n_ratio)
    gain_oos = np.zeros(shape)      # realized, scored out of sample
    gain_ins = np.zeros(shape)      # same rule scored in sample (bias probe)
    gain_se = np.zeros(shape)
    t_hat = np.zeros(shape, int)
    t_star = np.zeros(shape, int)
    gain_pop = np.zeros(shape)      # population optimum (reference only)
    phase = np.zeros(shape)

    for i, a in enumerate(alphas):
        for j, r in enumerate(ratios):
            delta = r * C.SIGMA
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
            A, B = us[:half], us[half:]
            curve_A = (A ** 2).mean(axis=0)
            th = int(np.argmin(curve_A))
            uB = B[:, th]
            gain_oos[i, j] = delta ** 2 - float((uB ** 2).mean())
            gain_ins[i, j] = delta ** 2 - float(curve_A[th])
            gain_se[i, j] = C.se_of_mean_square(uB)
            t_hat[i, j] = th
            ts, rs = C.t_star_theory(a, delta, C.SIGMA, C.ETA, T)
            t_star[i, j] = ts
            gain_pop[i, j] = delta ** 2 - rs
            phase[i, j] = (a * delta / C.SIGMA) ** 2
        print(f"[f2 seed {seed}] alpha row {i+1}/{n_alpha}", flush=True)

    # numerical tolerance: at cells where the rule correctly declines
    # (t_hat = 0) the realized risk is exactly delta^2 -- u_0 = delta is
    # deterministic -- so the gain is 0 up to float rounding and its
    # Monte-Carlo SE is identically 0. Compare against an absolute floor.
    scale = (np.asarray(ratios, float) ** 2)[None, :] * np.ones(shape)
    tol = 1e-9 * np.maximum(scale, 1.0)

    ph, g, se = phase.ravel(), gain_oos.ravel(), gain_se.ravel()
    tolr = tol.ravel()
    lab = (g > tolr).astype(int)

    fit_acc, thr = C.fit_sign_threshold(ph[::2], lab[::2])
    hold_acc, n_hold = C.eval_sign_threshold(ph[1::2], lab[1::2], thr)
    resolved = np.abs(g) > np.maximum(3.0 * se, tolr)
    res_odd = resolved[1::2]
    hold_acc_res, n_res = C.eval_sign_threshold(
        ph[1::2][res_odd], lab[1::2][res_odd], thr)

    # ---- check 1: realized gain cannot beat the population optimum
    gp = gain_pop.ravel()
    ok = g <= gp + 5.0 * se + tolr
    frac_ok = float(ok.mean())
    assert frac_ok >= 0.99, (
        f"seed {seed}: realized out-of-sample gain exceeds the population "
        f"optimum by >5 SE on {100*(1-frac_ok):.2f}% of cells")

    # ---- check 2: in-sample selection bias has the expected sign
    bias = float((gain_ins - gain_oos).mean())
    assert bias > 0, (
        f"seed {seed}: in-sample gain is not optimistic relative to the "
        f"held-out gain (mean difference {bias:.3e}) -- split is broken")

    return {
        "seed": seed, "n_rep": n_rep, "T": T, "eta": C.ETA, "sigma": C.SIGMA,
        "grid": [n_alpha, n_ratio],
        "alphas": alphas.tolist(), "ratios": ratios.tolist(),
        "gain_realized_oos": gain_oos.tolist(),
        "gain_in_sample": gain_ins.tolist(),
        "gain_se": gain_se.tolist(),
        "gain_population_optimum_reference": gain_pop.tolist(),
        "t_hat": t_hat.tolist(), "t_star_theory_reference": t_star.tolist(),
        "phase_stat": phase.tolist(),
        "fit_accuracy_even_cells": fit_acc,
        "fitted_threshold": thr,
        "theory_threshold_eta_over_2": C.ETA / 2.0,
        "threshold_ratio": thr / (C.ETA / 2.0),
        "holdout_accuracy_odd_cells": hold_acc, "n_holdout_cells": n_hold,
        "holdout_accuracy_resolved_cells": hold_acc_res,
        "n_holdout_resolved_cells": n_res,
        "frac_cells_resolved_3se": float(resolved.mean()),
        "n_cells_gain_negative": int((g < 0).sum()),
        "n_cells_gain_positive": int((g > 0).sum()),
        "min_gain": float(g.min()), "max_gain": float(g.max()),
        "mean_in_sample_optimism": bias,
        "frac_cells_within_population_optimum": frac_ok,
        "frac_t_hat_zero": float((t_hat.ravel() == 0).mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_rep)
        C.save(r, f"f2_boundary_stopped_seed{s}.json")
        per_seed.append(r)
        print(f"[f2] seed {s}: thr={r['fitted_threshold']:.6f} "
              f"(ratio {r['threshold_ratio']:.4f}) holdout="
              f"{r['holdout_accuracy_odd_cells']:.4f} "
              f"neg_cells={r['n_cells_gain_negative']} "
              f"min_gain={r['min_gain']:.4g}", flush=True)

    summary = {
        "script": "f2_boundary_stopped.py",
        "replaces": "run_e1.part_b gain heatmap / Figure F2",
        "measured_quantity": ("realized optimally-stopped gain "
                              "delta^2 - E_B[u_{t_hat}^2], t_hat selected on a "
                              "disjoint replicate half"),
        "seeds": args.seeds, "n_rep_per_cell": args.n_rep,
        "fitted_threshold": C.mean_range(
            [r["fitted_threshold"] for r in per_seed]),
        "threshold_ratio_vs_eta_over_2": C.mean_range(
            [r["threshold_ratio"] for r in per_seed]),
        "holdout_sign_accuracy_all_cells": C.mean_range(
            [r["holdout_accuracy_odd_cells"] for r in per_seed]),
        "holdout_sign_accuracy_resolved_cells": C.mean_range(
            [r["holdout_accuracy_resolved_cells"] for r in per_seed]),
        "n_cells_gain_negative": C.mean_range(
            [r["n_cells_gain_negative"] for r in per_seed]),
        "min_gain": C.mean_range([r["min_gain"] for r in per_seed]),
        "frac_t_hat_zero": C.mean_range(
            [r["frac_t_hat_zero"] for r in per_seed]),
        "mean_in_sample_optimism": C.mean_range(
            [r["mean_in_sample_optimism"] for r in per_seed]),
    }
    C.save(summary, "f2_boundary_stopped_summary.json")
    print("[f2] DONE", flush=True)


if __name__ == "__main__":
    main()
