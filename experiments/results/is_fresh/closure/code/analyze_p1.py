"""Analysis for P1 (Tier 1): the reported numbers, from the raw records.

Reporting discipline (DESIGN v2 s3):

*   Theorem 5.2 asserts a deterministic identity, so the headline is a
    VIOLATION COUNT with the complete dump of every violating episode -- not a
    proportion with a Wald interval around a quantity theory pins at 1.
*   T = 1 is the network the paper runs and is reported alone; T in {2,4} is a
    controlled boundary intervention and is never pooled into a T=1 rate.
*   The nine per-model estimates are printed in full.  No cluster bootstrap is
    used as primary inference for the identity.
*   Stratification edges are frozen powers-of-ten numerical-resolution strata,
    written here and not re-cut after seeing the table.
"""
import argparse
import glob
import hashlib
import os
import sys
from collections import defaultdict

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from common import read_records, rel, save_json  # noqa: E402

# FROZEN strata: powers-of-ten numerical-resolution bands, not data-adaptive
# quantiles.  Never re-cut after seeing results; empty cells are reported n=0.
P_EDGES = [0.0, 1e-6, 1e-4, 1e-2, 0.1, 0.4, 0.5000000001]
Q_EDGES = [0.0, 1e-6, 1e-4, 1e-2, 0.1, 1.0000000001]

MACHINE_EPS = {"float32": float(np.finfo(np.float32).eps),
               "float64": float(np.finfo(np.float64).eps)}
# A relative residual ||g - c*g_s|| / ||g|| is a 0/0 quantity when the
# coefficient c underflows: then c*g_s = 0 and the ratio is identically 1
# whatever the gradient does.  That is a property of the DIAGNOSTIC, not of the
# theorem -- the sign identity is unaffected and is checked separately.  The
# guard below marks an episode's residual as resolvable only when the predicted
# gradient stands clear of the noise floor by this many machine epsilons.
RESOLVABLE_MARGIN = 1e3


