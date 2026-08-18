"""F4 -- ALTA scored against a MEASURED oracle instead of the closed-form one.

CLASSIFICATION OF THE ORIGINAL: run_e1.part_d is SEMI-ANALYTIC. Its numerator
is genuinely measured -- ALTA is really run on K=3 simulated replica
trajectories and the realized risk is E[u_hat^2] at the stopping step. But its
denominator is not: `risk_star` comes from `t_star_theory`, the paper's own
closed form. Every published ratio ("median risk ratios against the oracle
range from 0.99 to 1.37 ... drop to 0.29-0.38 at alpha=1", "p90 within the
bound in 16 of 16 cells") is therefore measured-over-analytic, and the
"oracle" it is compared with was never run. The single published seed is 42
(a second seed 43 is reported as an E5 ablation).

WHAT THIS SCRIPT MEASURES INSTEAD
The same ALTA implementation (`core.alta.alta_run`, K=3, kappa=1.5, T_max=400,
unchanged original code), scored against an oracle that is itself simulated
and evaluated out of sample:

    oracle SELECT block  ->  t_ora = argmin_t mean_Osel[u_t^2]
    oracle SCORE  block  ->  R_ora = mean_Oscore[u_{t_ora}^2]

so R_ora is a realized oracle risk on held-out replicates, not a closed-form
minimum. ALTA's realized risk is the squared mean-replica prediction at t_hat,
exactly as in the original. The frozen reference delta^2 is exact (u_0 = delta
deterministically), so the safety comparison needs no estimate.

PROTOCOL
  * cells: alpha in {0.25,0.5,0.75,1.0} x delta/sigma in {1,2,4,8} (original
    part_d subgrid), eta = 0.05, sigma = 1, T_max = 400, K = 3, kappa = 1.5.
  * N_ALTA independent ALTA episodes per cell (original used 200).
  * oracle: N_ORACLE replicates split 50/50 into disjoint SELECT / SCORE.
  * gates re-evaluated as published: p90 realized risk <= 3 log(T) * R_ora
    + 2 eta sigma^2, and mean realized risk <= 1.02 * delta^2 (safety).
  * seeds 20260801..20260805; mean and range over seeds.

REPRODUCTION CHECK (asserted)
The measured oracle risk must never exceed the frozen risk delta^2 by more
than 2% -- an out-of-sample oracle stop always has t = 0 available.
"""
import argparse

import numpy as np

import common as C

N_ALTA = 400
N_ORACLE = 40_000
ALPHAS_D = [0.25, 0.5, 0.75, 1.0]
RATIOS_D = [1.0, 2.0, 4.0, 8.0]


def measured_oracle(a, delta, rng, T, n_rep):
    """Realized oracle risk: step picked on one replicate half, scored on the
    other. Returns (t_ora, R_ora, se)."""
    half = n_rep // 2
    us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
    t_ora = int(np.argmin((us[:half] ** 2).mean(axis=0)))
    uB = us[half:, t_ora]
    return t_ora, float((uB ** 2).mean()), C.se_of_mean_square(uB)


