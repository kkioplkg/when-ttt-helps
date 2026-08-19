"""F5 -- direct measurement of the sigma^2/N batch law.

WHAT THE PAPER CLAIMS: "Batch adaptation divides the variance term by N:
across N in {1,...,64} the measured variance matches sigma^2/N to a maximum
relative error of 0.35%."

WHAT run_e1.part_f ACTUALLY COMPUTES: no variance at all. It compares
`emp_min_risk = emp.min()` (the minimum of the simulated *risk* curve) with
`theory_min_risk = theo.min()` (the minimum of the closed form at sigma/sqrt(N))
and reports max_rel_err = 0.0035. Two problems: the quantity is a minimum
excess risk, not a variance; and `emp.min()` is an in-sample minimum taken over
the same 12,000 replicates that produced the curve, so it is optimistically
biased.

WHAT THIS SCRIPT MEASURES INSTEAD
Part 1 (the variance claim, direct):
  Var_emp(u_t; N) is estimated across replicates at a set of probe steps and
  compared with the closed-form variance at effective noise sigma/sqrt(N).
  Headline: max relative error over (t, N), reported with the Monte-Carlo
  standard error of the variance estimate itself so the reader can see whether
  a sub-percent claim is even resolvable at this replicate count.
Part 2 (the N-scaling law, closed-form-free):
  N * Var_emp(u_t; N) must be constant in N. Headline: max/min ratio of
  N * Var_emp over N in {1..64} at each probe step -- a pure measurement, with
  no closed form anywhere.
Part 3 (the min-risk quantity part_f actually reported, de-biased):
  t_hat is chosen on a SELECT replicate half and the achieved risk is scored on
  a disjoint SCORE half, so the reported gain is not an in-sample minimum. The
  in-sample number is reported alongside to size the bias that part_f carried.

PROTOCOL
  * alpha = 0.5, delta/sigma = 2, eta = 0.05, sigma = 1, T = 400 (part_f cell).
  * N in {1,2,4,8,16,32,64}; N_REP replicates per N, generated in chunks by
    `simulate_scalar` (original machinery) and accumulated so memory stays
    bounded.
  * probe steps t in {1,2,5,10,20,50,100,200,400}.
  * seeds 20260801..20260805; mean and range.

REPRODUCTION CHECK (asserted)
At N = 1 the measured variance must match the closed form within 6 standard
errors at every probe step (Theorem 1's variance term, reproduced directly).
"""
import argparse

import numpy as np

import common as C

N_REP = 400_000
CHUNK = 25_000
NS = [1, 2, 4, 8, 16, 32, 64]
PROBE_T = [1, 2, 5, 10, 20, 50, 100, 200, 400]
ALPHA = 0.5
RATIO = 2.0


def accumulate(a, delta, N, rng, T, n_rep, chunk=CHUNK):
    """Streamed moments of u_t: returns (mean_t, var_t, mean_sq_t, n)."""
    s1 = np.zeros(T + 1)
    s2 = np.zeros(T + 1)
    done = 0
    while done < n_rep:
        m = min(chunk, n_rep - done)
        us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, m, rng, batch_N=N)
        s1 += us.sum(axis=0)
        s2 += (us ** 2).sum(axis=0)
        done += m
    mean = s1 / n_rep
    msq = s2 / n_rep
    var = msq - mean ** 2
    return mean, var, msq, n_rep


