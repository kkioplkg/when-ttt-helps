"""Analysis for P2 (Tier 2): A2 along trajectories, Jacobian conditioning,
Proposition 5.5's certificate funnel.

Naming discipline (DESIGN v2 s4).  Path extrema are PATH STATISTICS, never A2's
region constants: for any Theta_loc containing the realized path,
min_t alpha_t >= alpha_*, min_t rho_t >= c_*, max_t rho_t <= C_*.  Nothing here
is called an estimate of c_g or C_g.

A2 falsification is decided on the inner product with explicit non-degeneracy,
not on a cosine that the vanishing-gradient convention would set to 0.  Because
Theta_loc is taken to be the ball containing the realized trajectory, A4 holds
by construction and the falsification is unconditional on that ball.

Proposition 5.5 is reported as a three-level funnel -- eligible -> Z >= 0 ->
LB > 0 -- so that a zero at the end still says whether the bound died in the
calibration term or in the Jacobian pullback.
"""
import argparse
import glob
import os
import sys
from collections import defaultdict

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from common import read_records, rel, save_json  # noqa: E402

PRACTICAL_LR = 1e-3          # the step size the manuscript's protocol uses


def q(vals, ps=(0, 5, 25, 50, 75, 95, 100)):
    v = [x for x in vals if x is not None and np.isfinite(x)]
    if not v:
        return None
    return {f"p{p}": float(np.percentile(v, p)) for p in ps} | {"n": len(v),
                                                                "mean": float(np.mean(v))}


