"""M0: source model training on clean CIFAR-10/100.

resnet26ttt: joint training main CE + rotation CE (TTT protocol, lambda=1).
wrn2810:     plain CE (Tent protocol).
"""
import argparse
import os
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed, run_meta  # noqa: E402
from e2_cifar.data import get_test_loader, get_train_loader  # noqa: E402
from e2_cifar.models import build_model, rotate_batch  # noqa: E402


@torch.no_grad()
def evaluate(model, loader, device, ssl=False):
    model.eval()
    correct = total = rot_correct = 0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        logits = model(x)
        correct += (logits.argmax(1) == y).sum().item()
        total += y.numel()
        if ssl:
            xr, yr = rotate_batch(x)
            rot_correct += (model.forward_ssl(xr).argmax(1) == yr).sum().item()
    return correct / total, (rot_correct / total if ssl else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--arch", required=True, choices=["resnet26ttt", "wrn2810"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--data-root", default="workdir/data")
    ap.add_argument("--out-dir", default="workdir/ttt/results/m0")
    ap.add_argument("--ckpt-dir", default="workdir/ttt/ckpt")
    args = ap.parse_args()
    if args.epochs is None:
        args.epochs = 200 if args.arch == "resnet26ttt" else 120

    set_seed(args.seed)
    device = "cuda"
    nc = 10 if args.dataset == "cifar10" else 100
    model = build_model(args.arch, nc).to(device)
    is_ttt = args.arch == "resnet26ttt"

    train_loader = get_train_loader(args.dataset, args.data_root, args.batch_size)
    test_loader = get_test_loader(args.dataset, args.data_root)

    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9,
                          weight_decay=args.wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda")

    tag = f"{args.dataset}_{args.arch}_s{args.seed}"
    history = []
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda"):
                if is_ttt:
                    xr, yr = rotate_batch(x)
                    logits = model(x)
                    rot_logits = model.forward_ssl(xr)
                    loss = F.cross_entropy(logits, y) + F.cross_entropy(rot_logits, yr)
                else:
                    loss = F.cross_entropy(model(x), y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        sched.step()
        if (ep + 1) % 10 == 0 or ep == args.epochs - 1:
            acc, rot = evaluate(model, test_loader, device, ssl=is_ttt)
            history.append({"epoch": ep + 1, "test_acc": acc, "rot_acc": rot,
                            "minutes": (time.time() - t0) / 60})
            print(f"[{tag}] ep{ep+1} acc={acc:.4f} rot={rot} "
                  f"({history[-1]['minutes']:.1f} min)", flush=True)

    os.makedirs(args.ckpt_dir, exist_ok=True)
    torch.save({"model": model.state_dict(), "args": vars(args)},
               os.path.join(args.ckpt_dir, f"{tag}.pt"))
    final = history[-1]
    acc_gate = final["test_acc"] >= ({"cifar10": 0.93, "cifar100": 0.70}[args.dataset]
                                     if is_ttt else
                                     {"cifar10": 0.945, "cifar100": 0.75}[args.dataset])
    rot_gate = (final["rot_acc"] >= 0.85) if is_ttt else True
    gate = acc_gate and rot_gate
    save_json({"meta": run_meta(args), "history": history, "final": final,
               "acc_gate": bool(acc_gate), "rot_gate": bool(rot_gate),
               "gate_pass": bool(gate)},
              os.path.join(args.out_dir, f"{tag}.json"))
    print(f"[{tag}] DONE acc={final['test_acc']:.4f} gate={gate}")


if __name__ == "__main__":
    main()
