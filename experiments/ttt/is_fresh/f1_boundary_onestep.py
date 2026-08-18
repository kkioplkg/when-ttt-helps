"""F1 -- MEASURED phase boundary from a one-step adaptation gain.

REPLACES (analytic original): run_e1.part_b, which built its whole gain grid
from `t_star_theory`/`excess_risk` -- the paper's own closed forms -- and never
touched its `rng` argument. Two facts make that grid a self-check rather than
evidence:
  * it is bit-identical for every seed (verified: seeds 42 and 20260801 give
    the same fitted threshold 0.025044195974408885);
  * because the argmin scan includes t = 0, its "gain" delta^2 - min_t E(t) is
    >= 0 by construction. In the published grid the minimum gain is -1.1e-14
    and 184 of 625 cells are exactly 0. The reported "sign accuracy 1.00" is
    therefore the accuracy of predicting "is the closed-form argmin strictly
    positive", at a 1e-9 tolerance -- not "does TTT help or hurt".

WHAT THIS SCRIPT MEASURES INSTEAD
The paper's boundary alpha^2 delta^2 / sigma^2 = eta/2 is the small-step /
flow-limit statement that the risk *starts* decreasing at t = 0. The directly
measurable, sign-flipping version of that is the one-step gain

    G1(alpha, delta) = delta^2 - E[u_1^2],

estimated by Monte-Carlo from simulated trajectories (`simulate_scalar`, the
original machinery). u_0 = delta holds deterministically in this model, so the
frozen risk delta^2 needs no estimate and G1 is genuinely signed: cells below
the boundary give G1 < 0 (adaptation hurts), cells above give G1 > 0.

PROTOCOL
  * grid: alpha in linspace(0.02, 1, 25) x delta/sigma in logspace(-1, 1.2, 25)
    (the original part_b grid), eta = 0.05, sigma = 1.
  * per cell: N_REP independent replicates, split into a disjoint SELECT half
    and SCORE half. Nothing is selected here (t = 1 is fixed), so the split is
    used only to report an independent replication of each cell's sign; the
    headline gain and its standard error come from the SCORE half.
  * label = sign of the measured G1 on the SCORE half.
  * threshold: fitted on the EVEN-indexed cells, evaluated on the disjoint
    ODD-indexed cells (cell-level holdout, as in the original).
  * seeds: 20260801..20260805 (five independent replications); mean and range.
  * "resolved" cells = |G1| > 3 * SE(G1); reported separately because near the
    boundary the true gain is ~0 and its measured sign is Monte-Carlo noise,
    not a model failure.

REPRODUCTION CHECK (asserted)
The closed form gives E(1) - E(0) = -2 eta alpha^2 delta^2 + eta^2 alpha^4
delta^2 + sigma^2 eta^2, i.e. G1_theory = -(that). On cells where the
measured gain is resolved at 5 SE, the measured sign must agree with the
closed-form sign; the script asserts >= 99% agreement there. This is the one
place a closed form is used, and it is used as a check, not as a number.
"""
import argparse

import numpy as np

import common as C

N_ALPHA = 25
N_RATIO = 25
N_REP = 400_000          # per cell, split 50/50 into SELECT / SCORE


def theory_g1(alpha, delta, sigma, eta):
    """Closed-form one-step gain; REFERENCE ONLY (reproduction check)."""
    return (2 * eta * alpha ** 2 * delta ** 2
            - eta ** 2 * alpha ** 4 * delta ** 2
            - sigma ** 2 * eta ** 2)


