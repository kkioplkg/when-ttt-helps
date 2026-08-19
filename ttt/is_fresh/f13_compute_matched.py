"""F13 -- ALTA against a COMPUTE-MATCHED oracle in the exact model.

WHY THIS SCRIPT EXISTS
----------------------
ALTA's output is the mean prediction of K = 3 replica trajectories at the
selected step, but the oracle it is compared with in Theorem 5 (and in
f4_alta_measured_oracle.py) is the best step of a SINGLE trajectory.  That is
not a like-for-like comparator: a
K-replica rule that is allowed to spend K trajectories should be measured
against what K trajectories can buy at a fixed step, i.e. the oracle over

    R_K(t) = m_t^2 + V_t / K ,      m_t = E[u_t],  V_t = Var(u_t),

which is exactly the risk of averaging K independent trajectories at step t.
Averaging alone shrinks the variance term by K, so min_t R_K(t) <= min_t R_1(t)
and the compute-matched benchmark is strictly harder.  Reporting ALTA only
against the easier one overstates how oracle-efficient the rule is.

WHAT THIS SCRIPT MEASURES
Three quantities per cell, all simulated, none taken from a closed form:

  R_ora_K1   single-trajectory measured oracle.  Step chosen on a SELECT block
             of replicates, risk scored on a disjoint SCORE block.  This is
             f4_alta_measured_oracle.py's denominator, recomputed here so both
             ratios come from the same simulation.
  R_ora_KK   COMPUTE-MATCHED measured oracle.  n_groups independent groups of
             K trajectories are simulated; the group-mean prediction is formed
             at every step; the best step is chosen on a SELECT block of GROUPS
             and the risk of the group-mean prediction is scored on a disjoint
             SCORE block of groups.  This is min_t {m_t^2 + V_t/K} measured
             rather than evaluated analytically.
  R_alta     ALTA's realized risk, from the unchanged original implementation
             (`core.alta.alta_run`, K = 3, kappa = 1.5, T_max = 400), i.e. the
             squared mean-replica prediction at the label-free stopping step.

and the two ratios R_alta / R_ora_K1 (the comparator the manuscript uses) and
R_alta / R_ora_KK (the compute-matched comparator), as medians and p90s
over N_ALTA episodes, at five fresh seeds.

The point of the exercise is a number, not a rhetorical concession: the gap
between the two ratio columns is the amount by which the published oracle
comparison flatters ALTA, and the sign of R_alta - R_ora_KK says whether the
adaptive rule is better or worse than simply averaging K trajectories and
stopping at the single best fixed step.

PROTOCOL
  * cells: alpha in {0.25, 0.5, 0.75, 1.0} x delta/sigma in {1, 2, 4, 8}
    (the original run_e1.part_d subgrid), eta = 0.05, sigma = 1, T_max = 400,
    K = 3, kappa = 1.5.
  * N_ALTA = 400 ALTA episodes per cell.
  * N_ORACLE = 40,000 single trajectories, split 50/50 SELECT / SCORE.
  * N_GROUP = 20,000 groups of K trajectories (60,000 trajectories), split
    50/50 SELECT / SCORE, for the compute-matched oracle.
  * seeds 20260801..20260805; mean and range over seeds.

REPRODUCTION CHECKS (asserted)
  1. The measured compute-matched oracle must agree with the closed form
     min_t {m_t^2 + V_t/K} to within 5 Monte-Carlo standard errors at every
     cell.  This is the one place a closed form appears, and it is a check.
  2. R_ora_KK <= R_ora_K1 * (1 + 1e-6) + 5 SE at every cell: averaging K
     trajectories cannot be worse than one at the same step, so the
     compute-matched oracle cannot be the looser benchmark.
  3. Neither oracle may exceed the frozen risk delta^2 by more than 2%
     (t = 0 is always available).
"""
import argparse

import numpy as np

import common as C

