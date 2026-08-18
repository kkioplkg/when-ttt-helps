"""Train the masked-reconstruction decoder on a FROZEN source encoder (M2 prep).

Cheap post-hoc job (~3 min/ckpt): the encoder stays exactly the source model, so
TTT-mask adaptation starts from the same theta_0 as TTT-rot.
"""
import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed  # noqa: E402
from core.adapt import masked_recon_loss  # noqa: E402
from e2_cifar.data import get_train_loader  # noqa: E402
from e2_cifar.models import ResNet26TTT, attach_recon_head  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--data-root", default="workdir/data")
    args = ap.parse_args()
    set_seed(0)
    device = "cuda"
    nc = 10 if args.dataset == "cifar10" else 100
    blob = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    model = ResNet26TTT(nc)
    model.load_state_dict(blob["model"])
    attach_recon_head(model)
    model.to(device)
    for p in model.parameters():
        p.requires_grad_(False)
    for p in model.recon_head.parameters():
        p.requires_grad_(True)
    opt = torch.optim.Adam(model.recon_head.parameters(), lr=1e-3)
    loader = get_train_loader(args.dataset, args.data_root, 256)
    model.eval()  # GN is stateless; keep deterministic
    last = None
    for ep in range(args.epochs):
        tot = n = 0
        for x, _ in loader:
            x = x.to(device, non_blocking=True)
            loss = masked_recon_loss(model, x, seed=n)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += float(loss.item()) * x.size(0)
            n += x.size(0)
        last = tot / n
        print(f"[recon] {os.path.basename(args.ckpt)} ep{ep+1} loss={last:.4f}",
              flush=True)
    blob["recon_head"] = model.recon_head.state_dict()
    blob["recon_final_loss"] = last
    torch.save(blob, args.ckpt)
    save_json({"ckpt": args.ckpt, "recon_final_loss": last},
              args.ckpt.replace(".pt", "_recon.json"))
    print(f"[recon] DONE {args.ckpt} loss={last:.4f}")


if __name__ == "__main__":
    main()
