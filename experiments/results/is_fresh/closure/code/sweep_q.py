"""T1.4 -- the q-sweep: Theorem 5.2 is a CALIBRATION law, not a correctness law.

Fix a model, an instance and theta, hence fix p and the modal prediction
argmax p.  Then sweep the declared target conditional q across (0,1),
recomputing grad_theta R by independent autograd at every q, and locate the
value q_flip at which the measured alignment changes sign.

Theorem 5.2 predicts

    alpha_ent = sign( s (q - p) ),

so the flip is exactly at q = p, and it happens WITHOUT the modal prediction
changing anywhere on the sweep.  Four eps points can only gesture at this; the
sweep shows it.

Legitimacy of sweeping q: q is the conditional of a DECLARED target
distribution (DESIGN v2 s0).  Sweeping it sweeps the target law, which the
theorem quantifies over -- Theorem 5.2 places no condition on Q.  No label is
sampled and none is used.

The grid is dense in the interior and refined geometrically around p, so
|q_flip - p| is resolved to ~1e-6 without spending points where nothing
happens.
"""
import argparse
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
                    corrupted_test_images, heartbeat, rel, run_meta, save_json,
                    set_seed, shift_cells)
from measure_p1 import flat_grad_of, load_binary_model  # noqa: E402
from models import subset_params  # noqa: E402


def q_grid(p, coarse=99, n_ref=12):
    """Coarse uniform grid plus a geometric refinement bracketing p."""
    g = list(np.linspace(0.01, 0.99, coarse))
    for k in range(1, n_ref + 1):
        d = 10.0 ** (-k / 2.0)
        for cand in (p - d, p + d):
            if 0.0 < cand < 1.0:
                g.append(float(cand))
    return sorted(set(float(v) for v in g))


def sweep_one(model, params, x, dtype):
    z = model(x)
    s = float((z[0, 1] - z[0, 0]).item())
    logp = F.log_softmax(z, dim=1)
    pv = logp.exp()
    p = float(pv[0, 1].item())
    H = -(pv * logp).sum()
    g_H = flat_grad_of(H, params)
    nH = float(g_H.norm().item())

    pts = []
    for q in q_grid(p):
        R = -(q * logp[0, 1] + (1.0 - q) * logp[0, 0])
        g_R = flat_grad_of(R, params)
        nR = float(g_R.norm().item())
        cos = (float(torch.dot(g_H, g_R).item() / (nH * nR))
               if (nH > 0 and nR > 0) else 0.0)
        pts.append({"q": q, "alpha_ent": cos, "abs_alpha": abs(cos),
                    "gnorm_R": nR,
                    "rhs_sign": float(np.sign(s * (q - p))),
                    # modal prediction is a property of p alone: constant on the
                    # whole sweep by construction, recorded so the claim is
                    # evidenced rather than asserted
                    "argmax_p": int(p > 0.5),
                    "argmax_q": int(q > 0.5)})

    # measured flip location: the midpoint of the adjacent pair that straddles
    # the sign change (the grid is sorted in q)
    flips = []
    for a, b in zip(pts[:-1], pts[1:]):
        sa, sb = np.sign(a["alpha_ent"]), np.sign(b["alpha_ent"])
        if sa != 0 and sb != 0 and sa != sb:
            flips.append(0.5 * (a["q"] + b["q"]))
    return {"p": p, "s": s, "gnorm_H": nH,
            "n_flips": len(flips),
            "q_flip": flips[0] if len(flips) == 1 else None,
            "q_flip_err": (abs(flips[0] - p) if len(flips) == 1 else None),
            "modal_pred_constant": int(len({pt["argmax_p"] for pt in pts}) == 1),
            "points": pts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, choices=list(PAIRS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arch", default="resnet26gn")
    ap.add_argument("--subset", default="norm")
    ap.add_argument("--instances", type=int, default=25,
                    help="instances per shift cell; cells are chosen to span p")
    ap.add_argument("--cells", default="clean,gaussian_noise:3,contrast:5")
    ap.add_argument("--dtype", default="float64",
                    choices=["float32", "float64"],
                    help="float64 by default: the sweep resolves |q_flip - p| "
                         "to ~1e-6 and must not be precision-limited")
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        args.instances = 3
        args.cells = "clean"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if args.dtype == "float32" else torch.float64
    set_seed(args.seed)
    model, _ = load_binary_model(args.ckpt_dir, args.pair, args.arch, args.seed,
                                 device, dtype)
    ids, lab = binary_test_ids(args.data_root, args.pair)
    params, _ = subset_params(model, args.subset)

    valid = {(c, s) for c, s in shift_cells()}
    cells = []
    for tok in args.cells.split(","):
        if ":" in tok:
            c, s = tok.split(":")
            cells.append((c, int(s)))
        else:
            cells.append((tok, 0))
    for c in cells:
        if c not in valid:
            raise ValueError(f"unknown shift cell {c}")

    tag = f"qsweep_{args.pair}_{args.arch}_s{args.seed}_{args.subset}_{args.dtype}"
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    if os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)

    t0, n = time.time(), 0
    for corr, sev in cells:
        xs = (clean_test_images(args.data_root, ids) if corr == "clean"
              else corrupted_test_images(args.data_root, corr, sev, ids))
        xs = torch.from_numpy(xs).to(device=device, dtype=dtype)
        rng = np.random.default_rng(np.random.SeedSequence(
            entropy=args.seed, spawn_key=(7717, abs(hash(corr)) % 9973, sev)))
        sel = rng.choice(len(ids), size=min(args.instances, len(ids)), replace=False)
        for i in sel:
            res = sweep_one(model, params, xs[int(i):int(i) + 1], dtype)
            writer.write({"pair": args.pair, "arch": args.arch,
                          "model_seed": args.seed, "subset": args.subset,
                          "dtype": args.dtype, "corruption": corr,
                          "severity": sev, "test_id": int(ids[int(i)]),
                          "row": int(i), "y_clean_bin": int(lab[int(i)]), **res})
            n += 1
        writer.flush()
        print(f"[qsweep] {tag} {corr} s{sev}: {len(sel)} instances "
              f"({time.time() - t0:.0f}s)", flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "cell": f"{corr}_{sev}",
                                       "records": n})
    writer.close()
    save_json({"meta": run_meta(args, {"n_records": n}), "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[qsweep] DONE {tag} {n} sweeps in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
