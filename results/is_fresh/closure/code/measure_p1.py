"""P1 -- Tier-1 closure of Theorem 5.2 (binary entropy-alignment identity).

DESIGN v2.  Every quantity below appears in the STATEMENT of Theorem 5.2, and
the two sides of the identity are computed by independent routes.

PROTOCOL INVARIANT Q (binding, and the reason v2 exists).  `q` is never read
off a dataset label.  Each record declares a target distribution

    Q_eps(y = 1 | x) = 1 - eps  if the clean class is class 1, else eps,

and `q` is that declared law's own pointwise conditional.  `Q_0` is a
constructed *realizable* target distribution, not an appeal to CIFAR labels
being "effectively deterministic".  R, grad R and every risk difference use the
conditional expected cross-entropy under the declared q; sampled labels never
construct a theorem estimand.

Routes:
  g_H = autograd on H = -sum_k p_k log p_k    (Tent's own objective, written
        K-class so the code does not presuppose K = 2)
  g_R = autograd on R = -q log p - (1-q) log(1-p)
  g_s = autograd on s = (z_1 - z_0), read off the model's OUTPUT, so under a
        temperature wrapper it is the theorem's s_T = (z_1 - z_0)/T and not the
        unscaled logit difference.

The theorem's factorizations are residuals, never inputs:
  resid_H = || g_H + p(1-p) s g_s || / || g_H ||          (claim 1)
  resid_R = || g_R - (p - q) g_s || / || g_R ||           (claim 2)
and, because logit(p) == s identically, the sign law is evaluated as
  RHS = sign( s * (q - p) )
rather than by recomputing the log-odds from a saturated p -- which would
manufacture the numerical catastrophe the boundary analysis is trying to
characterize.

T1.2, the theorem's actual first-order content, is a derivative AT ZERO:
  d/d eta R(theta + eta v)|_0 = -alpha_ent ||g_R||,   v = -g_H/||g_H||,
measured by central difference, a route that never touches <g_H, g_R>.
The finite-step risk change survives as T3.1 under its own name and is NOT part
of any closure success rate.
"""
import argparse
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from common import (PAIRS, RecordWriter, binary_test_ids, clean_test_images,  # noqa: E402
                    corrupted_test_images, heartbeat, read_records, rel,
                    run_meta, save_json, set_seed, shift_cells)
from models import TemperedHead, build, subset_params  # noqa: E402

# T1.2 central-difference steps for the zero-point directional derivative.
# The grid spans the whole useful range rather than a guessed optimum: a
# central difference has a truncation error that falls with h and a
# cancellation error that grows as h -> 0, so the curve has a minimum and the
# minimum is the measurement.  Measured on this model in float64 the truncation
# branch runs 1e-3 -> 1e-6 and the floor sits near h = 1e-6 at ~1e-11 relative;
# below 1e-8 cancellation takes over again.  Reporting the whole curve, and its
# minimum, is what distinguishes "the identity closes" from "we picked a lucky
# h".  In float32 the floor is ~1e-4 and the closure is precision-limited --
# which is why T1.2's primary run is float64.
CD_STEPS = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]
# T3.1 finite-step grid -- BEYOND the theorem, reported separately.
ETA_GRID = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
# Declared target label laws Q_eps.  eps = 0 is the constructed realizable law.
EPS_GRID = [0.0, 0.1, 0.25, 0.4]
TEMPERATURES = [1.0, 2.0, 4.0]


def load_binary_model(ckpt_dir, pair, arch, seed, device, dtype):
    blob = torch.load(os.path.join(ckpt_dir, f"{pair}_{arch}_s{seed}.pt"),
                      map_location="cpu", weights_only=False)
    model = build(arch, num_classes=2)
    model.load_state_dict(blob["model"])
    model.to(device=device, dtype=dtype).eval()
    for p in model.parameters():
        p.requires_grad_(True)
    return model, blob.get("test_acc")


def flat_grad_of(scalar, params):
    gs = torch.autograd.grad(scalar, params, retain_graph=True, allow_unused=True)
    parts = []
    for g, prm in zip(gs, params):
        parts.append(torch.zeros_like(prm).reshape(-1) if g is None else g.reshape(-1))
    return torch.cat(parts)


def unflatten_like(vec, params):
    out, i = [], 0
    for prm in params:
        n = prm.numel()
        out.append(vec[i:i + n].view_as(prm))
        i += n
    return out


def risk_from_p(p, q):
    """R = -q log p - (1-q) log(1-p): the DEFINITION of the pointwise risk under
    the declared conditional q, evaluated in float64."""
    tiny = 1e-300
    return float(-(q * math.log(max(p, tiny)) + (1.0 - q) * math.log(max(1.0 - p, tiny))))


