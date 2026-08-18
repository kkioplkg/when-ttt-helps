"""Train the P1 binary source models: one CIFAR-10 class pair, one seed.

The three pairs (`common.PAIRS`) were fixed before any measurement and span an
a-priori difficulty range.  Training touches only the CIFAR-10 TRAIN split; the
test identities that P1 measures on are never seen.

Augmentation runs on the GPU (pad+random-crop+hflip on the normalized tensor)
because the whole two-class train split is 10 000 images and fits in VRAM many
times over; this removes the dataloader from a job whose wall time is otherwise
dominated by it.

Usage:
    python train_binary.py --pair cat_dog --seed 20260901 \
        --data-root .../data --ckpt-dir .../ckpt/closure
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

from common import (PAIRS, binary_test_ids, binary_train_set, clean_test_images,  # noqa: E402
                    heartbeat, rel, run_meta, save_json, set_seed, _normalize)
from models import build  # noqa: E402


def gpu_augment(x, gen):
    """pad-4 random crop + random horizontal flip, on the normalized tensor."""
    n = x.size(0)
    xp = F.pad(x, (4, 4, 4, 4), mode="constant", value=0.0)
    ox = torch.randint(0, 9, (n,), generator=gen, device=x.device)
    oy = torch.randint(0, 9, (n,), generator=gen, device=x.device)
    idx = torch.arange(32, device=x.device)
    rows = (oy[:, None] + idx[None, :])
    cols = (ox[:, None] + idx[None, :])
    out = xp[torch.arange(n, device=x.device)[:, None, None, None],
             torch.arange(3, device=x.device)[None, :, None, None],
             rows[:, None, :, None], cols[:, None, None, :]]
    flip = torch.rand(n, generator=gen, device=x.device) < 0.5
    out[flip] = torch.flip(out[flip], dims=[3])
    return out


@torch.no_grad()
def evaluate(model, x, y, bs=512):
    model.eval()
    correct = 0
    loss = 0.0
    for i in range(0, x.size(0), bs):
        z = model(x[i:i + bs])
        loss += float(F.cross_entropy(z, y[i:i + bs], reduction="sum").item())
        correct += int((z.argmax(1) == y[i:i + bs]).sum().item())
    return correct / x.size(0), loss / x.size(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, choices=list(PAIRS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arch", default="resnet26gn", choices=["resnet26gn", "wrn2810"])
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--momentum", type=float, default=0.9)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    args = ap.parse_args()

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tag = f"{args.pair}_{args.arch}_s{args.seed}"
    out_path = os.path.join(args.ckpt_dir, f"{tag}.pt")
    if os.path.exists(out_path):
        print(f"[train] {tag}: checkpoint exists, skipping")
        return

    xtr_u8, ytr = binary_train_set(args.data_root, args.pair)
    xtr = torch.from_numpy(_normalize(xtr_u8)).to(device)
    ytr = torch.from_numpy(ytr).to(device)
    ids, lab = binary_test_ids(args.data_root, args.pair)
    xte = torch.from_numpy(clean_test_images(args.data_root, ids)).to(device)
    yte = torch.from_numpy(lab).to(device)
    print(f"[train] {tag}: train {tuple(xtr.shape)} test {tuple(xte.shape)}", flush=True)

    model = build(args.arch, num_classes=2).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum,
                          weight_decay=args.wd, nesterov=True)
    n = xtr.size(0)
    steps_per_epoch = n // args.batch_size
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=args.lr, total_steps=args.epochs * steps_per_epoch,
        pct_start=0.15, div_factor=10.0, final_div_factor=100.0)
    gen = torch.Generator(device=device).manual_seed(args.seed)

    t0 = time.time()
    hist = []
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(n, generator=gen, device=device)
        tot = 0.0
        for i in range(steps_per_epoch):
            sel = perm[i * args.batch_size:(i + 1) * args.batch_size]
            xb = gpu_augment(xtr[sel], gen)
            loss = F.cross_entropy(model(xb), ytr[sel])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += float(loss.item())
        if (ep + 1) % 10 == 0 or ep == args.epochs - 1:
            acc, tl = evaluate(model, xte, yte)
            hist.append({"epoch": ep + 1, "train_loss": tot / steps_per_epoch,
                         "test_acc": acc, "test_loss": tl})
            print(f"[train] {tag} ep{ep + 1}: train {tot / steps_per_epoch:.4f} "
                  f"test acc {acc:.4f} loss {tl:.4f}", flush=True)
            if args.heartbeat:
                heartbeat(args.heartbeat, {"job": tag, "epoch": ep + 1, "acc": acc})

    acc, tl = evaluate(model, xte, yte)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    torch.save({"model": model.state_dict(), "arch": args.arch, "pair": args.pair,
                "classes": PAIRS[args.pair], "seed": args.seed,
                "test_acc": acc, "test_loss": tl,
                "meta": run_meta(args)}, out_path)
    save_json({"meta": run_meta(args), "history": hist,
               "final": {"test_acc": acc, "test_loss": tl},
               "wall_s": time.time() - t0,
               "ckpt": rel(out_path)},
              os.path.join(args.ckpt_dir, f"{tag}_train.json"))
    print(f"[train] DONE {tag} acc={acc:.4f} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