def run_seed(seed, n_rep=N_REP, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    delta = RATIO * C.SIGMA
    per_N = {}
    for N in NS:
        mean, var, msq, n = accumulate(ALPHA, delta, N, rng, T, n_rep)
        theo_var = np.array([C.var_u(t, ALPHA, C.SIGMA / np.sqrt(N), C.ETA)
                             for t in range(T + 1)])
        se_var = var * np.sqrt(2.0 / (n - 1))     # Gaussian approx
        per_N[N] = {"var": var, "theo_var": theo_var, "se_var": se_var,
                    "msq": msq, "mean": mean, "n": n}
        print(f"[f5 seed {seed}] N={N} done", flush=True)

    # ---- Part 1: variance vs closed form at sigma/sqrt(N)
    var_rows, worst = [], 0.0
    for N in NS:
        d = per_N[N]
        for t in PROBE_T:
            v, tv, se = d["var"][t], d["theo_var"][t], d["se_var"][t]
            rel = abs(v - tv) / max(tv, 1e-15)
            worst = max(worst, rel)
            var_rows.append({"N": N, "t": t, "var_measured": float(v),
                             "var_theory_sigma_over_sqrtN": float(tv),
                             "rel_err": float(rel),
                             "mc_rel_se": float(se / max(v, 1e-15))})
    median_mc_rel_se = float(np.median([r["mc_rel_se"] for r in var_rows]))

    # ---- Part 2: N * Var must be constant in N (no closed form)
    scale_rows = []
    for t in PROBE_T:
        vals = [per_N[N]["var"][t] * N for N in NS]
        scale_rows.append({"t": t,
                           "N_times_var": [float(v) for v in vals],
                           "max_min_ratio": float(max(vals) / min(vals))})
    max_scale_ratio = float(max(r["max_min_ratio"] for r in scale_rows))

    # ---- Part 3: min risk with an honest select/score split
    minrisk_rows = []
    for N in NS:
        half = 100_000
        us = C.simulate_scalar(ALPHA, delta, C.SIGMA, C.ETA, T, 2 * half, rng,
                               batch_N=N)
        A, B = us[:half], us[half:]
        cA = (A ** 2).mean(axis=0)
        t_hat = int(np.argmin(cA))
        R_oos = float((B[:, t_hat] ** 2).mean())
        R_ins = float(cA[t_hat])
        R_pop_ref = float(C.excess_risk(
            np.arange(T + 1), ALPHA, delta, C.SIGMA / np.sqrt(N), C.ETA).min())
        minrisk_rows.append({
            "N": N, "t_hat_select_half": t_hat,
            "risk_at_t_hat_scored_oos": R_oos,
            "risk_at_t_hat_in_sample": R_ins,
            "gain_oos": delta ** 2 - R_oos,
            "gain_in_sample": delta ** 2 - R_ins,
            "in_sample_optimism": R_oos - R_ins,
            "population_min_risk_reference": R_pop_ref,
            "rel_err_vs_reference": abs(R_oos - R_pop_ref) / R_pop_ref})
    max_minrisk_rel = float(max(r["rel_err_vs_reference"]
                                for r in minrisk_rows))

    # ---- reproduction check: N=1 variance vs the closed form, 6 SE
    d1 = per_N[1]
    bad = [t for t in PROBE_T
           if abs(d1["var"][t] - d1["theo_var"][t]) > 6.0 * d1["se_var"][t]]
    assert not bad, (
        f"seed {seed}: measured variance at N=1 deviates from the closed form "
        f"by more than 6 SE at steps {bad}")

    return {"seed": seed, "n_rep": n_rep, "T": T, "alpha": ALPHA,
            "delta": delta, "eta": C.ETA, "sigma": C.SIGMA, "Ns": NS,
            "probe_steps": PROBE_T,
            "variance_rows": var_rows,
            "max_rel_err_variance_vs_sigma2_over_N": worst,
            "median_mc_rel_se_of_variance": median_mc_rel_se,
            "n_scaling_rows": scale_rows,
            "max_N_times_var_max_min_ratio": max_scale_ratio,
            "min_risk_rows": minrisk_rows,
            "max_rel_err_min_risk_oos": max_minrisk_rel,
            "mean_in_sample_optimism_min_risk": float(np.mean(
                [r["risk_at_t_hat_in_sample"] - r["risk_at_t_hat_scored_oos"]
                 for r in minrisk_rows]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_rep)
        C.save(r, f"f5_batch_variance_seed{s}.json")
        per_seed.append(r)
        print(f"[f5] seed {s}: max var rel err "
              f"{r['max_rel_err_variance_vs_sigma2_over_N']:.5f} "
              f"(MC SE ~{r['median_mc_rel_se_of_variance']:.5f}); "
              f"N*Var max/min {r['max_N_times_var_max_min_ratio']:.5f}",
              flush=True)

    keys = ["max_rel_err_variance_vs_sigma2_over_N",
            "median_mc_rel_se_of_variance",
            "max_N_times_var_max_min_ratio",
            "max_rel_err_min_risk_oos",
            "mean_in_sample_optimism_min_risk"]
    summary = {"script": "f5_batch_variance.py",
               "replaces": ("run_e1.part_f (min excess risk, in-sample, "
                            "reported as a variance)"),
               "seeds": args.seeds, "n_rep_per_N": args.n_rep, "Ns": NS,
               "probe_steps": PROBE_T}
    for k in keys:
        summary[k] = C.mean_range([r[k] for r in per_seed])
    C.save(summary, "f5_batch_variance_summary.json")
    print("[f5] DONE", flush=True)


if __name__ == "__main__":
    main()