def band(x, edges):
    for i in range(len(edges) - 1):
        if edges[i] <= x < edges[i + 1]:
            return i
    return len(edges) - 2


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def analyze(paths):
    out = {
        "n_records": 0, "n_eps_rows": 0,
        "by_T": defaultdict(lambda: {"n": 0, "violations": 0, "excluded": 0,
                                     "min_abs_alpha": None, "max_resid_H": 0.0,
                                     "max_resid_R": 0.0,
                                     "cd_best_rel_err_max": 0.0,
                                     "resid_H_resolvable": [],
                                     "resid_R_resolvable": [],
                                     "cd_resolvable": [],
                                     "n_resid_H_unresolvable": 0,
                                     "n_resid_R_unresolvable": 0,
                                     "n_cd_unresolvable": 0}),
        "by_model": defaultdict(lambda: {"n": 0, "violations": 0}),
        "strata": defaultdict(lambda: {"n": 0, "violations": 0,
                                       "min_abs_alpha": None}),
        "violations": [],
        "naive_disagreement": defaultdict(lambda: {"n": 0, "disagree": 0,
                                                   "theorem_right": 0}),
        "dtypes": set(),
    }
    for path in paths:
        for r in read_records(path):
            out["n_records"] += 1
            out["dtypes"].add(r["dtype"])
            # split by precision as well as temperature: pooling float32 with
            # float64 hides the fact that the float64 residuals sit at 1e-15
            T = f'{r["dtype"]}|T{r["T"]}'
            eps_m = MACHINE_EPS[r["dtype"]]
            mk = f'{r["pair"]}|{r["arch"]}|s{r["model_seed"]}'
            bt = out["by_T"][T]
            p = r["p"]
            coef_H = abs(p * (1.0 - p) * r["s"])
            if r.get("resid_H") is not None:
                bt["max_resid_H"] = max(bt["max_resid_H"], r["resid_H"])
                if coef_H > RESOLVABLE_MARGIN * eps_m:
                    bt["resid_H_resolvable"].append(r["resid_H"])
                else:
                    bt["n_resid_H_unresolvable"] += 1
            for e in r["per_eps"]:
                out["n_eps_rows"] += 1
                coef_R = abs(p - e["q"])
                resolvable_R = coef_R > RESOLVABLE_MARGIN * eps_m
                if e.get("resid_R") is not None:
                    bt["max_resid_R"] = max(bt["max_resid_R"], e["resid_R"])
                    if resolvable_R:
                        bt["resid_R_resolvable"].append(e["resid_R"])
                    else:
                        bt["n_resid_R_unresolvable"] += 1
                if e.get("cd_best_rel_err") is not None:
                    bt["cd_best_rel_err_max"] = max(bt["cd_best_rel_err_max"],
                                                    e["cd_best_rel_err"])
                    # the central difference is normalized by |alpha| * ||g_R||,
                    # which is itself unresolvable when q is within a few eps
                    # of p -- same 0/0 caveat as the residuals
                    if resolvable_R:
                        bt["cd_resolvable"].append(e["cd_best_rel_err"])
                    else:
                        bt["n_cd_unresolvable"] += 1
                agree = e["agree"]
                if agree is None:
                    # outside the theorem's hypotheses (p = 1/2, q = p, or a
                    # vanishing gradient): counted, reported, never silently
                    # dropped, never counted as agreement either
                    bt["excluded"] += 1
                    continue
                bt["n"] += 1
                aa = e["abs_alpha"]
                bt["min_abs_alpha"] = (aa if bt["min_abs_alpha"] is None
                                       else min(bt["min_abs_alpha"], aa))
                out["by_model"][mk]["n"] += 1
                bi = band(abs(r["p"] - 0.5), P_EDGES)
                bj = band(abs(e["q"] - r["p"]), Q_EDGES)
                st = out["strata"][f"{bi}|{bj}"]
                st["n"] += 1
                st["min_abs_alpha"] = (aa if st["min_abs_alpha"] is None
                                       else min(st["min_abs_alpha"], aa))
                if agree == 0:
                    bt["violations"] += 1
                    out["by_model"][mk]["violations"] += 1
                    st["violations"] += 1
                    if len(out["violations"]) < 5000:      # full dump, capped
                        out["violations"].append({
                            "pair": r["pair"], "arch": r["arch"],
                            "model_seed": r["model_seed"], "dtype": r["dtype"],
                            "corruption": r["corruption"],
                            "severity": r["severity"], "test_id": r["test_id"],
                            "T": r["T"], "p": r["p"], "s": r["s"],
                            "eps": e["eps"], "q": e["q"],
                            "alpha_ent": e["alpha_ent"],
                            "rhs_sign": e["rhs_sign"],
                            "abs_alpha": e["abs_alpha"],
                            "gnorm_H": r["gnorm_H"], "gnorm_R": e["gnorm_R"],
                            "gnorm_s": r["gnorm_s"]})
                # the discriminating comparison against modal-label correctness
                nd = out["naive_disagreement"][f'T{T}|eps{e["eps"]}']
                nd["n"] += 1
                if e["theorem_vs_naive_disagree"]:
                    nd["disagree"] += 1
                    if np.sign(e["alpha_ent"]) == e["rhs_sign"]:
                        nd["theorem_right"] += 1
    out["dtypes"] = sorted(out["dtypes"])
    for k in ("by_T", "by_model", "strata", "naive_disagreement"):
        out[k] = dict(out[k])
    # collapse the retained residual samples into quantiles; a single max is the
    # wrong summary for a quantity whose tail is dominated by 0/0 artifacts
    for T, b in out["by_T"].items():
        for src, dst in (("resid_H_resolvable", "resid_H"),
                         ("resid_R_resolvable", "resid_R"),
                         ("cd_resolvable", "cd_best_rel_err")):
            v = np.asarray(b.pop(src), dtype=float)
            v = v[np.isfinite(v)]
            b[dst + "_resolvable"] = ({
                "n": int(v.size),
                "p50": float(np.percentile(v, 50)),
                "p95": float(np.percentile(v, 95)),
                "p99": float(np.percentile(v, 99)),
                "max": float(v.max())} if v.size else None)
    out["resolvability_note"] = (
        "A relative residual (and the central-difference relative error) is a "
        "0/0 quantity when its coefficient underflows: at p = 1 in float32, "
        "p(1-p) = 0 exactly, so ||g - c g_s||/||g|| == 1 whatever the gradient "
        "is, and likewise when |q - p| falls to a few machine epsilons. Those "
        "rows are counted, not dropped, and reported separately; the sign "
        "identity is unaffected and is checked independently of them.")
    out["machine_eps"] = MACHINE_EPS
    out["resolvable_margin_in_eps"] = RESOLVABLE_MARGIN
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--design", default=None,
                    help="path to DESIGN.md; its hash is recorded so the "
                         "frozen stratification is checkable after the fact")
    ap.add_argument("--glob", default="p1_*.jsonl.gz")
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(args.in_dir, args.glob)))
    if not paths:
        raise SystemExit(f"no records matching {args.glob}")
    res = analyze(paths)
    res["inputs"] = [rel(p) for p in paths]
    res["strata_edges"] = {"abs_p_minus_half": P_EDGES, "abs_q_minus_p": Q_EDGES,
                           "note": "frozen powers-of-ten numerical-resolution "
                                   "strata, not data-adaptive quantiles"}
    if args.design and os.path.exists(args.design):
        res["design_sha256"] = file_sha256(args.design)

    for T, b in sorted(res["by_T"].items()):
        print(f"[{T}] n={b['n']} violations={b['violations']} "
              f"excluded={b['excluded']} min|alpha|={b['min_abs_alpha']}")
        for lbl, key, nun in (("resid_H", "resid_H_resolvable",
                               "n_resid_H_unresolvable"),
                              ("resid_R", "resid_R_resolvable",
                               "n_resid_R_unresolvable"),
                              ("CD relerr", "cd_best_rel_err_resolvable",
                               "n_cd_unresolvable")):
            s = b.get(key)
            if s:
                print(f"    {lbl:<10} n={s['n']:<7} p50={s['p50']:.3e} "
                      f"p99={s['p99']:.3e} max={s['max']:.3e} "
                      f"(unresolvable 0/0 rows: {b[nun]})")
    print("per-model (all nine printed, no bootstrap):")
    for m, b in sorted(res["by_model"].items()):
        print(f"   {m}: {b['violations']} / {b['n']} violations")
    print("theorem vs modal-label correctness:")
    for k, b in sorted(res["naive_disagreement"].items()):
        if b["disagree"]:
            print(f"   {k}: disagree {b['disagree']}/{b['n']}, "
                  f"theorem right on {b['theorem_right']}/{b['disagree']}")
    save_json(res, args.out)


if __name__ == "__main__":
    main()