N_ALTA = 400
N_ORACLE = 40_000
N_GROUP = 20_000
CHUNK = 5_000
ALPHAS_D = [0.25, 0.5, 0.75, 1.0]
RATIOS_D = [1.0, 2.0, 4.0, 8.0]


def measured_oracle_k1(a, delta, rng, T, n_rep):
    """Single-trajectory measured oracle (identical to f4's `measured_oracle`)."""
    half = n_rep // 2
    us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
    t_ora = int(np.argmin((us[:half] ** 2).mean(axis=0)))
    uB = us[half:, t_ora]
    return t_ora, float((uB ** 2).mean()), C.se_of_mean_square(uB)


def measured_oracle_kk(a, delta, rng, T, n_groups, K, chunk=CHUNK):
    """Compute-matched measured oracle: best fixed step for the K-group mean.

    Simulated in chunks so peak memory stays at (chunk * K * (T+1)) floats.
    """
    means = np.empty((n_groups, T + 1))
    done = 0
    while done < n_groups:
        g = min(chunk, n_groups - done)
        us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, g * K, rng)
        means[done:done + g] = us.reshape(g, K, T + 1).mean(axis=1)
        done += g
    half = n_groups // 2
    t_ora = int(np.argmin((means[:half] ** 2).mean(axis=0)))
    mB = means[half:, t_ora]
    return t_ora, float((mB ** 2).mean()), C.se_of_mean_square(mB)


def theory_risk_k(a, delta, K, T):
    """min_t {m_t^2 + V_t/K}; REFERENCE ONLY (reproduction check)."""
    ts = np.arange(0, T + 1)
    m = C.mean_u(ts, a, delta, C.ETA)
    v = C.var_u(ts, a, C.SIGMA, C.ETA)
    r = m ** 2 + v / K
    return int(np.argmin(r)), float(r.min())


def alta_episodes(a, delta, rng, cfg, n_alta):
    """Realized ALTA risks (squared mean-replica prediction at t_hat)."""
    root = np.sqrt(max(1 - a ** 2, 0.0))
    realized, t_hats = [], []
    for _rep in range(n_alta):
        states = [{"s": delta * a, "p": 0.0} for _ in range(cfg.K)]

        def mk(st):
            def step():
                st["s"] = ((1 - C.ETA) * st["s"]
                           - C.ETA * C.SIGMA * rng.standard_normal())
                st["p"] = st["p"] - C.ETA * C.SIGMA * rng.standard_normal()
                u = delta * (1 - a ** 2) + a * st["s"] + root * st["p"]
                return np.array([u])
            return step

        tr = C.alta_run([mk(s) for s in states], cfg, pred0=np.array([delta]))
        realized.append(float(tr.pred_at_t_hat[0] ** 2))
        t_hats.append(tr.t_hat)
    return np.asarray(realized), np.asarray(t_hats)