@torch.no_grad()
def _p_at_displaced(model, params, base, direction, alpha, x):
    """p at theta = base + alpha * direction, restoring nothing (caller does)."""
    for prm, b, d in zip(params, base, direction):
        prm.copy_(b + alpha * d)
    return float(F.softmax(model(x), dim=1)[0, 1].item())


def episode_quantities(model, params, x, y_clean_bin, eps_grid):
    """Every per-instance quantity for one image at one temperature."""
    out = {}
    z = model(x)                                    # (1, 2); already /T if tempered
    s = z[0, 1] - z[0, 0]                           # theorem's scalar logit s_T
    logp = F.log_softmax(z, dim=1)
    pv = logp.exp()
    p = float(pv[0, 1].item())
    out["s"] = float(s.item())
    out["p"] = p

    H = -(pv * logp).sum()                          # Tent's objective, K-class form
    g_H = flat_grad_of(H, params)
    g_s = flat_grad_of(s, params)
    nH = float(g_H.norm().item())
    ns = float(g_s.norm().item())
    out["gnorm_H"] = nH
    out["gnorm_s"] = ns
    out["H"] = float(H.item())

    # claim 1 residual: coefficient uses s, which IS logit(p) exactly
    if nH > 0:
        coef_H = -p * (1.0 - p) * out["s"]
        out["resid_H"] = float((g_H - coef_H * g_s).norm().item() / nH)
    else:
        out["resid_H"] = None

    # ORDER MATTERS.  Every autograd call that needs the forward graph runs
    # BEFORE any parameter is displaced: the displaced-p passes write the
    # parameters in place, which invalidates the retained graph and makes a
    # later `autograd.grad` fail outright (it does not silently return a wrong
    # number, but the ordering is load-bearing and is documented here so a
    # future edit does not reintroduce it).
    per_eps = []
    for eps in eps_grid:
        q = (1.0 - eps) if y_clean_bin == 1 else eps      # declared Q_eps
        R = -(q * logp[0, 1] + (1.0 - q) * logp[0, 0])
        g_R = flat_grad_of(R, params)
        nR = float(g_R.norm().item())
        rec = {"eps": eps, "q": q, "R": float(R.item()), "gnorm_R": nR}

        cos = (float(torch.dot(g_H, g_R).item() / (nH * nR))
               if (nR > 0 and nH > 0) else 0.0)          # Def 3.2 convention
        rec["alpha_ent"] = cos
        rec["abs_alpha"] = abs(cos)
        rec["inner"] = float(torch.dot(g_H, g_R).item())
        # RHS in the numerically stable form: logit(p) == s
        rhs = float(np.sign(out["s"] * (q - p)))
        rec["rhs_sign"] = rhs
        rec["agree"] = (int(np.sign(cos) == rhs)
                        if (rhs != 0.0 and cos != 0.0) else None)
        rec["resid_R"] = (float((g_R - (p - q) * g_s).norm().item() / nR)
                          if nR > 0 else None)

        # the deterministic naive comparator: MODAL-label correctness.
        # (a sampled label is a random event; the theorem's sign is a function
        #  of the full q, so the two are different objects and are not compared)
        rec["h_naive"] = 1 if ((p > 0.5) == (q > 0.5)) else -1
        rec["theorem_vs_naive_disagree"] = int(rhs != 0 and rhs != rec["h_naive"])

        rec["dirderiv_predicted"] = -cos * nR    # T1.2 target: -alpha_ent ||g_R||
        per_eps.append(rec)

    # --- only now displace the parameters ---------------------------------
    # p at displaced parameters is q-independent, so one pass covers every
    # declared law: 6 forwards for T1.2, 5 for T3.1.
    p_cd, p_eta = {}, {}
    if nH > 0:
        direction = [d.clone() for d in unflatten_like((-g_H / nH), params)]
        base = [prm.detach().clone() for prm in params]
        with torch.no_grad():
            for h in CD_STEPS:
                p_cd[(h, +1)] = _p_at_displaced(model, params, base, direction, +h, x)
                p_cd[(h, -1)] = _p_at_displaced(model, params, base, direction, -h, x)
            for eta in ETA_GRID:
                # T3.1 descends: theta - eta*g_H/||g_H|| = base + eta*v
                p_eta[eta] = _p_at_displaced(model, params, base, direction, +eta, x)
            for prm, b in zip(params, base):
                prm.copy_(b)
    out["p_cd"] = {f"{h}:{sgn}": v for (h, sgn), v in p_cd.items()}
    out["p_eta"] = {str(e): v for e, v in p_eta.items()}

    for rec in per_eps:
        q, pred = rec["q"], rec["dirderiv_predicted"]
        cd = {}
        for h in CD_STEPS:
            pp, pm = p_cd.get((h, +1)), p_cd.get((h, -1))
            if pp is None or pm is None:
                continue
            D = (risk_from_p(pp, q) - risk_from_p(pm, q)) / (2.0 * h)
            cd[str(h)] = {"D": D,
                          "rel_err": (abs(D - pred) / abs(pred)) if pred != 0 else None}
        rec["cd"] = cd
        errs = [v["rel_err"] for v in cd.values() if v["rel_err"] is not None]
        rec["cd_best_rel_err"] = min(errs) if errs else None
        R0 = risk_from_p(p, q)
        rec["dR_finite"] = {str(e): risk_from_p(pe, q) - R0 for e, pe in p_eta.items()}
    out["per_eps"] = per_eps
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, choices=list(PAIRS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arch", default="resnet26gn", choices=["resnet26gn", "wrn2810"])
    ap.add_argument("--subset", default="norm", choices=["norm", "all", "encoder"])
    ap.add_argument("--instances", type=int, default=200)
    ap.add_argument("--temperatures", default=",".join(str(t) for t in TEMPERATURES))
    ap.add_argument("--dtype", default="float32", choices=["float32", "float64"])
    ap.add_argument("--subsample-frac", type=float, default=1.0)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    temps = [float(t) for t in args.temperatures.split(",")]
    cells = shift_cells()
    if args.smoke:
        cells = cells[:2]
        args.instances = 4
        temps = temps[:2]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if args.dtype == "float32" else torch.float64
    set_seed(args.seed)

    model, ckpt_acc = load_binary_model(args.ckpt_dir, args.pair, args.arch,
                                        args.seed, device, dtype)
    ids, lab = binary_test_ids(args.data_root, args.pair)

    tag = f"p1_{args.pair}_{args.arch}_s{args.seed}_{args.subset}_{args.dtype}"
    if args.subsample_frac < 1.0:
        tag += f"_sub{args.subsample_frac:g}"
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    done_cells = set()
    if args.resume and os.path.exists(rec_path):
        for r in read_records(rec_path):
            done_cells.add((r["corruption"], r["severity"]))
        print(f"[p1] resume: {len(done_cells)} cells already recorded", flush=True)
    elif os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)

    t0 = time.time()
    n_written = 0
    for corr, sev in cells:
        if (corr, sev) in done_cells:
            continue
        xs = (clean_test_images(args.data_root, ids) if corr == "clean"
              else corrupted_test_images(args.data_root, corr, sev, ids))
        xs = torch.from_numpy(xs).to(device=device, dtype=dtype)
        # deterministic, cell-specific instance draw (no hash randomization)
        ss = np.random.SeedSequence(entropy=args.seed,
                                    spawn_key=(abs(hash(args.pair)) % 9973,
                                               abs(hash(corr)) % 9973, sev))
        rng = np.random.default_rng(ss)
        n_pick = min(args.instances, len(ids))
        sel = rng.choice(len(ids), size=n_pick, replace=False)
        if args.subsample_frac < 1.0:
            sel = sel[:max(1, int(round(args.subsample_frac * len(sel))))]
        for i in sel:
            x = xs[int(i):int(i) + 1]
            y_bin = int(lab[int(i)])
            for T in temps:
                m = TemperedHead(model, T) if T != 1.0 else model
                params, _ = subset_params(m, args.subset)
                q_out = episode_quantities(m, params, x, y_bin, EPS_GRID)
                writer.write({
                    "pair": args.pair, "arch": args.arch, "model_seed": args.seed,
                    "subset": args.subset, "dtype": args.dtype,
                    "corruption": corr, "severity": sev,
                    "test_id": int(ids[int(i)]), "row": int(i),
                    "y_clean_bin": y_bin, "T": T,
                    "n_params": int(sum(p.numel() for p in params)),
                    **q_out})
                n_written += 1
        writer.flush()
        print(f"[p1] {tag} {corr} s{sev}: {len(sel)} inst x {len(temps)} T "
              f"({n_written} recs, {time.time() - t0:.0f}s)", flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "cell": f"{corr}_{sev}",
                                       "records": n_written,
                                       "elapsed_s": time.time() - t0})
    writer.close()
    save_json({"meta": run_meta(args, {"ckpt_test_acc": ckpt_acc,
                                       "cd_steps": CD_STEPS, "eta_grid": ETA_GRID,
                                       "eps_grid": EPS_GRID, "temperatures": temps,
                                       "n_records": n_written}),
               "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[p1] DONE {tag} {n_written} records in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
