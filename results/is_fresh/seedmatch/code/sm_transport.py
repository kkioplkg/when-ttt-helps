#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Transport diagnostics: how good a stand-in is the fresh realization for the
lost published one?

The published checkpoints are gone, but that does NOT mean there is no
information about the lost models.  The published per-episode records retain,
on keys this experiment can match exactly:

    results/e5/delta_feat_{dataset}_{arch}.json   the seed-0 delta_feat values
    results/e2/*_main_*.json                      per-episode frozen_loss,
                                                  frozen_correct, confidence

This script compares those retained quantities against the freshly measured
ones on identical (corruption, severity, idx) keys.  It is the single best
piece of evidence available about whether the fresh networks are a reasonable
transport vehicle for the historical question, and the design review is right
that it belongs in the middle of the report rather than in an appendix.

The comparison that matters most is old-seed-0 delta_feat against NEW-seed-0
delta_feat.  Both are "the seed-0 network's feature distance" under the same
definition on the same images; they differ only by the training realization.
If the fresh seed-0 network does not even preserve the old seed-0 network's
ORDERING of images, then no contrast computed on the fresh family transports to
the published grid, and the report must say so rather than quietly proceed.

Nothing here is a pass/fail gate.  It is a reported diagnostic that scopes the
strength of every downstream claim.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_stats as S  # noqa: E402

ARCH = "resnet26ttt"


def load_published_dfeat(e5_dir, dataset):
    p = os.path.join(e5_dir, f"delta_feat_{dataset}_{ARCH}.json")
    with open(p, encoding="utf-8") as f:
        o = json.load(f)
    assert int(o.get("model_seed", 0)) == 0, "published map is not the seed-0 map"
    return {(r["corruption"], int(r["severity"]), int(r["idx"])):
            float(r["delta_feat"]) for r in o["records"]}, os.path.basename(p)


def load_published_episodes(e2_dir, dataset):
    """{(seed, corr, sev, idx): frozen_loss} from the stochastic main runs."""
    out = {}
    for p in sorted(glob.glob(os.path.join(e2_dir, f"{dataset}_*_main_*.json"))):
        b = os.path.basename(p)
        if "_lr" in b or "bntrain" in b:
            continue
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        argv = o["meta"]["argv"]
        if argv["method"] not in ("ttt_rot", "ttt_mask"):
            continue
        s = int(argv["seed"])
        for cell in o["results"]:
            c, v = cell["corruption"], int(cell["severity"])
            for e in cell["episodes"]:
                out[(s, c, v, int(e["idx"]))] = float(e["frozen_loss"])
    return out


def load_fresh(cross_dir, dataset, m):
    p = os.path.join(cross_dir, f"crossed_{dataset}_s{m}.json")
    with open(p, encoding="utf-8") as f:
        o = json.load(f)
    return {(r["corruption"], int(r["severity"]), int(r["idx"])): r
            for r in o["records"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cross-dir", required=True)
    ap.add_argument("--e5-dir", required=True)
    ap.add_argument("--e2-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {"script": "sm_transport.py", "per_dataset": {}}
    for ds in ("cifar10", "cifar100"):
        fresh_p = os.path.join(args.cross_dir, f"crossed_{ds}_s0.json")
        if not os.path.exists(fresh_p):
            continue
        old, oldfile = load_published_dfeat(args.e5_dir, ds)
        new0 = load_fresh(args.cross_dir, ds, 0)
        keys = sorted(set(old) & set(new0))
        o = np.array([old[k] for k in keys])
        n = np.array([new0[k]["delta_feat"] for k in keys])

        # cell-mean agreement, the level the downstream analysis consumes
        cm = {}
        for k, a, b in zip(keys, o, n):
            cm.setdefault((k[0], k[1]), [[], []])
            cm[(k[0], k[1])][0].append(a)
            cm[(k[0], k[1])][1].append(b)
        co = [float(np.mean(v[0])) for v in cm.values()]
        cn = [float(np.mean(v[1])) for v in cm.values()]

        # within-cell ordering agreement: the level the -0.144 audit lives at
        wc = [S.spearman(v[0], v[1]) for v in cm.values()]

        # affine calibration of new on old
        A = np.polyfit(o, n, 1) if len(o) > 2 else [np.nan, np.nan]

        # labelled-risk comparison against the lost networks, where keys match
        eps = load_published_episodes(args.e2_dir, ds)
        old_L, new_L = [], []
        for (s, c, v, i), fl in eps.items():
            r = load_fresh.__wrapped__ if False else None  # noqa: F841
            kk = (c, v, i)
            fp = os.path.join(args.cross_dir, f"crossed_{ds}_s{s}.json")
            if not os.path.exists(fp):
                continue
            old_L.append((s, kk, fl))
        # group by seed so each fresh file is opened once
        byseed = {}
        for s, kk, fl in old_L:
            byseed.setdefault(s, []).append((kk, fl))
        Lcmp = {}
        for s, items in sorted(byseed.items()):
            tab = load_fresh(args.cross_dir, ds, s)
            a = [fl for kk, fl in items if kk in tab]
            b = [tab[kk]["frozen_loss"] for kk, fl in items if kk in tab]
            if len(a) > 2:
                Lcmp[str(s)] = {
                    "n": len(a),
                    "spearman_old_vs_fresh_frozen_loss": S.spearman(a, b),
                    "mean_old": float(np.mean(a)), "mean_fresh": float(np.mean(b)),
                }

        out["per_dataset"][ds] = {
            "published_source": oldfile,
            "n_matched_keys": len(keys),
            "old_seed0_vs_new_seed0": {
                "episode_spearman": S.spearman(o, n),
                "episode_pearson": float(np.corrcoef(o, n)[0, 1]),
                "cell_mean_spearman": S.spearman(co, cn),
                "within_cell_spearman": S.describe(wc, "within_cell"),
                "affine_new_on_old": {"slope": float(A[0]), "intercept": float(A[1])},
                "mean_old": float(o.mean()), "sd_old": float(o.std()),
                "mean_new": float(n.mean()), "sd_new": float(n.std()),
            },
            "old_vs_fresh_frozen_loss_by_source_seed": Lcmp,
        }

    out["reading"] = (
        "If new-seed-0 does not preserve old-seed-0's ordering (episode and "
        "within-cell Spearman well below 1), the fresh family is a weak "
        "transport vehicle for the published grid and every contrast computed "
        "on it is scoped accordingly. These are diagnostics, not gates.")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=float)
    for ds, v in out["per_dataset"].items():
        a = v["old_seed0_vs_new_seed0"]
        print(f"[sm:transport] {ds}: n={v['n_matched_keys']} "
              f"episode rho={a['episode_spearman']:+.4f} "
              f"cell-mean rho={a['cell_mean_spearman']:+.4f} "
              f"within-cell median={a['within_cell_spearman']['median']:+.4f}")
    print(f"[sm:transport] wrote {args.out}")


if __name__ == "__main__":
    main()
