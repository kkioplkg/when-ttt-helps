"""Analysis for T1.5 -- the adversarial boundary-resolution sweep.

The reported quantity is the numerical sign-resolution boundary: the smallest
constructed |q - p| at which sign(alpha_ent) still reproduces sign(s(q-p)).

The attribution test is the COMPARISON between precisions, not the value at one
precision.  If the near-boundary disagreements are arithmetic, the boundary
tracks machine epsilon and moves by orders of magnitude between float32 and
float64; if they were the theorem's, the boundary would sit in the same place
at both precisions.  The temperature axis is the control: it varies |s| over
decades, so a boundary that is flat in T is a boundary set by the resolution of
(q - p) and not by proximity to the s = 0 degeneracy.
"""
import argparse
import glob
import os
import sys
from collections import defaultdict

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from common import read_records, rel, save_json  # noqa: E402

EPS = {"float32": float(np.finfo(np.float32).eps),
       "float64": float(np.finfo(np.float64).eps)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--glob", default="bnd_*.jsonl.gz")
    args = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(args.in_dir, args.glob)))
    if not paths:
        raise SystemExit(f"no records matching {args.glob}")

    cells = defaultdict(list)
    per_delta = defaultdict(lambda: {"n": 0, "agree": 0, "undef": 0})
    smallest_tested = None
    for p in paths:
        for r in read_records(p):
            cells[(r["dtype"], r["T"])].append(r["delta_min_resolved"])
            for row in r["rows"]:
                k = f'{r["dtype"]}|T{r["T"]}|d{row["delta"]:g}'
                d = per_delta[k]
                d["n"] += 1
                if row["agree"] is None:
                    d["undef"] += 1
                else:
                    d["agree"] += row["agree"]
                smallest_tested = (row["delta"] if smallest_tested is None
                                   else min(smallest_tested, row["delta"]))

    res = {"inputs": [rel(p) for p in paths], "machine_eps": EPS,
           "smallest_delta_tested": smallest_tested, "cells": {}, "per_delta": {}}
    for (dt, T), vals in sorted(cells.items()):
        got = [v for v in vals if v is not None]
        res["cells"][f"{dt}|T{T}"] = {
            "n": len(vals),
            "n_unresolved_at_every_delta": int(sum(1 for v in vals if v is None)),
            "delta_min_resolved_median": (float(np.median(got)) if got else None),
            "delta_min_resolved_max": (float(np.max(got)) if got else None),
            "delta_min_resolved_min": (float(np.min(got)) if got else None),
            "ratio_to_machine_eps": (float(np.median(got)) / EPS[dt]
                                     if got else None),
        }
    res["per_delta"] = {k: v for k, v in sorted(per_delta.items())}

    for k, c in sorted(res["cells"].items()):
        print(f"  {k}: median delta_min_resolved="
              f"{c['delta_min_resolved_median']} "
              f"(= {c['ratio_to_machine_eps']:.2f} x machine eps)"
              if c["ratio_to_machine_eps"] else f"  {k}: {c}")
    save_json(res, args.out)


if __name__ == "__main__":
    main()
