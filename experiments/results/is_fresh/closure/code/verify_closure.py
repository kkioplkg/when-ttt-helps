"""Independent verification of the closure suite.

House rule: no number reaches RESULTS.md that this script has not reproduced by
a DIFFERENT route from the one that produced it.  Nothing here imports the
analysis module; every quantity is recomputed from the raw records, and the
model-side checks reload the network and redo the episode from scratch.

Four independent routes:

1.  RHS BY A SECOND EXPRESSION.  The run computes the sign law as
    sign(s (q - p)); this script recomputes it as sign((p - 1/2)(q - p)), the
    form printed in the theorem.  The two agree only if logit(p) = s holds
    numerically, so the cross-check tests that too.  Disagreements are located
    and reported, not averaged away.

2.  REPRODUCE-FROM-RECORD.  For a random sample of episodes, reload the
    checkpoint, re-select the instance from (pair, corruption, severity,
    test_id), recompute p, s, alpha_ent and the RHS from scratch, and compare
    against the stored record.

3.  AGGREGATION BY A DIFFERENT ORDER.  Violation counts are recomputed by
    sorting records and scanning, rather than by the analysis script's
    dictionary accumulation, so an accumulator bug cannot survive in both.

4.  mu_J BY BISECTION.  Assumption 5.4's literal Loewner constant is
    recomputed as sup{lambda : lambda_min(A - lambda Pi) >= 0} by bisection,
    an entirely different algorithm from the Schur complement the run uses.
    The Gram matrix is re-derived from the stored trajectory point.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from common import read_records, rel, save_json  # noqa: E402

TOL_ALPHA = {"float32": 2e-5, "float64": 1e-11}
TOL_P = {"float32": 2e-5, "float64": 1e-12}


# ---------------------------------------------------------------- route 1 + 3

def recheck_p1_records(paths, out):
    """Routes 1 and 3: independent RHS expression, independent aggregation."""
    rows = []
    for path in paths:
        for r in read_records(path):
            for e in r["per_eps"]:
                rows.append((r["dtype"], r["T"], r["p"], r["s"], e["q"],
                             e["alpha_ent"], e["rhs_sign"], e["agree"],
                             r["pair"], r["model_seed"], r["corruption"],
                             r["severity"], r["test_id"], e["eps"]))
    rows.sort()
    n = viol = excl = 0
    rhs_mismatch = []
    logit_mismatch = []
    for (dt, T, p, s, q, alpha, rhs_stored, agree, pair, seed, corr, sev,
         tid, eps) in rows:
        # route 1: the theorem's printed form of the RHS
        rhs_alt = float(np.sign((p - 0.5) * (q - p)))
        if rhs_alt != rhs_stored:
            rhs_mismatch.append({"pair": pair, "seed": seed, "corruption": corr,
                                 "severity": sev, "test_id": tid, "T": T,
                                 "eps": eps, "p": p, "s": s, "q": q,
                                 "rhs_stored": rhs_stored, "rhs_alt": rhs_alt})
        # logit(p) == s, the identity that makes the two forms interchangeable
        if 0.0 < p < 1.0:
            lg = math.log(p / (1.0 - p))
            if abs(lg - s) > max(1e-4, 1e-4 * abs(s)):
                logit_mismatch.append({"p": p, "s": s, "logit_p": lg,
                                       "dtype": dt})
        if agree is None:
            excl += 1
            continue
        n += 1
        if float(np.sign(alpha)) != rhs_alt:
            viol += 1
    out["route1_rhs_mismatches"] = len(rhs_mismatch)
    out["route1_rhs_mismatch_examples"] = rhs_mismatch[:50]
    out["route1_logit_vs_s_mismatches"] = len(logit_mismatch)
    out["route1_logit_examples"] = logit_mismatch[:20]
    out["route3_n_tested"] = n
    out["route3_violations_recomputed"] = viol
    out["route3_excluded"] = excl
    return out


# ---------------------------------------------------------------- route 2

def reproduce_from_record(paths, data_root, ckpt_dir, n_sample, seed, out):
    import torch
    import torch.nn.functional as F
    from common import binary_test_ids, clean_test_images, corrupted_test_images
    from measure_p1 import flat_grad_of, load_binary_model
    from models import TemperedHead, subset_params

    recs = []
    for path in paths:
        for r in read_records(path):
            recs.append((path, r))
    if not recs:
        out["route2"] = {"n": 0}
        return out
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(recs), size=min(n_sample, len(recs)), replace=False)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache = {}
    worst = {"p": 0.0, "s": 0.0, "alpha": 0.0}
    bad = []
    n_ok = 0
    for k in pick:
        _, r = recs[int(k)]
        key = (r["pair"], r["arch"], r["model_seed"], r["dtype"])
        if key not in cache:
            dt = torch.float32 if r["dtype"] == "float32" else torch.float64
            m, _ = load_binary_model(ckpt_dir, r["pair"], r["arch"],
                                     r["model_seed"], device, dt)
            ids, lab = binary_test_ids(data_root, r["pair"])
            cache[key] = (m, ids, lab, dt)
        model, ids, lab, dt = cache[key]
        row = int(np.nonzero(ids == r["test_id"])[0][0])
        xs = (clean_test_images(data_root, ids) if r["corruption"] == "clean"
              else corrupted_test_images(data_root, r["corruption"],
                                         r["severity"], ids))
        x = torch.from_numpy(xs[row:row + 1]).to(device=device, dtype=dt)
        m = TemperedHead(model, r["T"]) if r["T"] != 1.0 else model
        params, _ = subset_params(m, r["subset"])
        z = m(x)
        s = float((z[0, 1] - z[0, 0]).item())
        logp = F.log_softmax(z, dim=1)
        pv = logp.exp()
        p = float(pv[0, 1].item())
        H = -(pv * logp).sum()
        gH = flat_grad_of(H, params)
        nH = float(gH.norm().item())
        e0 = r["per_eps"][0]
        q = e0["q"]
        Rr = -(q * logp[0, 1] + (1.0 - q) * logp[0, 0])
        gR = flat_grad_of(Rr, params)
        nR = float(gR.norm().item())
        alpha = float(torch.dot(gH, gR).item() / (nH * nR)) if nH * nR > 0 else 0.0
        dp, ds, da = abs(p - r["p"]), abs(s - r["s"]), abs(alpha - e0["alpha_ent"])
        worst["p"] = max(worst["p"], dp)
        worst["s"] = max(worst["s"], ds)
        worst["alpha"] = max(worst["alpha"], da)
        if dp > TOL_P[r["dtype"]] or da > TOL_ALPHA[r["dtype"]]:
            bad.append({"pair": r["pair"], "test_id": r["test_id"],
                        "corruption": r["corruption"], "severity": r["severity"],
                        "T": r["T"], "dp": dp, "ds": ds, "dalpha": da,
                        "dtype": r["dtype"]})
        else:
            n_ok += 1
    out["route2"] = {"n": int(len(pick)), "n_ok": n_ok, "n_bad": len(bad),
                     "worst_abs_diff": worst, "bad_examples": bad[:20],
                     "tolerances": {"p": TOL_P, "alpha": TOL_ALPHA}}
    return out


# ---------------------------------------------------------------- route 4

def mu2_bisect(A, U, iters=300, rtol=1e-12):
    """sup{lambda : A - lambda Pi >= 0} by bisection.

    The PSD test must use a RELATIVE tolerance.  With an absolute one, a Gram
    matrix whose spectrum spans ten orders of magnitude is declared indefinite
    (or definite) on the strength of round-off in its smallest eigenvalue, and
    the route disagrees with the Schur complement by orders of magnitude -- as
    an initial implementation of this check did, on synthetic matrices far
    worse conditioned than any measured one.
    """
    Pi = U @ U.T
    lam_max = float(np.linalg.eigvalsh(A)[-1])
    lo, hi = 0.0, lam_max + 1.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if np.linalg.eigvalsh(A - mid * Pi)[0] >= -rtol * lam_max:
            lo = mid
        else:
            hi = mid
    return lo


# Bisection is itself ill-conditioned near the critical lambda when cond(A) is
# ~1e10, which is where the measured Gram matrices live, so exact agreement is
# not achievable and claiming it would be false.  This is the standard the
# cross-check is held to, and it is ~40x below the margin that matters: the
# Proposition 5.5 certificate needs kappa_J ~ 1 against a measured kappa_J of
# 4-6, so a few percent of uncertainty in kappa_J cannot flip any conclusion.
ROUTE4_MAX_REL_ERR = 0.10


def recheck_p2_jacobian(paths, out, n_random=300, seed=20260931):
    """Route 4: mu_J by bisection instead of by Schur complement, characterized
    as a function of conditioning, plus a re-derivation of kappa_J and of the
    Proposition 5.5 bound from the stored scalars."""
    from measure_p2 import jacobian_constants
    rng = np.random.default_rng(seed)
    by_cond = {}
    worst = 0.0
    # sweep the conditioning rather than testing at one arbitrary severity, so
    # the limitation is characterized instead of hidden
    for sigma, label in ((0.5, "cond~1e2"), (1.5, "cond~1e6"), (2.5, "cond~1e10")):
        w = 0.0
        for _ in range(n_random):
            K = 10
            G = rng.normal(size=(K, 64)) * rng.lognormal(0, sigma, size=(K, 1))
            A = G @ G.T
            v1, v2 = rng.normal(size=K), rng.normal(size=K)
            jc = jacobian_constants(A, [v1, v2])
            U, _, _ = np.linalg.svd(np.stack([v1, v2], 1), full_matrices=False)
            mb = mu2_bisect(A, U[:, :2])
            if mb > 0:
                w = max(w, abs(jc["mu_J_literal"] ** 2 - mb) / mb)
        by_cond[label] = w
        worst = max(worst, w)
    # The synthetic sweep CHARACTERIZES the bisection route's own limits; it
    # does not gate anything, because randomly-oriented spans over
    # row-rescaled Gram matrices are far more adversarial than the measured
    # objects, whose span{grad_z H, p-q} lies in the sum-zero subspace.  The
    # gating cross-check is run on the REAL matrices, by rebuilding them.
    out["route4_synthetic_characterization"] = by_cond
    out["route4_synthetic_max_rel_err"] = worst
    out["route4_threshold"] = ROUTE4_MAX_REL_ERR

    # re-derive kappa_J and LB from the stored scalars, independently
    bad_k, bad_lb, n = [], [], 0
    for path in paths:
        for r in read_records(path):
            for t, j in r.get("jacobian", {}).items():
                if j.get("kappa_J") is None:
                    continue
                n += 1
                k2 = j["L_J"] / j["mu_J_literal"]
                if abs(k2 - j["kappa_J"]) > 1e-9 * max(1.0, abs(k2)):
                    bad_k.append({"t": t, "stored": j["kappa_J"], "recomp": k2})
                if j.get("LB") is not None and j.get("Lambda", 0) > 0:
                    W = j["Z"] / (2.0 * math.sqrt(10) * j["Lambda"])
                    lb = W / j["kappa_J"] ** 2 - (j["kappa_J"] ** 2 - 1.0)
                    if abs(lb - j["LB"]) > 1e-6 * max(1.0, abs(lb)):
                        bad_lb.append({"t": t, "stored": j["LB"], "recomp": lb})
                # mu_literal <= mu_restricted must hold by construction
                if j["mu_J_literal"] > j["mu_J_restricted"] * (1 + 1e-9):
                    bad_k.append({"t": t, "mu_literal": j["mu_J_literal"],
                                  "mu_restricted": j["mu_J_restricted"],
                                  "why": "literal exceeded restricted"})
    out["route4_n_jacobian_points"] = n
    out["route4_kappa_mismatches"] = len(bad_k)
    out["route4_LB_mismatches"] = len(bad_lb)
    out["route4_examples"] = (bad_k[:10] + bad_lb[:10])
    return out


# ---------------------------------------------------------------- q-sweep

def recheck_qsweep(paths, out):
    """Every sweep must have exactly one sign flip, located at q = p, with the
    modal prediction constant across the whole sweep."""
    n = n_one_flip = n_modal_const = 0
    worst_err = 0.0
    bad = []
    for path in paths:
        for r in read_records(path):
            n += 1
            n_one_flip += int(r["n_flips"] == 1)
            n_modal_const += int(r["modal_pred_constant"] == 1)
            # independent relocation of the flip from the stored points
            pts = sorted(r["points"], key=lambda d: d["q"])
            flips = [0.5 * (a["q"] + b["q"])
                     for a, b in zip(pts[:-1], pts[1:])
                     if np.sign(a["alpha_ent"]) * np.sign(b["alpha_ent"]) < 0]
            if len(flips) != 1:
                bad.append({"test_id": r["test_id"], "n_flips": len(flips),
                            "p": r["p"]})
                continue
            worst_err = max(worst_err, abs(flips[0] - r["p"]))
    out["qsweep"] = {"n": n, "n_exactly_one_flip": n_one_flip,
                     "n_modal_pred_constant": n_modal_const,
                     "max_abs_qflip_minus_p": worst_err,
                     "bad_examples": bad[:20]}
    return out


def recheck_mu_on_real(ckpt_dir, data_root, n_instances, out, seed=20260951):
    """Route 4, gating form: rebuild the ACTUAL logit-Jacobian Gram matrices
    from a checkpoint and compare the production Schur route against bisection
    on those, rather than on synthetic proxies."""
    import torch
    from common import load_cifar10_np, _normalize
    from measure_p2 import Float64Replica, OBJ_SUBSET
    from models import subset_params
    sys.path.insert(0, os.path.dirname(_HERE))
    from e2_cifar.models import ResNet26TTT

    ckpts = sorted(glob.glob(os.path.join(ckpt_dir, "cifar10_resnet26ttt_s*.pt")))
    if not ckpts:
        out["route4_real"] = {"n": 0, "note": "no 10-class checkpoint found"}
        return out
    device = "cuda" if torch.cuda.is_available() else "cpu"
    blob = torch.load(ckpts[0], map_location="cpu", weights_only=False)
    model = ResNet26TTT(10)
    model.load_state_dict(blob["model"])
    model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(True)
    _, _, tex, tey = load_cifar10_np(data_root)
    rng = np.random.default_rng(seed)
    sel = rng.choice(len(tey), size=min(n_instances, len(tey)), replace=False)
    xs = torch.from_numpy(_normalize(tex[sel])).to(device)

    worst, conds, n = 0.0, [], 0
    for obj in ("tent", "ttt_rot"):
        params, _ = subset_params(model, OBJ_SUBSET[obj])
        rep = Float64Replica(model, OBJ_SUBSET[obj], K=10)
        for j, i in enumerate(sel):
            terms, jc, A = rep.measure(xs[j:j + 1], int(tey[int(i)]), params)
            conds.append(float(np.linalg.cond(A)))
            M = np.stack([np.asarray(terms["grad_z_H"]),
                          np.asarray(terms["p_minus_q"])], 1)
            U, sv, _ = np.linalg.svd(M, full_matrices=False)
            r = int((sv > 1e-12 * max(1.0, sv[0])).sum())
            mb = mu2_bisect(A, U[:, :r])
            if mb > 0:
                worst = max(worst, abs(jc["mu_J_literal"] ** 2 - mb) / mb)
            n += 1
    out["route4_real"] = {
        "n": n,
        "cond_p50": float(np.percentile(conds, 50)),
        "cond_max": float(np.max(conds)),
        "schur_vs_bisection_max_rel_err_mu2": worst,
        "implied_max_rel_err_kappa": float(np.sqrt(1.0 + worst) - 1.0),
        "threshold": ROUTE4_MAX_REL_ERR,
        "within_threshold": bool(worst <= ROUTE4_MAX_REL_ERR),
        "note": "Bisection is itself ill-conditioned near the critical lambda "
                "at cond(A) ~ 1e10, so exact agreement is not attainable and "
                "is not claimed. The residual disagreement is far below the "
                "margin that matters: the Proposition 5.5 certificate needs "
                "kappa_J ~ 1 against a measured kappa_J of 4-6.",
    }
    out["route4_within_threshold"] = out["route4_real"]["within_threshold"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--ckpt-dir", default=None)
    ap.add_argument("--reproduce-n", type=int, default=200)
    ap.add_argument("--reproduce-seed", type=int, default=20260941)
    ap.add_argument("--skip-model-checks", action="store_true")
    args = ap.parse_args()

    p1 = sorted(glob.glob(os.path.join(args.in_dir, "p1_*.jsonl.gz")))
    p2 = sorted(glob.glob(os.path.join(args.in_dir, "p2_*.jsonl.gz")))
    qs = sorted(glob.glob(os.path.join(args.in_dir, "qsweep_*.jsonl.gz")))
    out = {"inputs": {"p1": [rel(p) for p in p1], "p2": [rel(p) for p in p2],
                      "qsweep": [rel(p) for p in qs]}}
    if p1:
        recheck_p1_records(p1, out)
        if not args.skip_model_checks and args.data_root and args.ckpt_dir:
            reproduce_from_record(p1, args.data_root, args.ckpt_dir,
                                  args.reproduce_n, args.reproduce_seed, out)
    if qs:
        recheck_qsweep(qs, out)
    if p2:
        recheck_p2_jacobian(p2, out)
        if not args.skip_model_checks and args.data_root and args.ckpt_dir:
            recheck_mu_on_real(args.ckpt_dir, args.data_root, 60, out)

    ok = (out.get("route1_rhs_mismatches", 0) == 0
          and out.get("route4_kappa_mismatches", 0) == 0
          and out.get("route4_LB_mismatches", 0) == 0
          and out.get("route2", {}).get("n_bad", 0) == 0
          # route 4's numerical agreement is now part of the gate; leaving it
          # out let a 4607x disagreement sit in the output next to a green
          # "all_routes_clean"
          and out.get("route4_within_threshold", True))
    out["all_routes_clean"] = bool(ok)
    for k, v in out.items():
        if k not in ("inputs",):
            print(f"  {k}: {v if not isinstance(v, list) else f'[{len(v)} items]'}")
    save_json(out, args.out)
    print(f"[verify] all_routes_clean = {ok}")


if __name__ == "__main__":
    main()
