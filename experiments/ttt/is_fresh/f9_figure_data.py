"""F9 -- consolidated data for regenerating Figure 2 (phase diagram) from
MEASURED gains.

The published F2_phase.pdf overlays a "fitted" boundary that came from
run_e1.part_b, i.e. from the paper's own closed forms (see f1/f2 docstrings).
This script collects the fresh, measured replacements into one compact JSON so
the figure track can redraw the panel without touching any analytic quantity.

Contents of the emitted file:
  grid                alphas (25) and delta/sigma ratios (25) -- the original
                      part_b grid
  gain_onestep        MEASURED one-step gain delta^2 - E[u_1^2], mean over the
                      five fresh seeds, and its across-seed range. This is the
                      genuinely signed quantity and the recommended heatmap
                      colour: it is negative below the boundary and positive
                      above it.
  gain_stopped        MEASURED realized gain of optimally-stopped TTT with the
                      stopping step selected on a disjoint replicate half.
                      Non-negative wherever the rule correctly declines to
                      adapt (t_hat = 0), negative where selection error makes
                      it adapt when it should not.
  boundary_theory     the curve alpha^2 delta^2 / sigma^2 = eta/2, eta = 0.05
  boundary_fitted     the measured single-threshold fit, per seed and pooled
  holdout             per-seed holdout sign accuracies (all cells, and cells
                      resolved at 3 Monte-Carlo standard errors)

Every number here carries its seed list and protocol string; nothing in this
file is computed from a closed form except `boundary_theory`, which is the
prediction being tested and is labelled as such.
"""
import glob
import json
import os

import numpy as np

import common as C


def load(pattern):
    out = {}
    for p in sorted(glob.glob(os.path.join(C.RESULTS_DIR, pattern))):
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        out[o["seed"]] = o
    return out


def stack(objs, key):
    a = np.stack([np.asarray(o[key], float) for o in objs.values()])
    return a.mean(axis=0), a.min(axis=0), a.max(axis=0)


def main():
    one = load("f1_boundary_onestep_seed*.json")
    stop = load("f2_boundary_stopped_seed*.json")
    assert one, "f1 outputs missing -- run f1_boundary_onestep.py first"
    assert stop, "f2 outputs missing -- run f2_boundary_stopped.py first"

    ref = next(iter(one.values()))
    g1_m, g1_lo, g1_hi = stack(one, "gain_measured")
    gs_m, gs_lo, gs_hi = stack(stop, "gain_realized_oos")

    out = {
        "note": ("measured replacements for the Figure 2 phase diagram; the "
                 "published panel was drawn from run_e1.part_b, which "
                 "computes its gain grid from the paper's own closed forms "
                 "and is bit-identical for every seed"),
        "eta": C.ETA, "sigma": C.SIGMA, "T": C.T,
        "grid": {"alphas": ref["alphas"], "ratios_delta_over_sigma": ref["ratios"],
                 "phase_stat": ref["phase_stat"]},
        "gain_onestep": {
            "protocol": ("delta^2 - E[u_1^2] measured on a held-out replicate "
                         "half of simulate_scalar trajectories; genuinely "
                         "signed (u_0 = delta is deterministic, so the frozen "
                         "risk needs no estimate)"),
            "seeds": sorted(one), "n_rep_per_cell": ref["n_rep"],
            "mean": g1_m.tolist(), "min": g1_lo.tolist(), "max": g1_hi.tolist(),
            "fitted_threshold_by_seed": {str(s): one[s]["fitted_threshold"]
                                         for s in sorted(one)},
            "threshold_ratio_by_seed": {str(s): one[s]["threshold_ratio"]
                                        for s in sorted(one)},
            "holdout_accuracy_by_seed": {
                str(s): one[s]["holdout_accuracy_odd_cells"]
                for s in sorted(one)},
            "holdout_accuracy_resolved_by_seed": {
                str(s): one[s]["holdout_accuracy_resolved_cells"]
                for s in sorted(one)},
            "fitted_threshold_pooled": C.mean_range(
                [one[s]["fitted_threshold"] for s in sorted(one)]),
            "holdout_accuracy_pooled": C.mean_range(
                [one[s]["holdout_accuracy_odd_cells"] for s in sorted(one)]),
        },
        "gain_stopped": {
            "protocol": ("delta^2 - E_B[u_{t_hat}^2] with t_hat = argmin of "
                         "the risk curve on a DISJOINT replicate half A; "
                         "t_hat = 0 (decline to adapt) is on the menu"),
            "seeds": sorted(stop), "n_rep_per_cell":
                next(iter(stop.values()))["n_rep"],
            "mean": gs_m.tolist(), "min": gs_lo.tolist(), "max": gs_hi.tolist(),
            "fitted_threshold_by_seed": {str(s): stop[s]["fitted_threshold"]
                                         for s in sorted(stop)},
            "threshold_ratio_by_seed": {str(s): stop[s]["threshold_ratio"]
                                        for s in sorted(stop)},
            "holdout_accuracy_by_seed": {
                str(s): stop[s]["holdout_accuracy_odd_cells"]
                for s in sorted(stop)},
            "n_cells_gain_negative_by_seed": {
                str(s): stop[s]["n_cells_gain_negative"] for s in sorted(stop)},
            "fitted_threshold_pooled": C.mean_range(
                [stop[s]["fitted_threshold"] for s in sorted(stop)]),
            "holdout_accuracy_pooled": C.mean_range(
                [stop[s]["holdout_accuracy_odd_cells"] for s in sorted(stop)]),
        },
        "boundary_theory": {
            "expression": "alpha^2 delta^2 / sigma^2 = eta/2",
            "value": C.ETA / 2.0,
            "label": "prediction under test (closed form), not a measurement",
            "curve_delta_over_sigma_vs_alpha": [
                {"alpha": float(a),
                 "delta_over_sigma": float(np.sqrt(C.ETA / 2.0) / a)}
                for a in ref["alphas"] if a > 0],
        },
    }
    C.save(out, "f9_phase_figure_data.json")
    print("[f9] DONE", flush=True)


if __name__ == "__main__":
    main()
