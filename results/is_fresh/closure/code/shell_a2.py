"""T2.5 -- neighbourhood shell search for A2 counterexamples.

A2 constrains EVERY point of a region Theta_loc.  A trajectory is 21 points, so
it has very little chance of meeting a counterexample even when the region is
full of them.  This raises the falsification power without pretending to verify
anything, by sampling preregistered shells around each trajectory point:

    radii   r in {1e-4, 1e-3, 1e-2} x ||theta_t||   (relative, preregistered)
    n_dir   random unit directions per shell
    report  min over the sampled shell of <gbar, grad R> and of alpha

The logic is one-sided and stays one-sided.  Sampling a ball can only
UNDER-estimate how negative the alignment gets inside it, so:

  * a non-positive inner product found anywhere in a shell falsifies A2 on every
    Theta_loc containing that shell -- and since the shells are centred on the
    realized path and we take Theta_loc to be a ball containing them, A4 holds
    by construction and the falsification is unconditional;
  * a uniformly positive sample proves nothing at all about the region.

The interesting outcome is the asymmetric one: a trajectory that never goes
negative while a 1e-3-relative perturbation does.  That is
"persistent alignment is not locally robust", and it is reported exactly as
measured -- as the minimum over a finite sample, never as a region infimum.

The same disciplines as measure_p2 apply: gbar is EXACT for the rotation
objective (enumeration over the four rotations, not Monte Carlo), and grad R is
the gradient of the conditional expected cross-entropy under the declared
deterministic target law Q_0.
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

_HERE = os.path.dirname(os.path.abspath(__file__))
_TTT = os.path.dirname(_HERE)
for _p in (_HERE, _TTT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common import (RecordWriter, corrupted_test_images, heartbeat,  # noqa: E402
                    load_cifar10_np, rel, run_meta, save_json, set_seed,
                    shift_cells, _normalize)
from e2_cifar.models import ResNet26TTT  # noqa: E402
from measure_p1 import flat_grad_of, unflatten_like  # noqa: E402
from measure_p2 import (OBJ_SUBSET, entropy_loss, rotation_gbar,  # noqa: E402
                        rotation_loss_stochastic)
from models import subset_params  # noqa: E402

# preregistered, relative to ||theta_t||; frozen before any sweep
SHELL_RADII = [1e-4, 1e-3, 1e-2]
SHELL_STEPS = [0, 5, 20]          # trajectory points around which to search


def a2_quantities(model, params, x, yt, objective):
    """<gbar, grad R>, alpha and rho at the CURRENT parameters."""
    R = F.cross_entropy(model(x), yt)
    g_R = flat_grad_of(R, params)
    g_bar = (flat_grad_of(entropy_loss(model, x), params) if objective == "tent"
             else rotation_gbar(model, params, x))
    nR = float(g_R.norm().item())
    nG = float(g_bar.norm().item())
    inner = float(torch.dot(g_bar, g_R).item())
    return {"inner": inner, "gnorm_bar": nG, "gnorm_R": nR,
            "alpha": (inner / (nG * nR)) if (nG > 0 and nR > 0) else 0.0,
            "rho": (nG / nR) if nR > 0 else None,
            "nondegenerate": int(nG > 0 and nR > 0)}


def search_shell(model, params, x, yt, objective, rng, n_dir):
    """Sample the preregistered shells around the current parameters."""
    base = [p.detach().clone() for p in params]
    theta_norm = float(torch.cat([b.reshape(-1) for b in base]).norm().item())
    d = sum(p.numel() for p in params)
    out = []
    for r_rel in SHELL_RADII:
        radius = r_rel * theta_norm
        worst = None
        n_falsify = 0
        for _ in range(n_dir):
            v = torch.randn(d, generator=rng, device=base[0].device,
                            dtype=base[0].dtype)
            v = v / v.norm()
            parts = unflatten_like(v, params)
            with torch.no_grad():
                for prm, b, dv in zip(params, base, parts):
                    prm.copy_(b + radius * dv)
            q = a2_quantities(model, params, x, yt, objective)
            if q["nondegenerate"] and q["inner"] <= 0:
                n_falsify += 1
            if worst is None or q["inner"] < worst["inner"]:
                worst = q
        with torch.no_grad():
            for prm, b in zip(params, base):
                prm.copy_(b)
        out.append({"r_rel": r_rel, "radius": radius, "n_dir": n_dir,
                    "n_falsifying_directions": n_falsify,
                    "min_inner": worst["inner"], "alpha_at_min": worst["alpha"],
                    "rho_at_min": worst["rho"],
                    "falsifies_A2": int(n_falsify > 0)})
    return theta_norm, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--objective", required=True, choices=list(OBJ_SUBSET))
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--instances", type=int, default=50)
    ap.add_argument("--n-dir", type=int, default=8)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    cells = shift_cells()
    if args.smoke:
        cells, args.instances, args.n_dir = cells[:2], 2, 3

    device = "cuda" if torch.cuda.is_available() else "cpu"
    set_seed(args.seed)
    blob = torch.load(os.path.join(args.ckpt_dir,
                                   f"cifar10_resnet26ttt_s{args.seed}.pt"),
                      map_location="cpu", weights_only=False)
    model = ResNet26TTT(10)
    model.load_state_dict(blob["model"])
    model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(True)
    params, _ = subset_params(model, OBJ_SUBSET[args.objective])
    loss_fn = entropy_loss if args.objective == "tent" else rotation_loss_stochastic

    _, _, tex, tey = load_cifar10_np(args.data_root)
    ids = np.arange(len(tey))

    tag = f"shell_{args.objective}_s{args.seed}_lr{args.lr:g}"
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    if os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)

    t0, n = time.time(), 0
    for corr, sev in cells:
        xs = (_normalize(tex) if corr == "clean"
              else corrupted_test_images(args.data_root, corr, sev, ids))
        xs = torch.from_numpy(xs).to(device)
        pick = np.random.default_rng(np.random.SeedSequence(
            entropy=args.seed, spawn_key=(6197, abs(hash(corr)) % 9973, sev)))
        sel = pick.choice(len(tey), size=min(args.instances, len(tey)),
                          replace=False)
        for j, i in enumerate(sel):
            x = xs[int(i):int(i) + 1]
            yt = torch.tensor([int(tey[int(i)])], device=device)
            gen = torch.Generator(device=device).manual_seed(
                int(args.seed) * 7919 + int(i) * 31 + j)
            snap = [p.detach().clone() for p in params]
            per_t = []
            for t in range(args.steps + 1):
                if t in SHELL_STEPS:
                    on_path = a2_quantities(model, params, x, yt, args.objective)
                    tn, shells = search_shell(model, params, x, yt,
                                              args.objective, gen, args.n_dir)
                    # the asymmetric outcome this instrument exists to find
                    asym = int(on_path["nondegenerate"] and on_path["inner"] > 0
                               and any(s["falsifies_A2"] for s in shells))
                    per_t.append({"t": t, "theta_norm": tn,
                                  "on_path": on_path, "shells": shells,
                                  "on_path_positive_shell_negative": asym})
                if t == args.steps:
                    break
                loss = (loss_fn(model, x) if args.objective == "tent"
                        else loss_fn(model, x, int(i) * 10007 + t))
                grads = torch.autograd.grad(loss, params, allow_unused=True)
                with torch.no_grad():
                    for prm, g in zip(params, grads):
                        if g is not None:
                            prm.sub_(args.lr * g)      # plain SGD, S2's update
            with torch.no_grad():
                for prm, s0 in zip(params, snap):
                    prm.copy_(s0)
            writer.write({"objective": args.objective, "model_seed": args.seed,
                          "subset": OBJ_SUBSET[args.objective], "lr": args.lr,
                          "corruption": corr, "severity": sev,
                          "test_id": int(i), "y_clean": int(tey[int(i)]),
                          "n_dir": args.n_dir, "shell_radii": SHELL_RADII,
                          "shell_steps": SHELL_STEPS, "points": per_t,
                          "any_asymmetric": int(any(
                              p["on_path_positive_shell_negative"] for p in per_t))})
            n += 1
        writer.flush()
        print(f"[shell] {tag} {corr} s{sev}: {len(sel)} episodes "
              f"({n} total, {time.time() - t0:.0f}s)", flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "cell": f"{corr}_{sev}",
                                       "episodes": n})
    writer.close()
    save_json({"meta": run_meta(args, {"shell_radii": SHELL_RADII,
                                       "shell_steps": SHELL_STEPS,
                                       "n_episodes": n}),
               "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[shell] DONE {tag} {n} episodes in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
