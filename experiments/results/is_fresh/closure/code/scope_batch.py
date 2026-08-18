"""T2.1 -- where Theorem 5.2 stops: collinearity loss at N > 1.

Theorem 5.2 is an N = 1 statement.  Its whole mechanism is that H and R depend
on theta only through the scalar logit s, so both gradients are multiples of
grad s and the cosine is exactly +-1.  At batch size N the two gradients are

    g_H^B = (1/N) sum_i a_i grad s_i ,     g_R^B = (1/N) sum_i b_i grad s_i ,

different weightings of N generally-independent vectors, so they are not
collinear and there is NO batch scalar that Theorem 5.2 defines as a
right-hand side.

Reporting an "agreement rate" at N > 1 would therefore be reporting agreement
with a quantity the theorem does not define -- which is why this script reports
ONLY |cos(g_H^B, g_R^B)| and its departure from 1.  There is no `agree` field
here, deliberately.

What makes the departure interpretable is the per-instance sign composition of
the batch, which the theorem DOES define: each member has its own
alpha_i = sign(s_i (q_i - p_i)).  A batch whose members all carry the same sign
should lose collinearity slowly; a mixed batch should lose it fast.  Recording
that covariate turns "the cosine is no longer 1" into a statement about why.
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
from measure_p1 import EPS_GRID, flat_grad_of, load_binary_model  # noqa: E402
from models import subset_params  # noqa: E402

BATCH_SIZES = [1, 2, 4, 8, 16]


def batch_quantities(model, params, x, y_bin, eps):
    """Batch-mean entropy and batch-mean risk under the declared law Q_eps."""
    z = model(x)                                    # (N, 2)
    s = z[:, 1] - z[:, 0]
    logp = F.log_softmax(z, dim=1)
    pv = logp.exp()
    p = pv[:, 1]

    # declared Q_eps conditional for each member
    q = torch.where(torch.as_tensor(y_bin, device=x.device) == 1,
                    torch.full_like(p, 1.0 - eps), torch.full_like(p, eps))

    H = -(pv * logp).sum(1).mean()                  # batch-mean entropy
    R = -(q * logp[:, 1] + (1.0 - q) * logp[:, 0]).mean()   # batch-mean risk
    g_H = flat_grad_of(H, params)
    g_R = flat_grad_of(R, params)
    nH, nR = float(g_H.norm().item()), float(g_R.norm().item())
    cos = (float(torch.dot(g_H, g_R).item() / (nH * nR))
           if (nH > 0 and nR > 0) else 0.0)

    pn, qn, sn = p.detach().cpu().numpy(), q.detach().cpu().numpy(), s.detach().cpu().numpy()
    signs = np.sign(sn * (qn - pn))                 # the theorem's per-member sign
    n_pos = int((signs > 0).sum())
    n_neg = int((signs < 0).sum())
    frac_major = max(n_pos, n_neg) / max(len(signs), 1)
    return {"eps": eps, "N": int(x.size(0)),
            "abs_cos": abs(cos), "cos": cos,
            "departure_from_1": 1.0 - abs(cos),
            "gnorm_H": nH, "gnorm_R": nR,
            "n_sign_pos": n_pos, "n_sign_neg": n_neg,
            "sign_majority_frac": frac_major,
            "sign_homogeneous": int(n_pos == 0 or n_neg == 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, choices=list(PAIRS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arch", default="resnet26gn")
    ap.add_argument("--subset", default="norm")
    ap.add_argument("--batches", type=int, default=60,
                    help="random batches drawn per (cell, N)")
    ap.add_argument("--dtype", default="float64", choices=["float32", "float64"],
                    help="float64 by default: the quantity of interest is how "
                         "far |cos| falls below 1, which must not be confounded "
                         "with the float32 floor measured in T1.5")
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    cells = shift_cells()
    if args.smoke:
        cells, args.batches = cells[:2], 3

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if args.dtype == "float32" else torch.float64
    set_seed(args.seed)
    model, _ = load_binary_model(args.ckpt_dir, args.pair, args.arch, args.seed,
                                 device, dtype)
    params, _ = subset_params(model, args.subset)
    ids, lab = binary_test_ids(args.data_root, args.pair)

    tag = f"scope_{args.pair}_{args.arch}_s{args.seed}_{args.subset}_{args.dtype}"
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    if os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)

    t0, n = time.time(), 0
    for corr, sev in cells:
        xs = (clean_test_images(args.data_root, ids) if corr == "clean"
              else corrupted_test_images(args.data_root, corr, sev, ids))
        xs = torch.from_numpy(xs).to(device=device, dtype=dtype)
        for N in BATCH_SIZES:
            rng = np.random.default_rng(np.random.SeedSequence(
                entropy=args.seed, spawn_key=(5309, abs(hash(corr)) % 9973, sev, N)))
            for b in range(args.batches):
                sel = rng.choice(len(ids), size=N, replace=False)
                x = xs[sel]
                y = lab[sel]
                rows = [batch_quantities(model, params, x, y, eps)
                        for eps in EPS_GRID]
                writer.write({"pair": args.pair, "arch": args.arch,
                              "model_seed": args.seed, "subset": args.subset,
                              "dtype": args.dtype, "corruption": corr,
                              "severity": sev, "N": N, "batch_index": b,
                              "test_ids": [int(ids[i]) for i in sel],
                              "per_eps": rows})
                n += 1
        writer.flush()
        print(f"[scope] {tag} {corr} s{sev}: {len(BATCH_SIZES)} Ns x "
              f"{args.batches} batches ({n} recs, {time.time() - t0:.0f}s)",
              flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "cell": f"{corr}_{sev}",
                                       "records": n})
    writer.close()
    save_json({"meta": run_meta(args, {"batch_sizes": BATCH_SIZES,
                                       "eps_grid": EPS_GRID, "n_records": n}),
               "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[scope] DONE {tag} {n} records in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
