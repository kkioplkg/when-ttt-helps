"""F3 -- MEASURED optimal stopping: is the risk at the empirical stop near optimal?

REPLACES (analytic scoring): run_e1.part_c. That part does select its stopping
step empirically (argmin of a simulated risk curve) but then scores it with

    risk_at_emp_t = excess_risk(emp_t, alpha, delta, sigma, eta)

i.e. the paper's own closed form evaluated at the selected step, compared to
the closed form's own minimum. Two consequences: (i) the reported "risk at the
empirical argmin is within 5% of the theoretical minimum in 100% of cells" is a
statement about the flatness of a closed-form curve, not about any achieved
risk; (ii) whenever the empirical argmin happens to equal the theoretical one
the gap is exactly 0.0 by construction (it is 0.0 in the published JSON for
most cells). The companion "88% of cells within a factor two of t*" is measured
on the selection side but is scored against the theoretical t*, and the argmin
is taken on the same replicates it is judged with.

WHAT THIS SCRIPT MEASURES INSTEAD
Three disjoint replicate blocks per cell:

    A (SELECT)  t_emp = argmin_t mean_A[u_t^2]      the empirical stopping rule
    C (ORACLE)  t_ora = argmin_t mean_C[u_t^2]      an INDEPENDENT estimate of
                                                    the true optimal step
    B (SCORE)   both are scored: R_emp = mean_B[u_{t_emp}^2],
                                 R_ora = mean_B[u_{t_ora}^2]

Headline: frac of cells with R_emp <= 1.05 * R_ora (achieved-risk near-
optimality, everything measured), and frac of cells with t_emp within a factor
two of the measured t_ora (time agreement, everything measured). The
theory-referenced versions are reported alongside for continuity, clearly
labelled.

PROTOCOL
  * cells: alpha in {0.1,0.25,0.5,0.75,1.0} x delta/sigma in {0.5,1,2,4,8}
    (the original part_c grid), eta = 0.05, sigma = 1, T = 400.
  * N_REP replicates per cell from `simulate_scalar`, split into three equal
    disjoint blocks A / B / C.
  * seeds 20260801..20260805, mean and range.

REPRODUCTION CHECK (asserted)
The measured risk at the oracle step must agree with the closed form
Exc(t_ora) within 5 standard errors on at least 90% of cells -- Theorem 1's
curve reproduced at the point that matters. Closed forms are used only here.
"""
import argparse

import numpy as np

import common as C

N_REP = 60_000            # per cell, split into 3 disjoint blocks of 20k


def run_seed(seed, n_rep=N_REP, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    blk = n_rep // 3
    rows = []
    n_curve_ok = 0
    for a in C.ALPHAS[1:]:
        for r in C.RATIOS:
            delta = r * C.SIGMA
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, 3 * blk, rng)
            A, B, Cc = us[:blk], us[blk:2 * blk], us[2 * blk:]
            t_emp = int(np.argmin((A ** 2).mean(axis=0)))
            t_ora = int(np.argmin((Cc ** 2).mean(axis=0)))
            uB_emp, uB_ora = B[:, t_emp], B[:, t_ora]
            R_emp = float((uB_emp ** 2).mean())
            R_ora = float((uB_ora ** 2).mean())
            se_ora = C.se_of_mean_square(uB_ora)
            # theory references (NOT used for the headline numbers)
            t_th, R_th = C.t_star_theory(a, delta, C.SIGMA, C.ETA, T)
            R_th_at_ora = float(C.excess_risk(t_ora, a, delta, C.SIGMA, C.ETA))
            curve_ok = abs(R_ora - R_th_at_ora) <= 5.0 * se_ora
            n_curve_ok += int(curve_ok)
            rows.append({
                "alpha": a, "delta": delta,
                "t_emp_select_block": t_emp,
                "t_oracle_independent_block": t_ora,
                "t_star_theory_reference": t_th,
                "risk_at_t_emp_scored": R_emp,
                "risk_at_t_oracle_scored": R_ora,
                "risk_se": se_ora,
                "rel_gap_measured": (R_emp - R_ora) / max(R_ora, 1e-12),
                "risk_star_theory_reference": R_th,
                "rel_gap_vs_theory_reference": (
                    (R_emp - R_th) / max(R_th, 1e-12)),
                "curve_matches_theory_5se": bool(curve_ok),
            })
    n = len(rows)
    frac_risk_5pct = sum(
        1 for x in rows if x["rel_gap_measured"] <= 0.05) / n
    frac_risk_5pct_theory = sum(
        1 for x in rows
        if abs(x["rel_gap_vs_theory_reference"]) <= 0.05) / n

    def within2x(t1, t2):
        t1, t2 = max(t1, 1), max(t2, 1)
        return t2 / 2 <= t1 <= t2 * 2

    frac_time_2x = sum(
        1 for x in rows
        if within2x(x["t_emp_select_block"],
                    x["t_oracle_independent_block"])) / n
    frac_time_2x_theory = sum(
        1 for x in rows
        if within2x(x["t_emp_select_block"],
                    x["t_star_theory_reference"])) / n

    frac_curve_ok = n_curve_ok / n
    assert frac_curve_ok >= 0.90, (
        f"seed {seed}: measured risk at the oracle step matches the closed "
        f"form within 5 SE in only {100*frac_curve_ok:.0f}% of cells")

    return {"seed": seed, "n_rep": n_rep, "block_size": blk, "T": T,
            "n_cells": n, "rows": rows,
            "frac_risk_within_5pct_of_measured_oracle": frac_risk_5pct,
            "frac_time_within_2x_of_measured_oracle": frac_time_2x,
            "frac_risk_within_5pct_of_theory_reference": frac_risk_5pct_theory,
            "frac_time_within_2x_of_theory_reference": frac_time_2x_theory,
            "median_rel_gap_measured": float(np.median(
                [x["rel_gap_measured"] for x in rows])),
            "max_rel_gap_measured": float(np.max(
                [x["rel_gap_measured"] for x in rows])),
            "frac_curve_matches_theory_5se": frac_curve_ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_rep)
        C.save(r, f"f3_optimal_stopping_seed{s}.json")
        per_seed.append(r)
        print(f"[f3] seed {s}: risk<=1.05x measured oracle in "
              f"{r['frac_risk_within_5pct_of_measured_oracle']:.2f}; "
              f"time within 2x in "
              f"{r['frac_time_within_2x_of_measured_oracle']:.2f}", flush=True)

    keys = ["frac_risk_within_5pct_of_measured_oracle",
            "frac_time_within_2x_of_measured_oracle",
            "frac_risk_within_5pct_of_theory_reference",
            "frac_time_within_2x_of_theory_reference",
            "median_rel_gap_measured", "max_rel_gap_measured",
            "frac_curve_matches_theory_5se"]
    summary = {"script": "f3_optimal_stopping.py",
               "replaces": "run_e1.part_c (risk scored with the closed form)",
               "seeds": args.seeds, "n_rep_per_cell": args.n_rep,
               "n_cells": per_seed[0]["n_cells"]}
    for k in keys:
        summary[k] = C.mean_range([r[k] for r in per_seed])
    C.save(summary, "f3_optimal_stopping_summary.json")
    print("[f3] DONE", flush=True)


if __name__ == "__main__":
    main()