def analyze(paths):
    out = {"n_episodes": 0}
    by = defaultdict(lambda: {
        "n": 0, "falsified": 0, "alpha_path_min": [], "alpha_t0": [],
        "rho_path_min": [], "rho_path_max": [], "eta_hat": [],
        "theta_loc_radius": [], "T_flip": [], "dR": []})
    curves = defaultdict(lambda: defaultdict(list))
    funnel = defaultdict(lambda: {"points": 0, "eligible_def53": 0,
                                  "eligible": 0, "Z_nonneg": 0, "LB_pos": 0,
                                  "LB_le_minus1": 0, "sound_violations": 0})
    jac = defaultdict(lambda: {"kappa_J": [], "L_J": [], "mu_literal": [],
                               "mu_restricted": [], "ratio_restricted_literal": [],
                               "gram_cond": [], "kappa_crit": [], "LB": [],
                               "Z": []})
    for path in paths:
        for r in read_records(path):
            out["n_episodes"] += 1
            key = f'{r["objective"]}|mom{r["momentum"]}'
            skey = f'{key}|sev{r["severity"]}'
            s = r["summary"]
            for k in (key, skey):
                b = by[k]
                b["n"] += 1
                b["falsified"] += int(s["any_falsifies_A2"])
                for f in ("alpha_path_min", "alpha_t0", "rho_path_min",
                          "rho_path_max", "theta_loc_radius"):
                    b[f].append(s[f])
                b["eta_hat"].append(s["eta_hat_optimistic_upper"])
                if s["T_flip"] is not None:
                    b["T_flip"].append(s["T_flip"])
                b["dR"].append(s["R_T"] - s["R_0"])
            for st in r["steps"]:
                curves[key][st["t"]].append(st["alpha"])
            for t, j in r.get("jacobian", {}).items():
                fk = f"{key}|t{t}"
                fn = funnel[fk]
                fn["points"] += 1
                fn["eligible_def53"] += int(j.get("eligible_def53", 0))
                fn["eligible"] += int(j.get("eligible", 0))
                if not j.get("eligible"):
                    continue
                fn["Z_nonneg"] += int(j["Z"] >= 0)
                if j.get("LB") is not None:
                    fn["LB_pos"] += int(j["LB"] > 0)
                    fn["LB_le_minus1"] += int(j["LB"] <= -1)
                jj = jac[fk]
                for a, b_ in (("kappa_J", "kappa_J"), ("L_J", "L_J"),
                              ("mu_J_literal", "mu_literal"),
                              ("mu_J_restricted", "mu_restricted"),
                              ("gram_cond", "gram_cond"),
                              ("kappa_crit", "kappa_crit"), ("LB", "LB"),
                              ("Z", "Z")):
                    if j.get(a) is not None:
                        jj[b_].append(j[a])
                if j.get("mu_J_literal"):
                    jj["ratio_restricted_literal"].append(
                        j["mu_J_restricted"] / j["mu_J_literal"])

    res = {"n_episodes": out["n_episodes"], "by_group": {}, "alpha_curves": {},
           "prop55_funnel": {}, "jacobian": {}}
    for k, b in by.items():
        res["by_group"][k] = {
            "n": b["n"],
            "A2_falsified_episodes": b["falsified"],
            "A2_falsified_frac": b["falsified"] / b["n"] if b["n"] else None,
            "alpha_path_min": q(b["alpha_path_min"]),
            "alpha_t0": q(b["alpha_t0"]),
            "rho_path_min": q(b["rho_path_min"]),
            "rho_path_max": q(b["rho_path_max"]),
            "theta_loc_radius": q(b["theta_loc_radius"]),
            "eta_hat_optimistic_upper": q(b["eta_hat"]),
            "n_eta_hat_below_practical_lr": int(sum(
                1 for e in b["eta_hat"] if e is not None and e < PRACTICAL_LR)),
            "T_flip": q(b["T_flip"]) if b["T_flip"] else None,
            "risk_change_R_T_minus_R_0": q(b["dR"]),
        }
    for k, c in curves.items():
        res["alpha_curves"][k] = {str(t): {"mean": float(np.mean(v)),
                                           "p5": float(np.percentile(v, 5)),
                                           "p50": float(np.percentile(v, 50)),
                                           "p95": float(np.percentile(v, 95)),
                                           "n": len(v)}
                                  for t, v in sorted(c.items())}
    for k, f in funnel.items():
        res["prop55_funnel"][k] = dict(f)
    for k, j in jac.items():
        res["jacobian"][k] = {kk: q(vv) for kk, vv in j.items() if vv}
    res["practical_lr"] = PRACTICAL_LR
    res["notes"] = {
        "path_statistics": "min/max over the realized trajectory. These bound "
                           "A2's region constants (min_t alpha_t >= alpha_*, "
                           "min_t rho_t >= c_*, max_t rho_t <= C_*); they are "
                           "not estimates of them.",
        "eta_hat": "trajectory-derived OPTIMISTIC UPPER BOUND on the maximal "
                   "admissible step cap. Only eta_practical > eta_hat is "
                   "informative; the converse implies nothing.",
        "mu_J": "literal Loewner constant via Schur complement; "
                "mu_restricted/mu_literal is the factor by which the restricted "
                "reading would have understated kappa_J.",
    }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--glob", default="p2_*.jsonl.gz")
    args = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(args.in_dir, args.glob)))
    if not paths:
        raise SystemExit(f"no records matching {args.glob}")
    res = analyze(paths)
    res["inputs"] = [rel(p) for p in paths]
    for k, b in sorted(res["by_group"].items()):
        if "sev" in k:
            continue
        print(f"[{k}] n={b['n']} A2-falsified={b['A2_falsified_episodes']} "
              f"alpha_path_min p50={b['alpha_path_min']['p50']:.4f} "
              f"p5={b['alpha_path_min']['p5']:.4f} "
              f"eta_hat<lr on {b['n_eta_hat_below_practical_lr']}/{b['n']}")
    for k, f in sorted(res["prop55_funnel"].items()):
        print(f"  funnel {k}: eligible {f['eligible']}/{f['points']} "
              f"-> Z>=0 {f['Z_nonneg']} -> LB>0 {f['LB_pos']} "
              f"(LB<=-1 on {f['LB_le_minus1']})")
    save_json(res, args.out)


if __name__ == "__main__":
    main()
