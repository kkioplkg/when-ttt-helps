"""F38 -- remeasure the feature-space shift proxy on the FRESH GroupNorm model.

WHY THIS SCRIPT EXISTS
`f15_e2_entropy_gn.py` adapted a freshly trained seed-20260806 ResNet-26+GN
source model over 45 cells x 256 = 11,520 episodes.  Its episode records carry
every quantity the phase statistic needs EXCEPT the feature-space shift proxy
`delta_feat`, which is not computed inside the adaptation loop.  `f16` therefore
joined `delta_feat` by (corruption, severity, idx) from the ORIGINAL E5 file
`results/e5/delta_feat_cifar10_resnet26ttt.json`, which was measured on the
PUBLISHED seed-0 source model over the PUBLISHED E2 episode indices.

That join has two defects, and the second is the reason this script exists:

  (a) it is across source models -- documented since the arm was added; and
  (b) it is SPARSE.  The fresh run drew its own 256 episode indices per cell,
      so only 300 of the 11,520 fresh episodes (2.60%) carry a joined
      `delta_feat` at all: 5-9 observations per cell, mean 6.67, and about 3
      per cell after the 50/50 commissioning split, with some cells left with
      none.  The effective support of the feature-proxy correlation for this
      arm was therefore roughly 1/40 of the 256 episodes/cell the adaptation
      run has.

This script removes both defects by measuring `delta_feat` where it should have
been measured: on the fresh model, on the fresh episodes, all 11,520 of them.

DEFINITION -- byte-for-byte the published one
`experiments/ttt/e2_cifar/delta_feat.py` defines, for one image x,

    delta_feat(x) = 1 - < f(x)/||f(x)|| , ref/||ref|| >

with f = adaptive_avg_pool(shared_encoder(x)) and `ref` the MEAN of f over the
clean CIFAR-10 test set, both computed by the SAME frozen source model.  The
encoder split (`model.shared` = conv1 + group1 + group2) and the normalisation
constants are imported from the project modules rather than restated here, so
the two scripts cannot drift apart.  The only change is which checkpoint and
which (corruption, severity, idx) set are used.

COMPUTE
CPU only, and cheap: 10,000 clean + 11,520 corrupted forward passes through a
ResNet-26 encoder at 32x32, about 20 seconds wall clock in the pinned
interpreter.  No GPU is required and none is used; the fresh checkpoint is a
2.6 MB file retained beside the records it produced.

GATE
The checkpoint is loaded and its clean test accuracy recomputed before any
proxy value is written.  `f15_source_gate.json` recorded 0.9165 on the GPU box
that trained it; the CPU recomputation must land within 0.002 of that, which is
what certifies that this script is looking at the same model, the same test
set and the same preprocessing as the run whose episodes it is annotating.
A wider deviation aborts.

OUTPUT
  e2_gn/delta_feat_fresh_cifar10_resnet26ttt_s20260806.json
      same schema as the published E5 file -- {dataset, arch, ref, model_seed,
      records:[{corruption, severity, idx, delta_feat}]} -- plus a `source`
      block naming the checkpoint and the gate it passed.  Written into the
      e2_gn record directory and NOT into results/e5/, because
      `f8_e2_crossfit.load_delta_feat()` globs results/e5/delta_feat_*.json and
      merges every file it finds into one (dataset, arch) map: a fresh-model
      file placed there would silently overwrite the published values the
      ttt_rot / ttt_mask arms depend on.
  f38_e2gn_deltafeat_fresh.json
      the support census -- old-join match rate and per-cell counts, new
      coverage, and the distribution of both -- so that the sparsity this
      script repairs is itself a retained, citable measurement rather than a
      claim in prose.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

import common as C
import f8_e2_crossfit as F8

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from e2_cifar.data import MEAN, STD, corrupted_tensor   # noqa: E402
from e2_cifar.models import ResNet26TTT                 # noqa: E402

GN_DIR = os.path.join(C.RESULTS_DIR, "e2_gn")
CKPT = os.path.join(GN_DIR, "cifar10_resnet26ttt_s20260806.pt")
GATE = os.path.join(GN_DIR, "f15_source_gate.json")
RECORDS = os.path.join(GN_DIR, "cifar10_tent_main_s20260806.json")
OUT_RECORDS = "delta_feat_fresh_cifar10_resnet26ttt_s20260806.json"
DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "data")
MODEL_SEED = 20260806
GATE_TOL = 0.002


@torch.no_grad()
def feats(model, x):
    """The published feature map: pooled shared-encoder activations."""
    z = model.shared(x)
    return torch.nn.functional.adaptive_avg_pool2d(z, 1).flatten(1)


def clean_test_tensor():
    """The clean CIFAR-10 test set under the project's test preprocessing.

    Read from the retained numpy copy rather than through torchvision's
    downloader: the transform is `ToTensor` then `Normalize`, which is exactly
    (uint8/255 - MEAN)/STD followed by the HWC->CHW transpose, and the accuracy
    gate below is what verifies that this is the same set in the same order.
    """
    x = np.load(os.path.join(DATA_ROOT, "cifar10_np", "test_x.npy"))
    y = np.load(os.path.join(DATA_ROOT, "cifar10_np", "test_y.npy"))
    x = x.astype(np.float32) / 255.0
    x = (x - np.asarray(MEAN["cifar10"], np.float32)) / \
        np.asarray(STD["cifar10"], np.float32)
    return torch.from_numpy(x.transpose(0, 3, 1, 2).copy()), y


@torch.no_grad()
def batched(model, fn, x, bs):
    return torch.cat([fn(model, x[i:i + bs]) for i in range(0, len(x), bs)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--out-prefix", default="f38_e2gn_deltafeat_fresh")
    args = ap.parse_args()
    t0 = time.time()
    torch.set_grad_enabled(False)

    # ---- model, and the gate that certifies it is the f15 source model ----
    blob = torch.load(CKPT, map_location="cpu", weights_only=False)
    model = ResNet26TTT(10)
    model.load_state_dict(blob["model"])
    model.eval()

    xte, yte = clean_test_tensor()
    logits = batched(model, lambda m, b: m(b), xte, args.batch)
    acc = float((logits.argmax(1).numpy() == yte).mean())
    with open(GATE, encoding="utf-8") as f:
        gate_acc = float(json.load(f)["test_acc"])
    if abs(acc - gate_acc) > GATE_TOL:
        raise SystemExit(
            f"source-model gate FAILED: recomputed clean test accuracy {acc:.4f} "
            f"differs from the f15 record {gate_acc:.4f} by more than {GATE_TOL}. "
            "The checkpoint, the test set or the preprocessing is not the one "
            "the fresh episodes were adapted from; no proxy value written.")
    print(f"[f38] source gate PASS: clean test acc {acc:.4f} "
          f"vs f15 record {gate_acc:.4f} ({time.time()-t0:.1f}s)", flush=True)

    # ---- clean-test feature reference mean, as in e2_cifar/delta_feat.py ----
    fref = batched(model, feats, xte, args.batch).mean(0)
    fref = fref / (fref.norm() + 1e-12)

    # ---- the (corruption, severity, idx) set the FRESH episodes actually use
    with open(RECORDS, encoding="utf-8") as f:
        gn = json.load(f)
    need = {}
    for cell in gn["results"]:
        need.setdefault((cell["corruption"], int(cell["severity"])), set()).update(
            int(e["idx"]) for e in cell["episodes"])
    n_need = sum(len(v) for v in need.values())
    print(f"[f38] {len(need)} cells, {n_need} distinct fresh episode indices",
          flush=True)

    records, by_cell = [], {}
    for (corr, sev), idxs in sorted(need.items()):
        xs, _ = corrupted_tensor("cifar10", DATA_ROOT, corr, sev, n=None, seed=0)
        idxs = sorted(idxs)
        f = batched(model, feats, xs[idxs], args.batch)
        f = f / (f.norm(dim=1, keepdim=True) + 1e-12)
        d = (1.0 - f @ fref).numpy()
        by_cell[(corr, sev)] = len(idxs)
        records += [{"corruption": corr, "severity": sev, "idx": int(i),
                     "delta_feat": float(v)} for i, v in zip(idxs, d)]
        print(f"[f38] {corr} s{sev}: {len(idxs)} eps", flush=True)

    C.save({"dataset": "cifar10", "arch": "resnet26ttt", "ref": "clean_test_mean",
            "model_seed": MODEL_SEED,
            "source": {"checkpoint": os.path.basename(CKPT),
                       "clean_test_acc_recomputed": acc,
                       "clean_test_acc_f15_record": gate_acc,
                       "gate_tol": GATE_TOL,
                       "definition": "experiments/ttt/e2_cifar/delta_feat.py"},
            "records": records},
           os.path.join("e2_gn", OUT_RECORDS))

    # ---- support census: what the old join gave, what this gives -----------
    old = F8.load_delta_feat().get(("cifar10", "resnet26ttt"), {})
    old_cell = {}
    for cell in gn["results"]:
        corr, sev = cell["corruption"], int(cell["severity"])
        old_cell[f"{corr}/s{sev}"] = sum(
            1 for e in cell["episodes"]
            if (corr, sev, int(e["idx"])) in old)
    om = np.asarray(sorted(old_cell.values()))
    n_ep = sum(len(c["episodes"]) for c in gn["results"])
    census = {
        "script": os.path.basename(__file__),
        "fresh_run": {"records": os.path.basename(RECORDS),
                      "n_cells": len(gn["results"]),
                      "n_episodes": n_ep,
                      "episodes_per_cell": int(np.median(
                          [len(c["episodes"]) for c in gn["results"]]))},
        "old_cross_model_join": {
            "source": "results/e5/delta_feat_cifar10_resnet26ttt.json",
            "source_model_seed": 0,
            "n_matched": int(om.sum()),
            "match_rate": float(om.sum()) / n_ep,
            "per_cell_min": int(om.min()), "per_cell_max": int(om.max()),
            "per_cell_mean": float(om.mean()),
            "per_cell_median": float(np.median(om)),
            "per_cell": old_cell},
        "fresh_remeasurement": {
            "source": "e2_gn/" + OUT_RECORDS,
            "source_model_seed": MODEL_SEED,
            "n_matched": len(records),
            "match_rate": len(records) / n_ep,
            "per_cell_min": int(min(by_cell.values())),
            "per_cell_max": int(max(by_cell.values())),
            "per_cell_mean": float(np.mean(list(by_cell.values()))),
            "per_cell_median": float(np.median(list(by_cell.values())))},
        "gate": {"clean_test_acc_recomputed": acc,
                 "clean_test_acc_f15_record": gate_acc, "tol": GATE_TOL},
        "seconds": round(time.time() - t0, 1),
    }

    # ---- what the superseded join actually produced, split by split --------
    # Retained here rather than as 41 more per-seed files: the point of the
    # superseded arm is no longer its value but its INSTABILITY, and that is
    # five numbers.  Their spread across splits is the visible symptom of the
    # ~3 usable commissioning observations per cell counted above.
    import f16_e2_gn_analysis as F16   # local: F16 imports nothing from here
    legacy = F16.restrict(F16.load_gn_cells("legacy"))
    per_seed = [F8.analyse(legacy, "tent_gn", s, 0.5, "phase_feat", 0)
                for s in C.SEEDS]
    rhos = [r["rho_mean_final"] for r in per_seed]
    def commissioning_share(cells, seed):
        """The commissioning half of every cell, drawn exactly as F8.build_rows
        draws it: ONE generator, advanced cell by cell in sorted key order.
        A fresh generator per cell would restart the same stream in each and
        report a different, wrong split."""
        rng = np.random.default_rng(seed + 1)
        out = {}
        for key in sorted(cells):
            v = cells[key]
            perm = rng.permutation(len(v))
            k = min(max(int(round(len(v) * 0.5)), 1), len(v) - 1)
            out[key] = [v[i] for i in perm[:k].tolist()]
        return out

    comm = [F16.statistic_support(commissioning_share(legacy, s),
                                  "tent_gn", "phase_feat") for s in C.SEEDS]
    census["legacy_join_analysis"] = {
        "what": ("the superseded tent_gn feature-proxy arm, recomputed here so "
                 "that its split-to-split instability is a retained number"),
        "seeds": list(C.SEEDS),
        "rho_mean_final_per_seed": rhos,
        "rho_mean_final_mean": float(np.mean(rhos)),
        "commissioning_proxy_obs_total_per_seed": [c["total"] for c in comm],
        "commissioning_proxy_obs_per_cell_median_per_seed":
            [c["per_cell_median"] for c in comm],
        "cells_with_no_commissioning_proxy_obs_per_seed":
            [c["n_cells_empty"] for c in comm],
        "superseded_by": "e2_gn/" + OUT_RECORDS,
    }
    C.save(census, f"{args.out_prefix}.json")
    print(f"[f38] old join {census['old_cross_model_join']['n_matched']}/{n_ep} "
          f"({100*census['old_cross_model_join']['match_rate']:.2f}%), "
          f"fresh {len(records)}/{n_ep} "
          f"({100*census['fresh_remeasurement']['match_rate']:.2f}%) "
          f"in {census['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
