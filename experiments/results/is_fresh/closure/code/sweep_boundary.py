"""T1.5 -- adversarial boundary-resolution sweep.

A fixed-bin stratification tells you where agreement degrades on whatever
near-boundary episodes the data happened to supply.  This constructs them
instead: hold the network and the instance fixed, so s and p are fixed, and set
the declared conditional to

    q = p +/- delta,     delta = 1e-1, 1e-2, ..., 1e-12,

so the theorem's exact distance-to-degeneracy |q - p| is a controlled INPUT.
Then vary |s| through the temperature knob, since sign(p - 1/2) = sign(s) and
the theorem's other degeneracy is s -> 0.

Estimand: the numerical sign-resolution boundary -- the smallest delta (and the
smallest |s|) at which sign(alpha_ent) still reproduces sign(s (q - p)) -- in
float32 and float64 separately.

This is what makes the numerical attribution testable rather than rhetorical.
If the disagreements are arithmetic, the boundary should move by roughly the
ratio of the two machine epsilons when the precision changes.  If they were the
theorem's, the boundary would sit in the same place at both precisions.
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
                    heartbeat, rel, run_meta, save_json, set_seed)
from measure_p1 import flat_grad_of, load_binary_model  # noqa: E402
from models import TemperedHead, subset_params  # noqa: E402

DELTAS = [10.0 ** (-k) for k in range(1, 13)]
# Temperatures spanning |s| over decades: s_T = s/T, so large T drives the
# prediction toward the p = 1/2 degeneracy under experimental control.
TEMPERATURES = [1.0, 10.0, 100.0, 1000.0]


def probe(model, params, x):
    z = model(x)
    s = float((z[0, 1] - z[0, 0]).item())
    logp = F.log_softmax(z, dim=1)
    pv = logp.exp()
    p = float(pv[0, 1].item())
    H = -(pv * logp).sum()
    g_H = flat_grad_of(H, params)
    nH = float(g_H.norm().item())
    rows = []
    for delta in DELTAS:
        for sgn in (+1, -1):
            q = p + sgn * delta
            if not (0.0 < q < 1.0):
                continue
            R = -(q * logp[0, 1] + (1.0 - q) * logp[0, 0])
            g_R = flat_grad_of(R, params)
            nR = float(g_R.norm().item())
            cos = (float(torch.dot(g_H, g_R).item() / (nH * nR))
                   if (nH > 0 and nR > 0) else 0.0)
            rhs = float(np.sign(s * (q - p)))
            rows.append({"delta": delta, "sign": sgn, "q": q,
                         "alpha_ent": cos, "abs_alpha": abs(cos),
                         "rhs_sign": rhs, "gnorm_R": nR,
                         "agree": (int(np.sign(cos) == rhs)
                                   if (rhs != 0 and cos != 0) else None)})
    # smallest delta at which BOTH signs still resolve correctly
    resolved = []
    for d in DELTAS:
        rs = [r for r in rows if r["delta"] == d]
        if rs and all(r["agree"] == 1 for r in rs):
            resolved.append(d)
    return {"p": p, "s": s, "gnorm_H": nH,
            "delta_min_resolved": min(resolved) if resolved else None,
            "n_delta_tested": len({r["delta"] for r in rows}),
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, choices=list(PAIRS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arch", default="resnet26gn")
    ap.add_argument("--subset", default="norm")
    ap.add_argument("--instances", type=int, default=40)
    ap.add_argument("--dtype", default="float32", choices=["float32", "float64"])
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if args.dtype == "float32" else torch.float64
    set_seed(args.seed)
    model, _ = load_binary_model(args.ckpt_dir, args.pair, args.arch, args.seed,
                                 device, dtype)
    ids, lab = binary_test_ids(args.data_root, args.pair)
    xs = torch.from_numpy(clean_test_images(args.data_root, ids)).to(
        device=device, dtype=dtype)
    rng = np.random.default_rng(np.random.SeedSequence(
        entropy=args.seed, spawn_key=(9151,)))
    sel = rng.choice(len(ids), size=min(args.instances, len(ids)), replace=False)

    tag = f"bnd_{args.pair}_{args.arch}_s{args.seed}_{args.subset}_{args.dtype}"
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    if os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)
    t0, n = time.time(), 0
    for T in TEMPERATURES:
        m = TemperedHead(model, T) if T != 1.0 else model
        params, _ = subset_params(m, args.subset)
        for i in sel:
            res = probe(m, params, xs[int(i):int(i) + 1])
            writer.write({"pair": args.pair, "arch": args.arch,
                          "model_seed": args.seed, "subset": args.subset,
                          "dtype": args.dtype, "T": T,
                          "test_id": int(ids[int(i)]),
                          "y_clean_bin": int(lab[int(i)]), **res})
            n += 1
        writer.flush()
        print(f"[bnd] {tag} T={T}: {len(sel)} instances ({time.time() - t0:.0f}s)",
              flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "T": T, "records": n})
    writer.close()
    save_json({"meta": run_meta(args, {"deltas": DELTAS,
                                       "temperatures": TEMPERATURES,
                                       "n_records": n}),
               "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[bnd] DONE {tag} {n} probes in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
