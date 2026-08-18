"""F28 -- direct simulation of the Appendix B (P3) fixed-law counterexample.

WHAT THE APPENDIX CLAIMS (`appendix/proofs_entropy_alta.tex`, the "Explicit
thresholds" paragraph of the Conjecture~70 discussion): at
$\\eta = 1/4$, $K = 3$, $T = 2$, $\\beta = 3$, $\\sigma = 1$ and
$c_\\psi = C' = 1$, a direct simulation of the population-band scan on the
fixed symmetric Pareto law already refutes the conjectured display at
$\\gamma = 10^{-4}$, the measured

    Pr( Excbar(that) > display's right-hand side ) / gamma

rising through three values at gamma = 1e-4, 1e-5, 1e-6.

CLASSIFICATION: MEASURED (Monte Carlo).  This script is the record of record
for those three ratios.  The analytic refutation in the appendix stands on its
own -- inequalities (S1) and (S2) are proved, not simulated -- so this run is
corroboration, not evidence; it exists because every other number in the
package has a named record of record and these three did not.

THE MODEL (Appendix B, "A fixed-law counterexample")
Scalar quadratic environment, prediction f_theta(x*) = theta, theta_0 = 0,
R*(x*) = 0, step size eta in (0, 1/2), a := 1 - 2 eta.  Each of the K replicas
runs, independently,

    theta^{(k)}_{t+1} = a theta^{(k)}_t - eta xi^{(k)}_t ,   t = 0 .. T-1,

with the xi^{(k)}_t i.i.d. from the symmetric polynomial-tail law

    Pr(|xi| >= x) = (x_m / x)^beta   (x >= x_m),   Pr(xi > 0) = 1/2,
    x_m = sigma sqrt((beta - 2) / beta),

which has mean 0 and variance sigma^2 and is FIXED -- it does not move with
gamma.  The exact population variance profile is v_0 = 0,
v_{t+1} = a^2 v_t + eta^2 sigma^2.

THE RULE.  Definition 15(P), the population-band scan, run with the matched
band constant of (B.kappapsi):

    that = min{ t >= 0 : for all u in (t, T],
                |ubar_u - ubar_t| <= kappa_{gamma,psi}
                                     (sqrt(v_u) + sqrt(v_t)) / sqrt(K) }
    kappa_{gamma,psi} = sqrt(c_psi) * 2 sqrt(2 log(4 T^2 / gamma)).

ubar_t is the replica mean thetabar_t, and the deployed output's realized
excess loss is Excbar(that) = thetabar_that^2 (P4 with M_t == M_infinity == 0).

THE COMPARATOR.  In this model Exc1(t*_N) = v_0 = 0, |M_{t*_N} - M_inf| = 0,
v_star = eta^2 sigma^2 and c_2/c_1 = eta sigma^2 / 2, so the log_+ term and the
multiplicative term both vanish and the conjectured right-hand side is exactly

    RHS(gamma) = (7/4) C' eta sigma^2 log(T / gamma) / K .

SEEDS: the five fresh seeds 20260801..20260805 (`common.SEEDS`), run as five
independent blocks so the headline is a pooled estimate with an honest
across-seed range rather than a single unreplicated number.  The same draws
serve all three gamma values (common random numbers); only the band and the
right-hand side move with gamma.

OUTPUT: results/is_fresh/f28_p3_montecarlo.json.  Bound in `r9_reconcile.py`
under the "P3 counterexample" labels.

`--out NAME` overrides that file name.  The full run (default `--reps` and the
five default seeds) writes the record of record; any REDUCED-parameter smoke
run must pass `--out verify_f28_p3_montecarlo.json`, and the script refuses to
run otherwise.  Without that guard a documented smoke command overwrites the
record of record with lower-replication values and `r9_reconcile.py` then
reports three spurious Appendix B mismatches -- the same failure mode
`--out-prefix` prevents for `f7`/`f8`.

Usage:  python f28_p3_montecarlo.py                  # 5 x 2e7 = 1e8 draws
        python f28_p3_montecarlo.py --reps 200000    # quick smoke run
"""
import argparse
import math
import sys

import numpy as np

import common as C

# ---- the construction's parameters, fixed by the appendix ----------------
ETA = 0.25
K = 3
T = 2
BETA = 3.0
SIGMA = 1.0
C_PSI = 1.0
C_PRIME = 1.0
GAMMAS = (1e-4, 1e-5, 1e-6)

A = 1.0 - 2.0 * ETA                     # contraction factor, 1/2
X_M = SIGMA * math.sqrt((BETA - 2.0) / BETA)


def variance_profile():
    """v_0 = 0, v_{t+1} = a^2 v_t + eta^2 sigma^2, for t = 0 .. T."""
    v = [0.0]
    for _ in range(T):
        v.append(A * A * v[-1] + ETA * ETA * SIGMA * SIGMA)
    return np.array(v)


def kappa(gamma):
    """The matched band constant of (B.kappapsi)."""
    return math.sqrt(C_PSI) * 2.0 * math.sqrt(
        2.0 * math.log(4.0 * T * T / gamma))


def rhs(gamma):
    """The conjectured display's right-hand side in this model."""
    return 1.75 * C_PRIME * ETA * SIGMA ** 2 * math.log(T / gamma) / K


def draw_xi(rng, shape):
    """Symmetric polynomial-tail draws: |xi| = x_m U^{-1/beta}, sign +-1.

    One uniform per variate: V ~ U(-1, 1) supplies both the sign and, through
    |V|, the tail uniform.  V = 0 has probability zero in double precision but
    is clipped anyway so the power never overflows.
    """
    v = rng.uniform(-1.0, 1.0, size=shape)
    u = np.abs(v)
    np.clip(u, 1e-300, 1.0, out=u)
    return np.copysign(X_M * u ** (-1.0 / BETA), v)


