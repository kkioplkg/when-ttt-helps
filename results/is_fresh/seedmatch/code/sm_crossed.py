#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage C': the CROSSED measurement matrix.

For one measurement network m and one dataset, record for every observation in
the frozen episode manifest:

    d_{i,m}    delta_feat  -- cosine distance of the pooled encoder feature of
                              the corrupted image to network m's OWN clean-test
                              feature centroid.  Identical computation to
                              `e2_cifar/delta_feat.py`; the only change is that
                              the output is keyed by the measurement network.
    L_{i,m}    the LABELLED frozen cross-entropy of network m on that image
    c_{i,m}    whether network m's frozen prediction is correct

Design v1 measured only the diagonal (episode of seed s through net s) plus the
seed-0 column.  Full crossing costs forward passes only and is what makes the
following possible:

  * the two complete derangements P1 (0->1,1->2,2->0) and P2 (0->2,1->0,2->1),
    i.e. a GENERIC-WRONG arm in which "wrong network" is held fixed while
    "which wrong network" varies.  With a single permuted arm, wrongness stays
    entangled with one identity mapping;
  * separating "which network" from "which episode set".  Source seed s picks
    BOTH the trained network AND the 128 images per cell, so a raw seed-1 vs
    seed-2 difference is not attributable to network geometry unless every
    observation is seen by every network.  With the full matrix it is;
  * the balanced-panel calibration decomposition (offset / scale / rank), which
    needs every network scored on exactly the same tuples.

L_{i,m} is the reason this script exists rather than a second delta_feat run.
The PRIMARY endpoint of the experiment is whether measuring through the correct
network makes delta_feat more concordant with THAT network's labelled risk, and
the labelled risk of the fresh networks is not in any existing record.

Nothing is written until the network reproduces its recorded clean-test
accuracy to within --acc-tol: a feature map read off the wrong checkpoint is
undetectable downstream.
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.utils import save_json, set_seed  # noqa: E402
from e2_cifar.data import corrupted_tensor, get_test_loader  # noqa: E402
from e2_cifar.models import ResNet26TTT  # noqa: E402

ARCH = "resnet26ttt"


@torch.no_grad()
def feats(model, x):
    """Pooled shared-encoder feature. Identical to e2_cifar/delta_feat.py."""
    z = model.shared(x)
    return F.adaptive_avg_pool2d(z, 1).flatten(1)


@torch.no_grad()
def clean_accuracy_and_centroid(model, dataset, data_root, device):
    """One pass over the clean test set: accuracy (for the gate) and the
    feature centroid (for delta_feat).  Both must come from the same network,
    so they are computed together and can never be mismatched."""
    loader = get_test_loader(dataset, data_root, 512)
    fsum, n, correct = None, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        f = feats(model, x)
        fsum = f.sum(0) if fsum is None else fsum + f.sum(0)
        correct += int((model(x).argmax(1) == y).sum().item())
        n += int(y.numel())
    ref = fsum / n
    return correct / n, ref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--measure-seed", type=int, required=True,
                    help="the SOURCE-MODEL seed whose network is measured through")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--m0-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--acc-tol", type=float, default=0.002)
    ap.add_argument("--batch", type=int, default=512)
    args = ap.parse_args()

    set_seed(0)              # the measurement draws no random numbers
    device = "cuda"
    ds = args.dataset
    m = args.measure_seed
    nc = 10 if ds == "cifar10" else 100
    tag = f"{ds}_{ARCH}_s{m}"

    with open(args.manifest, encoding="utf-8") as f:
        man = json.load(f)
    union = man["union_by_dataset"][ds]

    blob = torch.load(os.path.join(args.ckpt_dir, f"{tag}.pt"),
                      map_location="cpu", weights_only=False)
    model = ResNet26TTT(nc)
    model.load_state_dict(blob["model"])
    model.to(device).eval()

    acc, ref_raw = clean_accuracy_and_centroid(model, ds, args.data_root, device)
    with open(os.path.join(args.m0_dir, f"{tag}.json"), encoding="utf-8") as f:
        recorded = float(json.load(f)["final"]["test_acc"])
    if abs(acc - recorded) > args.acc_tol:
        raise SystemExit(
            f"CHECKPOINT GATE FAILED for {tag}: remeasured clean accuracy "
            f"{acc:.4f} against recorded {recorded:.4f} (tol {args.acc_tol}). "
            f"Refusing to write a feature map that may be read off the wrong "
            f"network.")
    print(f"[sm:crossed] {tag} clean acc recorded={recorded:.4f} "
          f"remeasured={acc:.4f} GATE PASS", flush=True)

    ref = ref_raw / (ref_raw.norm() + 1e-12)

    records = []
    for ck in sorted(union):
        corr, sev = ck.split("|")
        sev = int(sev)
        idxs = union[ck]
        xs, ys = corrupted_tensor(ds, args.data_root, corr, sev, n=None, seed=0)
        sel = torch.as_tensor(idxs, dtype=torch.long)
        for lo in range(0, len(sel), args.batch):
            chunk = sel[lo:lo + args.batch]
            xb = xs[chunk].to(device)
            yb = ys[chunk].to(device)
            with torch.no_grad():
                fb = feats(model, xb)
                fn_ = fb / (fb.norm(dim=1, keepdim=True) + 1e-12)
                d = (1.0 - fn_ @ ref).cpu().numpy()
                logits = model(xb)
                loss = F.cross_entropy(logits, yb, reduction="none").cpu().numpy()
                ok = (logits.argmax(1) == yb).cpu().numpy().astype(int)
            for j, i in enumerate(chunk.tolist()):
                records.append({"corruption": corr, "severity": sev, "idx": int(i),
                                "delta_feat": float(d[j]),
                                "frozen_loss": float(loss[j]),
                                "frozen_correct": int(ok[j])})
        print(f"[sm:crossed] {tag} {corr} s{sev}: {len(idxs)} obs", flush=True)

    # completeness against the manifest, asserted rather than trusted
    want = sum(len(v) for v in union.values())
    if len(records) != want:
        raise SystemExit(f"COMPLETENESS FAILED: {len(records)} records for "
                         f"{want} manifest observations")

    dv = np.array([r["delta_feat"] for r in records], float)
    save_json({
        "dataset": ds, "arch": ARCH, "measurement_seed": m,
        "ref": "clean_test_mean_of_this_network",
        "join_key": ["dataset", "arch", "measurement_seed", "corruption",
                     "severity", "idx"],
        "driven_by": "frozen episode manifest (union), not a glob",
        "manifest_source_files": [f["file"] for f in man["source_files"]],
        "n_records": len(records),
        "n_manifest_observations": want,
        "completeness_gate": True,
        "clean_acc_recorded": recorded,
        "clean_acc_remeasured": acc,
        "clean_acc_tol": args.acc_tol,
        "clean_acc_gate": True,
        "clean_feature_centroid_norm": float(ref_raw.norm().item()),
        "delta_feat_summary": {"mean": float(dv.mean()), "sd": float(dv.std()),
                               "min": float(dv.min()), "max": float(dv.max())},
        "records": records,
    }, os.path.join(args.out_dir, f"crossed_{ds}_s{m}.json"))
    print(f"[sm:crossed] DONE {tag}: {len(records)} records, "
          f"delta_feat mean={dv.mean():.4f} sd={dv.std():.4f}", flush=True)


if __name__ == "__main__":
    main()
