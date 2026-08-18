"""E1b: Monte Carlo replacements for parts B and C of run_e1.py.

WHY THIS SCRIPT EXISTS
----------------------
run_e1.py parts B and C do not measure what an E1 sign-prediction test and an
E1 stopping test have to measure to be evidence for anything.

  part_b builds its gains from t_star_theory() and excess_risk(), labels those
  same analytic values, and then splits the grid into fitted and held-out
  halves. Its `rng` argument is never used: no stochastic trajectory is ever
  generated. Held-out accuracy 1.00 is therefore a deterministic consequence of
  the theorem being tested, not evidence for it.

  part_c selects the stopping step from a simulated risk curve, which is
  genuinely empirical, but then evaluates the risk achieved at that step with
  the analytic formula rather than from the simulation.

This script redoes both honestly, with three properties the originals lacked.

  1. Every gain and every achieved risk comes from simulated trajectories.
  2. Selection and evaluation use DISJOINT replicate sets. Taking the minimum
     of a noisy risk curve and reporting that minimum is optimistically biased,
     which would manufacture positive gains in cells where none exist; here the
     step is chosen on one half of the replicates and scored on the other.
  3. Everything is repeated over independent simulation seeds, so the reported
     accuracies carry a spread instead of a single deterministic number.

The closed form is still used for ONE thing: as the theoretical reference the
measured quantities are compared against. It never supplies a measured value.

Outputs e1b_montecarlo.json next to the other e1 results.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_e1 import (ETA, SIGMA, T, excess_risk,  # noqa: E402
                    simulate_scalar, t_star_theory)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "results", "e1")

# Part B grid, unchanged from run_e1.part_b so the comparison is like for like.
ALPHAS_B = np.linspace(0.02, 1.0, 25)
RATIOS_B = np.logspace(-1, 1.2, 25)

# Replicates per cell, split in half for selection and evaluation.
NREP_B = 24000
NREP_C = 24000
SEEDS = (20260731, 20260732, 20260733, 20260734, 20260735)


def split_halves(us):
    """Disjoint selection and evaluation replicate sets."""
    n = us.shape[0] // 2
    return us[:n], us[n:]


def measured_gain(alpha, delta, eta, sigma, horizon, n_rep, rng):
    """Empirical best-step gain with honest selection/evaluation separation.

    Returns (gain, t_hat, risk0_eval, risk_at_that_step_eval). The step is the
    argmin of the SELECTION half's risk curve; the gain is measured on the
    EVALUATION half at that step, against the evaluation half's own risk at
    t = 0. Both halves come from the same simulation call and are disjoint.
    """
    us = simulate_scalar(alpha, delta, sigma, eta, horizon, n_rep, rng)
    sel, ev = split_halves(us)
    sel_curve = (sel ** 2).mean(axis=0)
    ev_curve = (ev ** 2).mean(axis=0)
    t_hat = int(np.argmin(sel_curve))
    return (float(ev_curve[0] - ev_curve[t_hat]), t_hat,
            float(ev_curve[0]), float(ev_curve[t_hat]))


def fit_threshold(ph, lb):
    """Best single-threshold sign classifier, ties broken at the lowest cut."""
    ph = np.asarray(ph, dtype=float)
    lb = np.asarray(lb, dtype=int)
    order = np.argsort(ph, kind="stable")
    ph_s, lb_s = ph[order], lb[order]
    n = len(ph_s)
    zeros_prefix = np.concatenate(([0], np.cumsum(lb_s == 0)))
    ones_total = int((lb_s == 1).sum())
    ones_prefix = np.concatenate(([0], np.cumsum(lb_s == 1)))
    correct = zeros_prefix + (ones_total - ones_prefix)
    k = int(np.argmax(correct))
    return float(correct[k]) / n, (float(ph_s[k - 1]) if k > 0 else 0.0)


def part_b_montecarlo(seed, horizon=T):
    """Sign prediction from SIMULATED gains, fitted and held out on disjoint
    halves of the (alpha, delta/sigma) grid."""
    rng = np.random.default_rng(seed)
    phase, gains, thats = [], [], []
    for a in ALPHAS_B:
        for r in RATIOS_B:
            delta = r * SIGMA
            g, t_hat, _, _ = measured_gain(a, delta, ETA, SIGMA, horizon,
                                           NREP_B, rng)
            phase.append((a * delta / SIGMA) ** 2)
            gains.append(g)
            thats.append(t_hat)
    phase = np.asarray(phase)
    gains = np.asarray(gains)
    lab = (gains > 0).astype(int)
    fit_acc, thr = fit_threshold(phase[::2], lab[::2])
    hold_pred = (phase[1::2] > thr).astype(int)
    hold_acc = float((hold_pred == lab[1::2]).mean())
    # The analytic labels the superseded part_b used, for the delta.
    an_lab = []
    for a in ALPHAS_B:
        for r in RATIOS_B:
            delta = r * SIGMA
            _, risk = t_star_theory(a, delta, SIGMA, ETA, horizon)
            an_lab.append(int(delta ** 2 - risk > 1e-9))
    an_lab = np.asarray(an_lab)
    return {
        "seed": int(seed),
        "n_cells": int(len(lab)),
        "n_positive_measured": int(lab.sum()),
        "n_positive_analytic": int(an_lab.sum()),
        "measured_vs_analytic_label_agreement":
            float((lab == an_lab).mean()),
        "fit_accuracy": fit_acc,
        "fitted_threshold": thr,
        "holdout_accuracy": hold_acc,
        "mean_selected_step": float(np.mean(thats)),
    }


def part_c_montecarlo(seed, horizon=T):
    """Achieved risk at the empirically selected step, measured on held-out
    replicates rather than read off the closed form."""
    rng = np.random.default_rng(seed)
    rows = []
    for a in (0.1, 0.25, 0.5, 0.75, 1.0):
        for r in (0.5, 1.0, 2.0, 4.0, 8.0):
            delta = r * SIGMA
            t_star, risk_star = t_star_theory(a, delta, SIGMA, ETA, horizon)
            us = simulate_scalar(a, delta, SIGMA, ETA, horizon, NREP_C, rng)
            sel, ev = split_halves(us)
            t_hat = int(np.argmin((sel ** 2).mean(axis=0)))
            ev_curve = (ev ** 2).mean(axis=0)
            achieved = float(ev_curve[t_hat])
            at_theory_step = float(ev_curve[t_star])
            rows.append({
                "alpha": a, "delta_over_sigma": r,
                "t_star_theory": t_star, "t_hat_measured": t_hat,
                "risk_star_theory": risk_star,
                "risk_at_t_hat_measured": achieved,
                "risk_at_t_star_measured": at_theory_step,
                # Excess of the measured achieved risk over the theoretical
                # optimum, as a fraction of the theoretical optimum.
                "relative_excess_vs_theory":
                    float((achieved - risk_star) / max(risk_star, 1e-12)),
                # Measured-against-measured: how much worse the empirically
                # chosen step is than the theoretically chosen step, both
                # scored on the same held-out replicates.
                "relative_excess_vs_theory_step":
                    float((achieved - at_theory_step)
                          / max(at_theory_step, 1e-12)),
            })
    rel = np.array([r["relative_excess_vs_theory"] for r in rows])
    rel_step = np.array([r["relative_excess_vs_theory_step"] for r in rows])
    return {
        "seed": int(seed), "n_cells": len(rows), "rows": rows,
        "max_relative_excess_vs_theory": float(rel.max()),
        "median_relative_excess_vs_theory": float(np.median(rel)),
        "max_relative_excess_vs_theory_step": float(rel_step.max()),
        "median_relative_excess_vs_theory_step": float(np.median(rel_step)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=len(SEEDS))
    args = ap.parse_args()
    seeds = SEEDS[:args.seeds]

    b = [part_b_montecarlo(s) for s in seeds]
    for r in b:
        print(f"[B seed {r['seed']}] measured positives "
              f"{r['n_positive_measured']}/{r['n_cells']} "
              f"(analytic {r['n_positive_analytic']}), label agreement "
              f"{r['measured_vs_analytic_label_agreement']:.4f}, "
              f"fit {r['fit_accuracy']:.4f}, holdout "
              f"{r['holdout_accuracy']:.4f}", flush=True)
    hold = np.array([r["holdout_accuracy"] for r in b])
    agree = np.array([r["measured_vs_analytic_label_agreement"] for r in b])

    c = [part_c_montecarlo(s) for s in seeds]
    for r in c:
        print(f"[C seed {r['seed']}] max relative excess vs theory "
              f"{r['max_relative_excess_vs_theory']:.4f}, vs theory-step "
              f"{r['max_relative_excess_vs_theory_step']:.4f}", flush=True)
    cmax = np.array([r["max_relative_excess_vs_theory"] for r in c])
    cmax_step = np.array([r["max_relative_excess_vs_theory_step"]
                          for r in c])

    out = {
        "purpose": "Monte Carlo replacements for run_e1.py parts B and C, "
                   "whose gains and achieved risks were computed from the "
                   "closed form rather than from simulated trajectories",
        "config": {"eta": ETA, "sigma": SIGMA, "horizon": T,
                   "n_rep_b": NREP_B, "n_rep_c": NREP_C,
                   "seeds": list(seeds),
                   "selection_evaluation_split": "disjoint halves of the "
                                                 "replicate set; the step is "
                                                 "chosen on one half and "
                                                 "scored on the other"},
        "part_b": b,
        "part_b_summary": {
            "holdout_accuracy_mean": float(hold.mean()),
            "holdout_accuracy_min": float(hold.min()),
            "holdout_accuracy_max": float(hold.max()),
            "label_agreement_with_analytic_mean": float(agree.mean()),
            "label_agreement_with_analytic_min": float(agree.min()),
        },
        "part_c": c,
        "part_c_summary": {
            "max_relative_excess_vs_theory_worst_seed": float(cmax.max()),
            "max_relative_excess_vs_theory_mean": float(cmax.mean()),
            "max_relative_excess_vs_theory_step_worst_seed":
                float(cmax_step.max()),
            "max_relative_excess_vs_theory_step_mean":
                float(cmax_step.mean()),
        },
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "e1b_montecarlo.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"\nholdout accuracy over {len(seeds)} seeds: "
          f"mean {hold.mean():.4f}, range [{hold.min():.4f}, "
          f"{hold.max():.4f}]")
    print(f"measured-vs-analytic label agreement: mean {agree.mean():.4f}, "
          f"min {agree.min():.4f}")
    print(f"part C max relative excess vs theory: worst seed "
          f"{cmax.max():.4f}; vs theory step: worst seed "
          f"{cmax_step.max():.4f}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