def scan_and_score(tb, v, gam):
    """Population-band scan on replica means `tb` (reps x (T+1)).

    Returns Excbar(that) = thetabar_that^2 for every replication.
    """
    kg = kappa(gam)
    sq = np.sqrt(v)
    that = np.full(tb.shape[0], T, dtype=np.int8)
    # walk t downwards so the smallest admissible t wins
    for t in range(T - 1, -1, -1):
        ok = np.ones(tb.shape[0], dtype=bool)
        for u in range(t + 1, T + 1):
            band = kg * (sq[u] + sq[t]) / math.sqrt(K)
            ok &= np.abs(tb[:, u] - tb[:, t]) <= band
        that[ok] = t
    return tb[np.arange(tb.shape[0]), that] ** 2, that


def run_block(seed, reps, chunk, v):
    """One seed: return {gamma: n_exceedances} and the replication count."""
    rng = np.random.default_rng(seed)
    hits = {g: 0 for g in GAMMAS}
    at_T = 0
    done = 0
    while done < reps:
        n = min(chunk, reps - done)
        xi = draw_xi(rng, (n, K, T))              # xi^{(k)}_t
        th = np.zeros((n, K, T + 1))
        for t in range(T):
            th[:, :, t + 1] = A * th[:, :, t] - ETA * xi[:, :, t]
        tb = th.mean(axis=1)                      # thetabar_t
        for g in GAMMAS:
            loss, that = scan_and_score(tb, v, g)
            hits[g] += int(np.count_nonzero(loss > rhs(g)))
            if g == GAMMAS[0]:
                at_T += int(np.count_nonzero(that == T))
        done += n
    return hits, at_T, done


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=20_000_000,
                    help="replications PER SEED (default 2e7; 5 seeds)")
    ap.add_argument("--chunk", type=int, default=1_000_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--out", default="f28_p3_montecarlo.json",
                    help="output file name under results/is_fresh (default "
                         "f28_p3_montecarlo.json, the RECORD OF RECORD). Any "
                         "run at reduced --reps/--seeds MUST pass a different "
                         "name, e.g. --out verify_f28_p3_montecarlo.json: "
                         "overwriting the record of record with a "
                         "reduced-parameter run makes r9_reconcile.py report "
                         "spurious mismatches on the three Appendix B ratios.")
    args = ap.parse_args()
    if (args.reps != ap.get_default("reps")
            or list(args.seeds) != list(C.SEEDS)) and \
            args.out == ap.get_default("out"):
        ap.error("reduced-parameter run would overwrite the record of record "
                 f"({args.out}); pass --out verify_f28_p3_montecarlo.json "
                 "(or another name) instead.")

    v = variance_profile()
    print(f"[f28] eta={ETA} a={A} K={K} T={T} beta={BETA} sigma={SIGMA} "
          f"c_psi={C_PSI} C'={C_PRIME}")
    print(f"[f28] x_m={X_M:.6f}  m={X_M * (2 * K * T) ** (1 / BETA):.6f}  "
          f"v={np.array2string(v, precision=6)}")
    for g in GAMMAS:
        print(f"[f28] gamma={g:.0e}  kappa={kappa(g):.6f}  "
              f"RHS={rhs(g):.6f}")

    per_seed = {f"{g:.0e}": [] for g in GAMMAS}
    tot_hits = {g: 0 for g in GAMMAS}
    tot_reps = 0
    tot_at_T = 0
    for s in args.seeds:
        hits, at_T, n = run_block(s, args.reps, args.chunk, v)
        tot_reps += n
        tot_at_T += at_T
        for g in GAMMAS:
            tot_hits[g] += hits[g]
            per_seed[f"{g:.0e}"].append(hits[g] / n / g)
        print(f"[f28] seed {s}  n={n}  " + "  ".join(
            f"{g:.0e}:{hits[g] / n / g:.4f}" for g in GAMMAS), flush=True)

    out = {"model": {"eta": ETA, "a": A, "K": K, "T": T, "beta": BETA,
                     "sigma": SIGMA, "c_psi": C_PSI, "C_prime": C_PRIME,
                     "x_m": X_M, "m_bound": X_M * (2 * K * T) ** (1 / BETA),
                     "variance_profile": v.tolist()},
           "seeds": list(args.seeds),
           "reps_per_seed": args.reps,
           "reps_total": tot_reps,
           "frac_that_equals_T_at_gamma_1e-4": tot_at_T / tot_reps,
           "ratios": {}}
    print()
    for g in GAMMAS:
        p = tot_hits[g] / tot_reps
        ratio = p / g
        se = math.sqrt(max(p * (1 - p), 0.0) / tot_reps) / g
        vals = per_seed[f"{g:.0e}"]
        out["ratios"][f"{g:.0e}"] = {
            "gamma": g,
            "rhs": rhs(g),
            "kappa_gamma_psi": kappa(g),
            "n_exceedances": tot_hits[g],
            "prob": p,
            "ratio_prob_over_gamma": ratio,
            "mc_standard_error_of_ratio": se,
            "per_seed_ratio": vals,
            "per_seed_min": min(vals),
            "per_seed_max": max(vals),
        }
        print(f"[f28] gamma={g:.0e}  hits={tot_hits[g]}  "
              f"P/gamma = {ratio:.4f} +- {se:.4f} (MC SE)  "
              f"per-seed [{min(vals):.4f}, {max(vals):.4f}]")
    print(f"[f28] refuted at every gamma: "
          f"{all(out['ratios'][f'{g:.0e}']['ratio_prob_over_gamma'] > 1.0 for g in GAMMAS)}")

    C.save(out, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