def run_seed(seed, n_alta=N_ALTA, n_oracle=N_ORACLE, n_group=N_GROUP, T=None):
    T = C.T if T is None else T
    rng = np.random.default_rng(seed)
    cfg = C.ALTAConfig(T_max=T)
    K = cfg.K
    rows = []
    for a in ALPHAS_D:
        for r in RATIOS_D:
            delta = r * C.SIGMA
            frozen = delta ** 2

            t1, R1, se1 = measured_oracle_k1(a, delta, rng, T, n_oracle)
            tk, Rk, sek = measured_oracle_kk(a, delta, rng, T, n_group, K)
            tk_th, Rk_th = theory_risk_k(a, delta, K, T)

            # ---- check 3: neither oracle can lose to the frozen model
            assert R1 <= frozen * 1.02 and Rk <= frozen * 1.02, (
                f"seed {seed} cell (a={a}, d={delta}): oracle risk exceeds "
                f"frozen ({R1:.4g}, {Rk:.4g} vs {frozen:.4g})")
            # ---- check 1: measured compute-matched oracle vs its closed form
            assert abs(Rk - Rk_th) <= 5.0 * sek + 1e-9 * max(frozen, 1.0), (
                f"seed {seed} cell (a={a}, d={delta}): measured K-oracle "
                f"{Rk:.6g} disagrees with min_t(m^2+V/K) = {Rk_th:.6g} "
                f"(5 SE = {5*sek:.3g})")
            # ---- check 2: averaging cannot make the oracle worse
            assert Rk <= R1 * (1 + 1e-6) + 5.0 * (se1 + sek), (
                f"seed {seed} cell (a={a}, d={delta}): compute-matched oracle "
                f"{Rk:.6g} exceeds the single-trajectory oracle {R1:.6g}")

            realized, t_hats = alta_episodes(a, delta, rng, cfg, n_alta)
            ratio1 = realized / max(R1, 1e-12)
            ratiok = realized / max(Rk, 1e-12)
            rows.append({
                "alpha": a, "delta": delta, "frozen_risk": frozen, "K": K,
                "t_oracle_k1": t1, "risk_oracle_k1": R1, "se_oracle_k1": se1,
                "t_oracle_kK": tk, "risk_oracle_kK": Rk, "se_oracle_kK": sek,
                "t_oracle_kK_theory_reference": tk_th,
                "risk_oracle_kK_theory_reference": Rk_th,
                "variance_reduction_ratio_R1_over_RK": float(R1 / max(Rk, 1e-12)),
                "median_t_hat": float(np.median(t_hats)),
                "mean_realized_risk": float(realized.mean()),
                "median_realized_risk": float(np.median(realized)),
                "median_ratio_vs_k1": float(np.median(ratio1)),
                "p90_ratio_vs_k1": float(np.percentile(ratio1, 90)),
                "median_ratio_vs_computematched": float(np.median(ratiok)),
                "p90_ratio_vs_computematched": float(np.percentile(ratiok, 90)),
                "alta_beats_computematched_median": bool(
                    np.median(realized) <= Rk),
                "alta_beats_k1_median": bool(np.median(realized) <= R1),
                "frac_episodes_worse_than_computematched": float(
                    (realized > Rk).mean()),
                "frac_episodes_worse_than_frozen": float(
                    (realized > frozen).mean()),
            })
        print(f"[f13 seed {seed}] alpha {a} done", flush=True)

    return {
        "seed": seed, "n_alta_episodes": n_alta, "n_oracle_rep": n_oracle,
        "n_oracle_groups": n_group, "T_max": T, "K": K, "kappa": cfg.kappa,
        "rows": rows, "n_cells": len(rows),
        "median_ratio_vs_k1_range": [
            float(np.min([x["median_ratio_vs_k1"] for x in rows])),
            float(np.max([x["median_ratio_vs_k1"] for x in rows]))],
        "median_ratio_vs_computematched_range": [
            float(np.min([x["median_ratio_vs_computematched"] for x in rows])),
            float(np.max([x["median_ratio_vs_computematched"] for x in rows]))],
        "max_p90_ratio_vs_k1": float(np.max(
            [x["p90_ratio_vs_k1"] for x in rows])),
        "max_p90_ratio_vs_computematched": float(np.max(
            [x["p90_ratio_vs_computematched"] for x in rows])),
        "n_cells_alta_beats_computematched_median": sum(
            1 for x in rows if x["alta_beats_computematched_median"]),
        "n_cells_alta_beats_k1_median": sum(
            1 for x in rows if x["alta_beats_k1_median"]),
        "mean_variance_reduction_R1_over_RK": float(np.mean(
            [x["variance_reduction_ratio_R1_over_RK"] for x in rows])),
        "max_variance_reduction_R1_over_RK": float(np.max(
            [x["variance_reduction_ratio_R1_over_RK"] for x in rows])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-alta", type=int, default=N_ALTA)
    ap.add_argument("--n-oracle", type=int, default=N_ORACLE)
    ap.add_argument("--n-group", type=int, default=N_GROUP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.n_alta, args.n_oracle, args.n_group)
        C.save(r, f"f13_compute_matched_seed{s}.json")
        per_seed.append(r)
        print(f"[f13] seed {s}: median ratio vs K=1 oracle "
              f"{r['median_ratio_vs_k1_range'][0]:.2f}-"
              f"{r['median_ratio_vs_k1_range'][1]:.2f}; vs compute-matched "
              f"{r['median_ratio_vs_computematched_range'][0]:.2f}-"
              f"{r['median_ratio_vs_computematched_range'][1]:.2f}; ALTA "
              f"beats compute-matched in "
              f"{r['n_cells_alta_beats_computematched_median']}/16 cells",
              flush=True)

    keys = ["max_p90_ratio_vs_k1", "max_p90_ratio_vs_computematched",
            "n_cells_alta_beats_computematched_median",
            "n_cells_alta_beats_k1_median",
            "mean_variance_reduction_R1_over_RK",
            "max_variance_reduction_R1_over_RK"]
    summary = {
        "script": "f13_compute_matched.py",
        "finding": ("a K-replica averaged output was "
                    "compared with a single-trajectory oracle"),
        "comparators": {
            "k1": "min over t of the risk of ONE trajectory (measured)",
            "compute_matched":
                "min over t of the risk of the mean of K trajectories "
                "(measured); equals min_t {m_t^2 + V_t/K} in population"},
        "seeds": args.seeds, "n_alta_episodes": args.n_alta,
        "n_oracle_rep": args.n_oracle, "n_oracle_groups": args.n_group,
        "K": per_seed[0]["K"],
    }
    for k in keys:
        summary[k] = C.mean_range([r[k] for r in per_seed])

    cells = {}
    for r in per_seed:
        for x in r["rows"]:
            cells.setdefault((x["alpha"], x["delta"]), []).append(x)
    summary["cells"] = [
        {"alpha": k[0], "delta": k[1],
         "risk_oracle_k1": C.mean_range([x["risk_oracle_k1"] for x in v]),
         "risk_oracle_kK": C.mean_range([x["risk_oracle_kK"] for x in v]),
         "variance_reduction_R1_over_RK": C.mean_range(
             [x["variance_reduction_ratio_R1_over_RK"] for x in v]),
         "median_ratio_vs_k1": C.mean_range(
             [x["median_ratio_vs_k1"] for x in v]),
         "median_ratio_vs_computematched": C.mean_range(
             [x["median_ratio_vs_computematched"] for x in v]),
         "p90_ratio_vs_k1": C.mean_range([x["p90_ratio_vs_k1"] for x in v]),
         "p90_ratio_vs_computematched": C.mean_range(
             [x["p90_ratio_vs_computematched"] for x in v]),
         "alta_beats_computematched_median_all_seeds": all(
             x["alta_beats_computematched_median"] for x in v),
         "t_oracle_k1": C.mean_range([x["t_oracle_k1"] for x in v]),
         "t_oracle_kK": C.mean_range([x["t_oracle_kK"] for x in v]),
         "median_t_hat": C.mean_range([x["median_t_hat"] for x in v])}
        for k, v in sorted(cells.items())]

    allmed1 = [x["median_ratio_vs_k1"] for r in per_seed for x in r["rows"]]
    allmedk = [x["median_ratio_vs_computematched"]
               for r in per_seed for x in r["rows"]]
    summary["headline"] = {
        "median_ratio_vs_k1_over_all_cells_and_seeds": [
            float(np.min(allmed1)), float(np.max(allmed1))],
        "median_ratio_vs_computematched_over_all_cells_and_seeds": [
            float(np.min(allmedk)), float(np.max(allmedk))],
        "n_cells_of_16_where_alta_median_beats_compute_matched":
            summary["n_cells_alta_beats_computematched_median"],
    }
    C.save(summary, "f13_compute_matched_summary.json")
    print("[f13] DONE", flush=True)


if __name__ == "__main__":
    main()
