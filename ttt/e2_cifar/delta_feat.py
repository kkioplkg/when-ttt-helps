"""E5: feature-space shift proxy for E2 episodes (C2 follow-up, mirrors E4's
delta_v2). For each (dataset, corruption, severity) and the episode indices
recorded in the E2 main-mode results, compute the cosine distance between the
frozen encoder's pooled features of the corrupted image and the clean-test
feature mean of the same dataset. Join key: (dataset, corruption, severity, idx).
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed  # noqa: E402
from e2_cifar.data import corrupted_tensor, get_test_loader  # noqa: E402
from e2_cifar.models import ResNet26TTT, WRN2810  # noqa: E402


@torch.no_grad()
def feats_r26(model, x):
    z = model.shared(x)
    return torch.nn.functional.adaptive_avg_pool2d(z, 1).flatten(1)


@torch.no_grad()
def feats_wrn(model, x):
    out = model.blocks(model.conv1(x))
    out = torch.nn.functional.relu(model.bn(out))
    return torch.nn.functional.adaptive_avg_pool2d(out, 1).flatten(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="workdir/ttt/results/e2")
    ap.add_argument("--data-root", default="workdir/data")
    ap.add_argument("--ckpt-dir", default="workdir/ttt/ckpt")
    ap.add_argument("--out-dir", default="workdir/ttt/results/e5")
    ap.add_argument("--seed", type=int, default=0, help="source-model seed for features")
    args = ap.parse_args()
    set_seed(0)
    device = "cuda"

    for dataset, arch, cls, featfn in [
            ("cifar10", "resnet26ttt", ResNet26TTT, feats_r26),
            ("cifar100", "resnet26ttt", ResNet26TTT, feats_r26),
            ("cifar10", "wrn2810", WRN2810, feats_wrn),
            ("cifar100", "wrn2810", WRN2810, feats_wrn)]:
        nc = 10 if dataset == "cifar10" else 100
        blob = torch.load(os.path.join(args.ckpt_dir, f"{dataset}_{arch}_s{args.seed}.pt"),
                          map_location="cpu", weights_only=False)
        model = cls(nc)
        model.load_state_dict(blob["model"])
        model.to(device).eval()

        # clean feature reference mean
        loader = get_test_loader(dataset, args.data_root, 512)
        fsum, n = None, 0
        for x, _ in loader:
            f = featfn(model, x.to(device))
            fsum = f.sum(0) if fsum is None else fsum + f.sum(0)
            n += f.size(0)
        ref = fsum / n
        ref = ref / (ref.norm() + 1e-12)

        # needed (corruption, severity, idx) sets from E2 main results
        need = {}
        for rf in glob.glob(os.path.join(args.results_dir, f"{dataset}_*_main_*.json")):
            d = json.load(open(rf))
            meth = d["meta"]["argv"]["method"]
            m_arch = "resnet26ttt" if meth.startswith("ttt") else "wrn2810"
            if m_arch != arch:
                continue
            for cell in d["results"]:
                key = (cell["corruption"], cell["severity"])
                need.setdefault(key, set()).update(
                    ep["idx"] for ep in cell["episodes"])
        if not need:
            continue
        records = []
        for (corr, sev), idxs in sorted(need.items()):
            xs, _ = corrupted_tensor(dataset, args.data_root, corr, sev, n=None, seed=0)
            idxs = sorted(idxs)
            xb = xs[idxs].to(device)
            f = featfn(model, xb)
            fn_ = f / (f.norm(dim=1, keepdim=True) + 1e-12)
            dist = (1.0 - fn_ @ ref).cpu().numpy()
            records += [{"corruption": corr, "severity": sev, "idx": int(i),
                         "delta_feat": float(v)} for i, v in zip(idxs, dist)]
            print(f"[e5:dfeat] {dataset}/{arch} {corr} s{sev}: {len(idxs)} eps",
                  flush=True)
        save_json({"dataset": dataset, "arch": arch, "ref": "clean_test_mean",
                   "model_seed": args.seed, "records": records},
                  os.path.join(args.out_dir, f"delta_feat_{dataset}_{arch}.json"))
    print("[e5:dfeat] DONE")


if __name__ == "__main__":
    main()