def run_seed(seed, n_rep=N_REP):
    rng = np.random.default_rng(seed)
    alphas = np.linspace(0.02, 1.0, N_ALPHA)
    ratios = np.logspace(-1, 1.2, N_RATIO)
    half = n_rep // 2

    gain, gain_se, gain_sel, phase, gain_th = (
        np.zeros((N_ALPHA, N_RATIO)) for _ in range(5))
    for i, a in enumerate(alphas):
        for j, r in enumerate(ratios):
            delta = r * C.SIGMA
            # T = 1: only the first adaptation step is needed
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, 1, n_rep, rng)
            u1 = us[:, 1]
            u1_sel, u1_sco = u1[:half], u1[half:]
            gain[i, j] = delta ** 2 - float((u1_sco ** 2).mean())
            gain_sel[i, j] = delta ** 2 - float((u1_sel ** 2).mean())
            gain_se[i, j] = C.se_of_mean_square(u1_sco)
            phase[i, j] = (a * delta / C.SIGMA) ** 2
            gain_th[i, j] = theory_g1(a, delta, C.SIGMA, C.ETA)
        print(f"[f1 seed {seed}] alpha row {i+1}/{N_ALPHA}", flush=True)

    ph = phase.ravel()
    g = gain.ravel()
    se = gain_se.ravel()
    lab = (g > 0).astype(int)
    lab_sel = (gain_sel.ravel() > 0).astype(int)
    gth = gain_th.ravel()

    # cell-level holdout: fit on even cells, evaluate on odd cells
    fit_acc, thr = C.fit_sign_threshold(ph[::2], lab[::2])
    hold_acc, n_hold = C.eval_sign_threshold(ph[1::2], lab[1::2], thr)

    resolved = np.abs(g) > 3.0 * se
    res_odd = resolved[1::2]
    hold_acc_res, n_res = C.eval_sign_threshold(
        ph[1::2][res_odd], lab[1::2][res_odd], thr)

    # ---- reproduction check against the closed form on well-resolved cells
    strong = np.abs(g) > 5.0 * se
    agree = float((np.sign(g[strong]) == np.sign(gth[strong])).mean())
    assert agree >= 0.99, (
        f"measured one-step gain sign disagrees with the closed form on "
        f"{100*(1-agree):.2f}% of 5-SE-resolved cells (seed {seed})")

    # split-half stability of the measured labels (independent replicate half)
    split_agree = float((lab == lab_sel).mean())
    split_agree_res = float((lab[resolved] == lab_sel[resolved]).mean())

    return {
        "seed": seed, "n_rep": n_rep, "n_rep_score_half": n_rep - half,
        "eta": C.ETA, "sigma": C.SIGMA, "grid": [N_ALPHA, N_RATIO],
        "alphas": alphas.tolist(), "ratios": ratios.tolist(),
        "gain_measured": gain.tolist(), "gain_se": gain_se.tolist(),
        "phase_stat": phase.tolist(),
        "fit_accuracy_even_cells": fit_acc,
        "fitted_threshold": thr,
        "theory_threshold_eta_over_2": C.ETA / 2.0,
        "threshold_ratio": thr / (C.ETA / 2.0),
        "holdout_accuracy_odd_cells": hold_acc,
        "n_holdout_cells": n_hold,
        "holdout_accuracy_resolved_cells": hold_acc_res,
        "n_holdout_resolved_cells": n_res,
        "frac_cells_resolved_3se": float(resolved.mean()),
        "n_cells_gain_negative": int((g < 0).sum()),
        "n_cells_gain_positive": int((g > 0).sum()),
        "split_half_label_agreement": split_agree,
        "split_half_label_agreement_resolved": split_agree_res,
        "closed_form_sign_agreement_5se": agree,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_rep)
        C.save(r, f"f1_boundary_onestep_seed{s}.json")
        per_seed.append(r)
        print(f"[f1] seed {s}: thr={r['fitted_threshold']:.6f} "
              f"(ratio {r['threshold_ratio']:.4f}), holdout="
              f"{r['holdout_accuracy_odd_cells']:.4f}, "
              f"resolved-holdout={r['holdout_accuracy_resolved_cells']:.4f}",
              flush=True)

    summary = {
        "script": "f1_boundary_onestep.py",
        "replaces": "run_e1.part_b (analytic gain grid, seed-independent)",
        "measured_quantity": "one-step gain G1 = delta^2 - E[u_1^2]",
        "seeds": args.seeds, "n_rep_per_cell": args.n_rep,
        "fitted_threshold": C.mean_range(
            [r["fitted_threshold"] for r in per_seed]),
        "threshold_ratio_vs_eta_over_2": C.mean_range(
            [r["threshold_ratio"] for r in per_seed]),
        "holdout_sign_accuracy_all_cells": C.mean_range(
            [r["holdout_accuracy_odd_cells"] for r in per_seed]),
        "holdout_sign_accuracy_resolved_cells": C.mean_range(
            [r["holdout_accuracy_resolved_cells"] for r in per_seed]),
        "frac_cells_resolved_3se": C.mean_range(
            [r["frac_cells_resolved_3se"] for r in per_seed]),
        "n_cells_gain_negative": C.mean_range(
            [r["n_cells_gain_negative"] for r in per_seed]),
        "split_half_label_agreement": C.mean_range(
            [r["split_half_label_agreement"] for r in per_seed]),
        "closed_form_sign_agreement_5se": C.mean_range(
            [r["closed_form_sign_agreement_5se"] for r in per_seed]),
    }
    C.save(summary, "f1_boundary_onestep_summary.json")
    print("[f1] DONE", flush=True)


if __name__ == "__main__":
    main()
