#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""How big is "cross-model measurement noise", against its own natural scale?

The objection this addresses treats measuring delta_feat through a DIFFERENT SEED's
network as a defect.  That framing has an implicit baseline: it assumes the
same seed's network would have given the same answer.  It would not, because
the published networks and the fresh ones are different realizations of the
same recipe under a different execution stack.

So there are two disagreements to compare, at exactly the same level and with
exactly the same statistic:

  CROSS-SEED          fresh network s  vs  fresh network 0   (s in {1,2})
                      -- the defect the manuscript disclosed

  CROSS-REALIZATION   published network 0 vs fresh network 0
                      -- two independent training runs of the SAME seed,
                         i.e. ordinary training nondeterminism

If cross-seed disagreement is no larger than cross-realization disagreement,
then "measured through the wrong seed's network" is not a special defect: it is
the same order as the irreducible noise between any two training runs, and no
retained-checkpoint discipline could have removed it.

Both are computed WITHIN CELL, the level at which the manuscript's damaging
-0.144 audit lives, and pooled at episode level for reference.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_stats as S  # noqa: E402

SEEDS = [0, 1, 2]


def load_crossed(cross_dir, ds, m):
    with open(os.path.join(cross_dir, f"crossed_{ds}_s{m}.json"), encoding="utf-8") as f:
        return {(r["corruption"], int(r["severity"]), int(r["idx"])): r["delta_feat"]
                for r in json.load(f)["records"]}


def load_published(e5_dir, ds):
    with open(os.path.join(e5_dir, f"delta_feat_{ds}_resnet26ttt.json"),
              encoding="utf-8") as f:
        o = json.load(f)
    assert int(o.get("model_seed", 0)) == 0
    return {(r["corruption"], int(r["severity"]), int(r["idx"])): float(r["delta_feat"])
            for r in o["records"]}


def within_cell(a, b, keys):
    cells = {}
    for k in keys:
        cells.setdefault((k[0], k[1]), [[], []])
        cells[(k[0], k[1])][0].append(a[k])
        cells[(k[0], k[1])][1].append(b[k])
    return [S.spearman(v[0], v[1]) for v in cells.values()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cross-dir", required=True)
    ap.add_argument("--e5-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {"script": "sm_noise_scale.py", "per_dataset": {}}
    for ds in ("cifar10", "cifar100"):
        fresh = {m: load_crossed(args.cross_dir, ds, m) for m in SEEDS}
        pub = load_published(args.e5_dir, ds)
        keys = sorted(set(pub) & set.intersection(*[set(v) for v in fresh.values()]))

        cross_seed = {}
        for s in (1, 2):
            wc = within_cell(fresh[s], fresh[0], keys)
            cross_seed[f"fresh_s{s}_vs_fresh_s0"] = {
                "within_cell": S.describe(wc, "within_cell"),
                "episode_spearman": S.spearman([fresh[s][k] for k in keys],
                                               [fresh[0][k] for k in keys])}
        wc0 = within_cell(pub, fresh[0], keys)
        cross_real = {
            "published_s0_vs_fresh_s0": {
                "within_cell": S.describe(wc0, "within_cell"),
                "episode_spearman": S.spearman([pub[k] for k in keys],
                                               [fresh[0][k] for k in keys])}}

        cs_med = float(np.median([v["within_cell"]["median"]
                                  for v in cross_seed.values()]))
        cr_med = cross_real["published_s0_vs_fresh_s0"]["within_cell"]["median"]
        out["per_dataset"][ds] = {
            "n_keys": len(keys),
            "cross_seed": cross_seed,
            "cross_realization": cross_real,
            "median_within_cell_cross_seed": cs_med,
            "median_within_cell_cross_realization": cr_med,
            "cross_seed_minus_cross_realization": cs_med - cr_med,
        }
        print(f"[sm:noise] {ds}: n={len(keys)}")
        for k, v in cross_seed.items():
            print(f"[sm:noise]   CROSS-SEED        {k:26s} within-cell median "
                  f"{v['within_cell']['median']:+.4f}  episode "
                  f"{v['episode_spearman']:+.4f}")
        v = cross_real["published_s0_vs_fresh_s0"]
        print(f"[sm:noise]   CROSS-REALIZATION {'published_s0_vs_fresh_s0':26s} "
              f"within-cell median {v['within_cell']['median']:+.4f}  episode "
              f"{v['episode_spearman']:+.4f}")
        print(f"[sm:noise]   difference (cross-seed - cross-realization): "
              f"{cs_med - cr_med:+.4f}")

    out["reading"] = (
        "If the difference is near zero or negative, measuring delta_feat "
        "through another SEED's network disagrees no more than two independent "
        "training runs of the SAME seed do. Cross-seed measurement is then not "
        "a special defect but ordinary training nondeterminism, and no "
        "checkpoint-retention discipline could have removed it.")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=float)
    print(f"[sm:noise] wrote {args.out}")


if __name__ == "__main__":
    main()
