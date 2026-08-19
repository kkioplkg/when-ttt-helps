"""Compute-matched K=3-ensembled fixed-10 baseline for E3.

ALTA runs K=3 augmentation-view replica trajectories and deploys the
mean-replica (ensembled) prediction, so its comparators should include a
baseline with the same compute and the same ensembling but a fixed stop.
In each results/e3/<corruption>_<method>_alta_s0.json, the per-batch
"acc_by_step" is the accuracy trajectory of the MEAN-REPLICA ensemble
(index 0 = truly frozen eval-BN prediction; index t = K=3 batch-mean
logits after t gradient steps -- see e3_imagenet/run_e3.py run_cell).
Its value at t=10 therefore IS a K=3-ensembled fixed-10 baseline.

This script reports, per (corruption, method) at severity 5 (seed 0):
  - frozen accuracy,
  - ALTA adapted accuracy (label-free stop),
  - K=3-ensembled fixed-10 accuracy (alta file, mean over batches of
    per-batch acc_by_step[10]/n),
  - single-trajectory fixed-10 accuracy (fixed file, adapted_acc),
plus pooled means over the 45 severity-5 cells.

Output is printed only (numbers are quoted in sections/experiments.tex).
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
E3 = ROOT / "results" / "e3"

CORRUPTIONS = sorted({f.name.split("_" + m)[0]
                      for m in ("tent", "eata", "sar")
                      for f in E3.glob(f"*_{m}_alta_s0.json")})
METHODS = ("tent", "eata", "sar")
SEV = 5


def cell(obj, sev):
    for c in obj["results"]:
        if int(c["severity"]) == sev:
            return c
    raise KeyError(sev)


def main():
    rows = []
    for corr in CORRUPTIONS:
        for meth in METHODS:
            alta = json.loads(
                (E3 / f"{corr}_{meth}_alta_s0.json").read_text())
            fixed = json.loads(
                (E3 / f"{corr}_{meth}_fixed_s0.json").read_text())
            ca, cf = cell(alta, SEV), cell(fixed, SEV)
            # K=3-ensembled fixed-10: image-weighted mean over batches of
            # the mean-replica trajectory at t=10 (== cell acc_by_step[10])
            k3_corr = sum(b["acc_by_step"][10] for b in ca["batches"])
            k3_n = sum(b["n"] for b in ca["batches"])
            k3_fixed10 = k3_corr / k3_n
            assert abs(k3_fixed10 - ca["acc_by_step"][10]) < 1e-9
            rows.append({
                "corruption": corr, "method": meth,
                "frozen": ca["frozen_acc"],
                "alta": ca["adapted_acc"],
                "k3_fixed10": k3_fixed10,
                "single_fixed10": cf["adapted_acc"],
            })

    hdr = (f"{'corruption':18s} {'method':6s} {'frozen':>7s} {'ALTA':>7s} "
           f"{'K3-fx10':>8s} {'1tr-fx10':>8s}")
    print(hdr)
    for r in rows:
        print(f"{r['corruption']:18s} {r['method']:6s} "
              f"{100*r['frozen']:7.2f} {100*r['alta']:7.2f} "
              f"{100*r['k3_fixed10']:8.2f} {100*r['single_fixed10']:8.2f}")
    for k in ("frozen", "alta", "k3_fixed10", "single_fixed10"):
        print(f"pooled mean {k:15s} = "
              f"{100*float(np.mean([r[k] for r in rows])):.2f}")
    d_k3_alta = [r["k3_fixed10"] - r["alta"] for r in rows]
    d_k3_1tr = [r["k3_fixed10"] - r["single_fixed10"] for r in rows]
    n_k3_above_alta = sum(1 for d in d_k3_alta if d > 0)
    print(f"K3-fixed10 minus ALTA: mean {100*float(np.mean(d_k3_alta)):+.2f} pt, "
          f"above ALTA in {n_k3_above_alta}/{len(rows)} cells")
    print(f"K3-fixed10 minus single fixed10: "
          f"mean {100*float(np.mean(d_k3_1tr)):+.2f} pt")


if __name__ == "__main__":
    main()