def run_seed(seed, n_alta=N_ALTA, n_oracle=N_ORACLE, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    cfg = C.ALTAConfig(T_max=T)
    logT = float(np.log(T))
    eps_add = 2.0 * C.ETA * C.SIGMA ** 2
    rows = []
    for a in ALPHAS_D:
        for r in RATIOS_D:
            delta = r * C.SIGMA
            t_ora, R_ora, se_ora = measured_oracle(a, delta, rng, T, n_oracle)
            assert R_ora <= delta ** 2 * 1.02, (
                f"seed {seed} cell (a={a}, d={delta}): measured oracle risk "
                f"{R_ora:.4g} exceeds frozen {delta**2:.4g}")
            root = np.sqrt(max(1 - a ** 2, 0.0))
            realized, t_hats = [], []
            for _rep in range(n_alta):
                states = [{"s": delta * a, "p": 0.0} for _ in range(cfg.K)]

                def mk(st):
                    def step():
                        st["s"] = ((1 - C.ETA) * st["s"]
                                   - C.ETA * C.SIGMA * rng.standard_normal())
                        st["p"] = (st["p"]
                                   - C.ETA * C.SIGMA * rng.standard_normal())
                        u = delta * (1 - a ** 2) + a * st["s"] + root * st["p"]
                        return np.array([u])
                    return step

                tr = C.alta_run([mk(s) for s in states], cfg,
                                pred0=np.array([delta]))
                realized.append(float(tr.pred_at_t_hat[0] ** 2))
                t_hats.append(tr.t_hat)
            realized = np.asarray(realized)
            ratio = realized / max(R_ora, 1e-12)
            p90 = float(np.percentile(realized, 90))
            rows.append({
                "alpha": a, "delta": delta,
                "t_oracle_measured": t_ora,
                "t_star_theory_reference": C.t_star_theory(
                    a, delta, C.SIGMA, C.ETA, T)[0],
                "risk_oracle_measured": R_ora, "risk_oracle_se": se_ora,
                "risk_star_theory_reference": float(
                    C.t_star_theory(a, delta, C.SIGMA, C.ETA, T)[1]),
                "median_t_hat": float(np.median(t_hats)),
                "mean_realized_risk": float(realized.mean()),
                "median_risk_ratio": float(np.median(ratio)),
                "p90_risk_ratio": float(np.percentile(ratio, 90)),
                "frac_worse_than_frozen": float((realized > delta ** 2).mean()),
                "safe_vs_frozen": bool(realized.mean() <= delta ** 2 * 1.02),
                "p90_bound_holds": bool(
                    p90 <= 3.0 * logT * R_ora + eps_add),
                "implied_constant": float(p90 / max(R_ora, 1e-12)),
            })
    p90_ok = all(x["p90_bound_holds"] for x in rows)
    safe_ok = all(x["safe_vs_frozen"] for x in rows
                  if x["t_oracle_measured"] > 0)
    return {"seed": seed, "n_alta_episodes": n_alta, "n_oracle_rep": n_oracle,
            "T_max": T, "K": cfg.K, "kappa": cfg.kappa,
            "log_Tmax": logT, "eps_additive": eps_add, "rows": rows,
            "n_cells": len(rows),
            "n_cells_p90_bound_holds": sum(
                1 for x in rows if x["p90_bound_holds"]),
            "n_cells_safe_vs_frozen": sum(
                1 for x in rows if x["safe_vs_frozen"]),
            "p90_gate": bool(p90_ok), "safety_gate": bool(safe_ok),
            "min_median_risk_ratio": float(np.min(
                [x["median_risk_ratio"] for x in rows])),
            "max_median_risk_ratio": float(np.max(
                [x["median_risk_ratio"] for x in rows])),
            "max_p90_risk_ratio": float(np.max(
                [x["p90_risk_ratio"] for x in rows])),
            "max_implied_constant": float(np.max(
                [x["implied_constant"] for x in rows]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-alta", type=int, default=N_ALTA)
    ap.add_argument("--n-oracle", type=int, default=N_ORACLE)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_alta, args.n_oracle)
        C.save(r, f"f4_alta_measured_oracle_seed{s}.json")
        per_seed.append(r)
        print(f"[f4] seed {s}: p90 gate {r['n_cells_p90_bound_holds']}/16, "
              f"safety {r['n_cells_safe_vs_frozen']}/16, median ratio "
              f"{r['min_median_risk_ratio']:.2f}-{r['max_median_risk_ratio']:.2f}",
              flush=True)

    keys = ["n_cells_p90_bound_holds", "n_cells_safe_vs_frozen",
            "min_median_risk_ratio", "max_median_risk_ratio",
            "max_p90_risk_ratio", "max_implied_constant"]
    summary = {"script": "f4_alta_measured_oracle.py",
               "replaces": ("run_e1.part_d ratios (measured numerator over a "
                            "closed-form oracle denominator)"),
               "seeds": args.seeds, "n_alta_episodes": args.n_alta,
               "n_oracle_rep": args.n_oracle}
    for k in keys:
        summary[k] = C.mean_range([r[k] for r in per_seed])
    # per-cell table averaged over seeds
    cells = {}
    for r in per_seed:
        for x in r["rows"]:
            cells.setdefault((x["alpha"], x["delta"]), []).append(x)
    summary["cells"] = [
        {"alpha": k[0], "delta": k[1],
         "t_oracle_measured": C.mean_range(
             [x["t_oracle_measured"] for x in v]),
         "median_t_hat": C.mean_range([x["median_t_hat"] for x in v]),
         "median_risk_ratio": C.mean_range(
             [x["median_risk_ratio"] for x in v]),
         "p90_risk_ratio": C.mean_range([x["p90_risk_ratio"] for x in v]),
         "safe_vs_frozen_all_seeds": all(x["safe_vs_frozen"] for x in v),
         "p90_bound_holds_all_seeds": all(x["p90_bound_holds"] for x in v)}
        for k, v in sorted(cells.items())]
    C.save(summary, "f4_alta_measured_oracle_summary.json")
    print("[f4] DONE", flush=True)


if __name__ == "__main__":
    main()
