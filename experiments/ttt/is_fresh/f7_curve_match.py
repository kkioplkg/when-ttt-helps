"""F7 -- multi-seed confirmation of the E1 risk-curve match (original part a).

CLASSIFICATION OF THE ORIGINAL: run_e1.part_a is MEASURED -- it simulates
trajectories with `simulate_scalar` and compares the empirical risk curve with
the closed form. Nothing is smuggled in. Two things are nonetheless worth
re-doing:

  1. It was run at a single seed (42), like every other E1 gate, so the
     published "worst-case relative error 1.8% over the 30-cell grid" has no
     uncertainty attached.
  2. Its error is normalised by the *global maximum* of the theoretical curve
     for that cell:  max_t |emp(t) - theo(t)| / max_t theo(t).  Since the
     curve's maximum is typically delta^2 (the frozen risk) while the
     interesting region is near the minimum, this normalisation is
     systematically flattering. This script reports it (for comparability with
     the published number) alongside a pointwise-relative error
     max_t |emp(t) - theo(t)| / theo(t) and a Monte-Carlo-standardised error
     max_t |emp(t) - theo(t)| / SE(emp(t)), which is the statistically correct
     way to ask whether the simulation and the closed form agree.

PROTOCOL
  * grid: alpha in {0,0.1,0.25,0.5,0.75,1} x delta/sigma in {0.5,1,2,4,8}
    (the original 30-cell part_a grid), eta = 0.05, sigma = 1, T = 400.
  * N_REP replicates per cell from `simulate_scalar` (original machinery).
  * seeds 20260801..20260805; mean and range over seeds.

REPRODUCTION CHECK (asserted)
The published normalisation must reproduce its gate (worst error < 0.05) at
every fresh seed.
"""
import argparse

import numpy as np

import common as C

N_REP = 40_000


def run_seed(seed, n_rep=N_REP, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    ts = np.arange(T + 1)
    rows = []
    for a in C.ALPHAS:
        for r in C.RATIOS:
            delta = r * C.SIGMA
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
            emp = (us ** 2).mean(axis=0)
            se = (us ** 2).std(axis=0, ddof=1) / np.sqrt(n_rep)
            theo = C.excess_risk(ts, a, delta, C.SIGMA, C.ETA)
            absdiff = np.abs(emp - theo)
            rows.append({
                "alpha": a, "delta": delta,
                "max_rel_err_published_norm": float(
                    absdiff.max() / max(theo.max(), 1e-12)),
                "max_rel_err_pointwise": float(
                    (absdiff / np.maximum(theo, 1e-12)).max()),
                "max_err_in_se_units": float(
                    (absdiff / np.maximum(se, 1e-30)).max()),
                "median_err_in_se_units": float(np.median(
                    absdiff / np.maximum(se, 1e-30))),
            })
    worst_pub = max(x["max_rel_err_published_norm"] for x in rows)
    assert worst_pub < 0.05, (
        f"seed {seed}: published-normalisation gate fails ({worst_pub:.4f})")
    return {"seed": seed, "n_rep": n_rep, "T": T, "n_cells": len(rows),
            "rows": rows,
            "worst_rel_err_published_norm": worst_pub,
            "worst_rel_err_pointwise": max(
                x["max_rel_err_pointwise"] for x in rows),
            "worst_err_in_se_units": max(
                x["max_err_in_se_units"] for x in rows),
            "median_err_in_se_units": float(np.median(
                [x["median_err_in_se_units"] for x in rows])),
            "gate_pass_published_norm": bool(worst_pub < 0.05)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    # A reduced-parameter run (as the release-archive verifier makes) must not
    # be able to overwrite the archived 5-seed / 40,000-replicate records that
    # Sec. 5.1, Table T4 and fig_f1_curves.py all read.
    ap.add_argument("--out-prefix", default="f7_curve_match")
    args = ap.parse_args()
    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_rep)
        C.save(r, f"{args.out_prefix}_seed{s}.json")
        per_seed.append(r)
        print(f"[f7] seed {s}: published-norm {r['worst_rel_err_published_norm']:.4f}, "
              f"pointwise {r['worst_rel_err_pointwise']:.4f}, "
              f"max |err|/SE {r['worst_err_in_se_units']:.2f}", flush=True)
    keys = ["worst_rel_err_published_norm", "worst_rel_err_pointwise",
            "worst_err_in_se_units", "median_err_in_se_units"]
    summary = {"script": "f7_curve_match.py",
               "replaces": "run_e1.part_a at a single seed (42)",
               "seeds": args.seeds, "n_rep_per_cell": args.n_rep,
               "n_cells": per_seed[0]["n_cells"],
               "n_seeds_gate_pass": sum(
                   1 for r in per_seed if r["gate_pass_published_norm"])}
    for k in keys:
        summary[k] = C.mean_range([r[k] for r in per_seed])
    C.save(summary, f"{args.out_prefix}_summary.json")
    print("[f7] DONE", flush=True)


if __name__ == "__main__":
    main()
