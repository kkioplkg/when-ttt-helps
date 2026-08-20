#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Where does an epoch of `train_source.py --arch resnet26ttt` actually go?

Run before committing GPU-hours: the published m0 records say 200 epochs took
~49 min on an RTX 2080 Ti, and a 2-epoch smoke on this host extrapolated to
~180 min, which would put the six retrainings alone at 18 GPU-h and blow the
budget.  A 4x slowdown on a faster GPU is not a GPU story, so this splits the
epoch into data / rotate_batch / fwd+bwd and reports GPU utilisation, to find
out what to fix before paying for it six times.
"""
import argparse
import os
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from e2_cifar.data import get_train_loader  # noqa: E402
from e2_cifar.models import build_model, rotate_batch  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--batches", type=int, default=390)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=128)
    args = ap.parse_args()

    dev = "cuda"
    m = build_model("resnet26ttt", 10).to(dev)
    opt = torch.optim.SGD(m.parameters(), lr=0.1, momentum=0.9,
                          weight_decay=5e-4, nesterov=True)
    scaler = torch.amp.GradScaler("cuda")
    ld = get_train_loader("cifar10", args.data_root, args.batch_size,
                          workers=args.workers)
    m.train()

    t_data = t_rot = t_fwd = 0.0
    t0 = time.time()
    tprev = time.time()
    n = 0
    for x, y in ld:
        t_data += time.time() - tprev
        x = x.to(dev, non_blocking=True)
        y = y.to(dev, non_blocking=True)
        opt.zero_grad(set_to_none=True)

        ta = time.time()
        xr, yr = rotate_batch(x)
        torch.cuda.synchronize()
        t_rot += time.time() - ta

        tb = time.time()
        with torch.amp.autocast("cuda"):
            loss = F.cross_entropy(m(x), y) + F.cross_entropy(m.forward_ssl(xr), yr)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        torch.cuda.synchronize()
        t_fwd += time.time() - tb

        n += 1
        tprev = time.time()
        if n >= args.batches:
            break
    tot = time.time() - t0
    print(f"batches={n} workers={args.workers} bs={args.batch_size}")
    print(f"  total       {tot:8.2f}s   ({tot/n*1000:.1f} ms/batch)")
    print(f"  data wait   {t_data:8.2f}s   ({100*t_data/tot:.1f}%)")
    print(f"  rotate_batch{t_rot:8.2f}s   ({100*t_rot/tot:.1f}%)")
    print(f"  fwd+bwd     {t_fwd:8.2f}s   ({100*t_fwd/tot:.1f}%)")
    print(f"  200-epoch extrapolation: {200*tot/n*ld.__len__()/60:.0f} min "
          f"(if n<len(loader), scaled by {ld.__len__()}/{n})")


if __name__ == "__main__":
    main()
