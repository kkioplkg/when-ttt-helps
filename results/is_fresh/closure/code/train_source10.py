"""Train 10-class ResNet26TTT source models for P2 (main CE + rotation CE).

Same TTT protocol as the manuscript's `e2_cifar/train_source.py` -- joint main
and rotation cross-entropy at lambda = 1, SGD + nesterov, cosine schedule -- but
fed from the in-memory numpy CIFAR-10 arrays with GPU-side augmentation instead
of a torchvision DataLoader.  The reason is throughput, not protocol: the whole
train split is 50 000 32x32 images and fits in VRAM many times over, so the
DataLoader was the wall-clock bottleneck of the original job.  The model, the
objective, the augmentation (pad-4 random crop + horizontal flip) and the
optimizer are unchanged.

P2 needs more than one source seed: the alignment-persistence estimands are
clustered by (seed, corruption), and a single checkpoint would leave the
cluster structure resting on corruptions alone.
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

from common import _normalize, heartbeat, load_cifar10_np, rel, run_meta, save_json, set_seed  # noqa: E402
from e2_cifar.models import ResNet26TTT  # noqa: E402
from train_binary import gpu_augment  # noqa: E402


def rotate_batch_seeded(x, gen):
    """Each image rotated by k*90deg, k uniform -- the manuscript's rotate_batch
    with an explicit generator so the run is reproducible from the seed."""
    k = torch.randint(0, 4, (x.size(0),), generator=gen, device=x.device)
    xs = torch.stack([torch.rot90(img, int(kk), dims=(1, 2))
                      for img, kk in zip(x, k)])
    return xs, k


@torch.no_grad()
def evaluate(model, x, y, gen, bs=500):
    model.eval()
    correct = rot_correct = 0
    for i in range(0, x.size(0), bs):
        xb, yb = x[i:i + bs], y[i:i + bs]
        correct += int((model(xb).argmax(1) == yb).sum().item())
        xr, yr = rotate_batch_seeded(xb, gen)
        rot_correct += int((model.forward_ssl(xr).argmax(1) == yr).sum().item())
    n = x.size(0)
    return correct / n, rot_correct / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    args = ap.parse_args()

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tag = f"cifar10_resnet26ttt_s{args.seed}"
    out_path = os.path.join(args.ckpt_dir, f"{tag}.pt")
    if os.path.exists(out_path):
        print(f"[m0] {tag}: checkpoint exists, skipping")
        return

    trx, try_, tex, tey = load_cifar10_np(args.data_root)
    xtr = torch.from_numpy(_normalize(trx)).to(device)
    ytr = torch.from_numpy(try_.astype(np.int64)).to(device)
    xte = torch.from_numpy(_normalize(tex)).to(device)
    yte = torch.from_numpy(tey.astype(np.int64)).to(device)

    model = ResNet26TTT(10).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9,
                          weight_decay=args.wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda")
    gen = torch.Generator(device=device).manual_seed(args.seed)

    n = xtr.size(0)
    spe = n // args.batch_size
    hist, t0 = [], time.time()
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(n, generator=gen, device=device)
        for i in range(spe):
            sel = perm[i * args.batch_size:(i + 1) * args.batch_size]
            xb = gpu_augment(xtr[sel], gen)
            yb = ytr[sel]
            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda"):
                xr, yr = rotate_batch_seeded(xb, gen)
                loss = (F.cross_entropy(model(xb), yb)
                        + F.cross_entropy(model.forward_ssl(xr), yr))
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        sched.step()
        if (ep + 1) % 10 == 0 or ep == args.epochs - 1:
            acc, rot = evaluate(model, xte, yte, gen)
            hist.append({"epoch": ep + 1, "test_acc": acc, "rot_acc": rot,
                         "minutes": (time.time() - t0) / 60})
            print(f"[m0] {tag} ep{ep + 1} acc={acc:.4f} rot={rot:.4f} "
                  f"({hist[-1]['minutes']:.1f} min)", flush=True)
            if args.heartbeat:
                heartbeat(args.heartbeat, {"job": tag, "epoch": ep + 1, "acc": acc})

    acc, rot = evaluate(model, xte, yte, gen)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    torch.save({"model": model.state_dict(), "seed": args.seed,
                "test_acc": acc, "rot_acc": rot, "meta": run_meta(args)}, out_path)
    save_json({"meta": run_meta(args), "history": hist,
               "final": {"test_acc": acc, "rot_acc": rot},
               "gate_pass": bool(acc >= 0.93 and rot >= 0.85),
               "ckpt": rel(out_path)},
              os.path.join(args.ckpt_dir, f"{tag}_train.json"))
    print(f"[m0] DONE {tag} acc={acc:.4f} rot={rot:.4f} "
          f"in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
