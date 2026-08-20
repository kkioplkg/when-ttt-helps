#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Freeze the published episode manifest.

The fresh computation is driven by THIS FILE, not by a glob and not by
regenerating `episode_indices(n, k, seed*977 + sev)` under a different NumPy.
Both alternatives were in design v1 and both were removed: a glob is sensitive
to whatever files happen to exist on the machine that runs it, and reproducing
an RNG call across software stacks is avoidable risk when the indices are
sitting in the records.

Run once, on the machine that holds `experiments/results/e2/`, and ship the
output.  It records, for every published stochastic run:

    (dataset, method, source_seed) -> {(corruption, severity): [idx, ...]}

plus the union per dataset (which is what the published seed-0 feature map
covered, and therefore what the PUBLISHED-STYLE arm needs), and the cross-seed
census that must reproduce the manuscript's disclosed 66.7% / 58.8%.

The census is an ASSERTION, not a printout: if the manifest this builds does not
reproduce the disclosed percentages and cell counts, the manifest is wrong and
nothing downstream of it is worth computing.
"""
import argparse
import glob
import hashlib
import json
import os

STOCHASTIC = ("ttt_rot", "ttt_mask")
# the manuscript's own disclosed figures, which this manifest must reproduce
DISCLOSED = {
    "ttt_rot": {"frac_cross_seed": 0.667, "cells_with_any": ("all", 105)},
    "ttt_mask": {"frac_cross_seed": 0.588, "cells_with_any": (75, 105)},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs = {}
    files = []
    for p in sorted(glob.glob(os.path.join(args.e2_dir, "*_main_*.json"))):
        base = os.path.basename(p)
        if "_lr" in base or "bntrain" in base:
            continue
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        argv = o["meta"]["argv"]
        if argv["method"] not in STOCHASTIC:
            continue
        if argv.get("bn_mode", "eval") != "eval":
            continue
        key = f"{argv['dataset']}|{argv['method']}|{int(argv['seed'])}"
        cells = {}
        for cell in o["results"]:
            ck = f"{cell['corruption']}|{int(cell['severity'])}"
            cells[ck] = sorted(int(e["idx"]) for e in cell["episodes"])
        runs[key] = cells
        with open(p, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        files.append({"file": base, "sha256": sha, "n_cells": len(cells),
                      "n_episodes": sum(len(v) for v in cells.values())})

    assert runs, f"no stochastic main records under {args.e2_dir}"

    # ---- per-dataset union: what the published seed-0 map had to cover ----
    union = {}
    for key, cells in runs.items():
        ds = key.split("|")[0]
        u = union.setdefault(ds, {})
        for ck, idxs in cells.items():
            u.setdefault(ck, set()).update(idxs)
    union = {ds: {ck: sorted(v) for ck, v in sorted(c.items())}
             for ds, c in sorted(union.items())}

    # ---- cross-seed census, per method, over EPISODES and over CELLS ------
    census = {}
    for meth in STOCHASTIC:
        n_tot = n_cross = 0
        cells_any, cells_tot = set(), set()
        for key, cells in runs.items():
            ds, m, seed = key.split("|")
            if m != meth:
                continue
            seed = int(seed)
            for ck, idxs in cells.items():
                n = len(idxs)
                n_tot += n
                cells_tot.add((ds, ck))
                if seed != 0:                       # measured through net 0
                    n_cross += n
                    cells_any.add((ds, ck))
        census[meth] = {
            "n_episodes": n_tot, "n_cross_seed": n_cross,
            "frac_cross_seed": n_cross / n_tot,
            "n_cells": len(cells_tot),
            "n_cells_with_any_cross_seed": len(cells_any),
        }

    # ---- the assertion the whole manifest stands on ----------------------
    bad = []
    for meth, want in DISCLOSED.items():
        got = census[meth]
        if abs(got["frac_cross_seed"] - want["frac_cross_seed"]) > 0.0015:
            bad.append(f"{meth}: cross-seed fraction {got['frac_cross_seed']:.4f}, "
                       f"manuscript discloses {want['frac_cross_seed']}")
        want_any, want_tot = want["cells_with_any"]
        if got["n_cells"] != want_tot:
            bad.append(f"{meth}: {got['n_cells']} cells, manuscript says {want_tot}")
        exp_any = got["n_cells"] if want_any == "all" else want_any
        if got["n_cells_with_any_cross_seed"] != exp_any:
            bad.append(f"{meth}: {got['n_cells_with_any_cross_seed']} cells carry a "
                       f"cross-seed episode, manuscript says {exp_any}")
    if bad:
        raise SystemExit("MANIFEST DOES NOT REPRODUCE THE DISCLOSED CENSUS:\n  "
                         + "\n  ".join(bad))

    out = {
        "note": ("frozen episode manifest for the seed-matched delta_feat "
                 "experiment; the fresh computation is driven by this file "
                 "and never by a glob or by regenerating the episode RNG"),
        "source_files": files,
        "runs": {k: v for k, v in sorted(runs.items())},
        "union_by_dataset": union,
        "cross_seed_census": census,
        "disclosed_census_reproduced": True,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    with open(args.out, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    print(f"[manifest] {len(runs)} runs, "
          f"{sum(sum(len(v) for v in c.values()) for c in runs.values())} episodes")
    for ds, u in union.items():
        print(f"[manifest] {ds}: union {len(u)} cells, "
              f"{sum(len(v) for v in u.values())} distinct observations")
    for meth, c in census.items():
        print(f"[manifest] {meth}: {100*c['frac_cross_seed']:.1f}% cross-seed "
              f"({c['n_cross_seed']}/{c['n_episodes']}), "
              f"{c['n_cells_with_any_cross_seed']}/{c['n_cells']} cells affected")
    print(f"[manifest] disclosed census REPRODUCED; wrote {args.out}")
    print(f"[manifest] sha256 {sha}")


if __name__ == "__main__":
    main()
