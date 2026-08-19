"""Analysis for T2.1 (batch-scope collinearity loss) and T2.5 (A2 shell search).

T2.1 reports |cos(g_H^B, g_R^B)| only.  There is deliberately no agreement rate:
Theorem 5.2 defines no batch right-hand side, so an "agreement" at N > 1 would be
agreement with a quantity that does not exist.  The per-member sign composition
IS defined by the theorem and is used as the covariate that explains the loss.

T2.5 reports the shell minimum of <gbar, grad R> as what it is: the minimum over
a FINITE SAMPLE of directions, which lower-bounds nothing and upper-bounds the
region infimum.  A non-positive value falsifies A2 on any region containing the
shell; a positive sample proves nothing.  The headline is the asymmetric count --
episodes whose on-path inner product stays positive while some sampled shell
point goes non-positive -- i.e. alignment that persists along the path without
being locally robust.
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


def stats(v):
    v = [x for x in v if x is not None and np.isfinite(x)]
    if not v:
        return None
    return {"n": len(v), "mean": float(np.mean(v)), "min": float(np.min(v)),
            "p5": float(np.percentile(v, 5)), "p50": float(np.percentile(v, 50)),
            "max": float(np.max(v))}


def analyze_scope(paths):
    by = defaultdict(list)
    by_sign = defaultdict(list)
    for p in paths:
        for r in read_records(p):
            for e in r["per_eps"]:
                by[e["N"]].append(e["abs_cos"])
                by_sign[(e["N"], e["sign_homogeneous"])].append(e["abs_cos"])
    return {
        "note": "|cos(g_H^B, g_R^B)| only; Theorem 5.2 defines no batch RHS, so "
                "no agreement rate is computed at N > 1.",
        "by_N": {str(k): stats(v) for k, v in sorted(by.items())},
        "by_N_and_sign_homogeneity": {
            f"N{k[0]}|homogeneous{k[1]}": stats(v)
            for k, v in sorted(by_sign.items())},
    }


def analyze_shell(paths):
    out = defaultdict(lambda: {
        "episodes": 0, "asymmetric": 0, "on_path_falsified": 0,
        "by_radius": defaultdict(lambda: {"points": 0, "falsifying_points": 0,
                                          "min_inner": [], "alpha_at_min": [],
                                          "falsifying_direction_frac": []}),
        "on_path_alpha": [],
    })
    for p in paths:
        for r in read_records(p):
            k = f'{r["objective"]}|s{r["model_seed"]}'
            g = out[k]
            g["episodes"] += 1
            g["asymmetric"] += int(r["any_asymmetric"])
            on_path_neg = False
            for pt in r["points"]:
                op = pt["on_path"]
                g["on_path_alpha"].append(op["alpha"])
                if op["nondegenerate"] and op["inner"] <= 0:
                    on_path_neg = True
                for s in pt["shells"]:
                    b = g["by_radius"][str(s["r_rel"])]
                    b["points"] += 1
                    b["falsifying_points"] += int(s["falsifies_A2"])
                    b["min_inner"].append(s["min_inner"])
                    b["alpha_at_min"].append(s["alpha_at_min"])
                    b["falsifying_direction_frac"].append(
                        s["n_falsifying_directions"] / max(s["n_dir"], 1))
            g["on_path_falsified"] += int(on_path_neg)
    res = {}
    for k, g in out.items():
        res[k] = {
            "episodes": g["episodes"],
            "episodes_with_on_path_A2_falsification": g["on_path_falsified"],
            "episodes_asymmetric_on_path_pos_shell_neg": g["asymmetric"],
            "on_path_alpha": stats(g["on_path_alpha"]),
            "by_radius": {
                r_: {"points": b["points"],
                     "points_with_a_falsifying_direction": b["falsifying_points"],
                     "min_inner": stats(b["min_inner"]),
                     "alpha_at_min": stats(b["alpha_at_min"]),
                     "falsifying_direction_frac": stats(b["falsifying_direction_frac"])}
                for r_, b in sorted(g["by_radius"].items())},
        }
    res["_note"] = ("Shell minima are minima over a FINITE SAMPLE of random "
                    "directions: they upper-bound the region infimum, so a "
                    "non-positive value falsifies A2 on any region containing "
                    "the shell while a positive sample proves nothing.")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sc = sorted(glob.glob(os.path.join(args.in_dir, "scope_*.jsonl.gz")))
    sh = sorted(glob.glob(os.path.join(args.in_dir, "shell_*.jsonl.gz")))
    res = {"inputs": {"scope": [rel(p) for p in sc], "shell": [rel(p) for p in sh]}}
    if sc:
        res["T2_1_batch_scope"] = analyze_scope(sc)
        for k, v in res["T2_1_batch_scope"]["by_N"].items():
            print(f"  N={k}: mean|cos|={v['mean']:.6f} min={v['min']:.6f} n={v['n']}")
    if sh:
        res["T2_5_shell"] = analyze_shell(sh)
        for k, v in sorted(res["T2_5_shell"].items()):
            if k.startswith("_"):
                continue
            print(f"  {k}: episodes={v['episodes']} "
                  f"on-path falsified={v['episodes_with_on_path_A2_falsification']} "
                  f"asymmetric={v['episodes_asymmetric_on_path_pos_shell_neg']}")
    save_json(res, args.out)


if __name__ == "__main__":
    main()
