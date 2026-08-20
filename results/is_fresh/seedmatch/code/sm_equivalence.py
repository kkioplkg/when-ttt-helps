#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prove the port: recompute the PUBLISHED delta_feat audit with this package's
statistics helpers and require agreement with the published JSON.

`sm_stats.spearman` is a verbatim port from `is_fresh/f14_deltafeat_check.py`
and `f8_e2_crossfit.py`.  A verbatim port is a claim, not a fact, so it is
checked: this script recomputes f14's three headline quantities from the
ORIGINAL records --

    results/e5/delta_feat_{dataset}_{arch}.json
    results/e2/*_main_*.json

-- using only `sm_stats`, and compares them to
`results/is_fresh/f14_deltafeat_check.json`.  If they do not agree, every
number this package produces is suspect and it exits non-zero.

It also recomputes the split the design review's audit exposed: the published
"23 of 60 triples increase strictly across severities 1--5" pools a genuine
five-severity test (CIFAR-10) with a two-point test (CIFAR-100, whose
stochastic grid covers severities 3 and 5 only).  The per-dataset split is
printed so the new report can state it correctly.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_stats as S  # noqa: E402

METHOD_ARCH = {"ttt_rot": "resnet26ttt", "ttt_mask": "resnet26ttt",
               "tent": "wrn2810", "pl": "wrn2810"}
TOL = 1e-9


def load_dfeat(e5_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(e5_dir, "delta_feat_*.json"))):
        b = os.path.basename(p)
        parts = b[len("delta_feat_"):-len(".json")].split("_")
        if len(parts) != 2:
            continue
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        out[(o.get("dataset", parts[0]), o.get("arch", parts[1]))] = o["records"]
    return out


def load_eps(e2_dir):
    rows = []
    for fn in sorted(os.listdir(e2_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(e2_dir, fn), encoding="utf-8") as f:
            o = json.load(f)
        argv = o.get("meta", {}).get("argv", {})
        if argv.get("mode", "main") != "main":
            continue
        ds, meth = argv["dataset"], argv["method"]
        for cell in o.get("results", []):
            for e in cell.get("episodes", []):
                if e.get("idx") is None:
                    continue
                rows.append({"src": fn, "dataset": ds, "method": meth,
                             "arch": METHOD_ARCH[meth],
                             "corruption": cell["corruption"],
                             "severity": int(cell["severity"]),
                             "idx": int(e["idx"]),
                             "frozen_loss": float(e["frozen_loss"])})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e5-dir", required=True)
    ap.add_argument("--e2-dir", required=True)
    ap.add_argument("--published", required=True,
                    help="results/is_fresh/f14_deltafeat_check.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.published, encoding="utf-8") as f:
        pub = json.load(f)

    dfeat = load_dfeat(args.e5_dir)
    eps = load_eps(args.e2_dir)

    # ---- (A) severity monotonicity, per (dataset, arch, corruption) -------
    triples = []
    for (ds, arch), recs in sorted(dfeat.items()):
        by = {}
        for r in recs:
            by.setdefault(r["corruption"], {}).setdefault(
                int(r["severity"]), []).append(float(r["delta_feat"]))
        for corr in sorted(by):
            sevs = sorted(by[corr])
            means = [float(np.mean(by[corr][s])) for s in sevs]
            allv = [v for s in sevs for v in by[corr][s]]
            alls = [s for s in sevs for _ in by[corr][s]]
            triples.append({
                "dataset": ds, "arch": arch, "corruption": corr,
                "severities": sevs, "n_sev": len(sevs),
                "strict": bool(all(b > a for a, b in zip(means, means[1:]))),
                "rho_ep": S.spearman(alls, allv)})
    n_tot = len(triples)
    n_strict = sum(1 for t in triples if t["strict"])
    med_rho_ep = float(np.median([t["rho_ep"] for t in triples
                                  if t["rho_ep"] is not None]))

    # ---- (B) within-cell rho(delta_feat, frozen labelled loss) -----------
    fmap = {(ds, arch): {(r["corruption"], int(r["severity"]), int(r["idx"])):
                         float(r["delta_feat"]) for r in recs}
            for (ds, arch), recs in dfeat.items()}
    cells = {}
    for e in eps:
        d = fmap.get((e["dataset"], e["arch"]), {}).get(
            (e["corruption"], e["severity"], e["idx"]))
        if d is None:
            continue
        cells.setdefault((e["dataset"], e["method"], e["corruption"],
                          e["severity"]), []).append((d, e["frozen_loss"]))
    within = [S.spearman([a for a, _ in v], [b for _, b in v])
              for v in cells.values()]
    within = [w for w in within if w is not None]
    med_within = float(np.median(within))

    # ---- compare against the published record -----------------------------
    A = pub["A_severity_monotonicity"]
    B = pub["B_labelled_risk"]["within_cell_rho_delta_feat_vs_frozen_loss"]
    checks = [
        ("n_triples", n_tot, A["n_triples_dataset_arch_corruption"]),
        ("n_strictly_increasing", n_strict, A["n_strictly_increasing_mean"]),
        ("median_episode_rho_severity", med_rho_ep,
         A["episode_level_rho_severity"]["median"]),
        ("n_cells_within", len(within), B["n_cells"]),
        ("median_within_cell_rho", med_within, B["median"]),
    ]
    bad = [(k, g, w) for k, g, w in checks
           if (abs(g - w) > TOL if isinstance(g, float) else g != w)]

    # ---- the split the pooled published figure conceals -------------------
    split = {}
    for t in triples:
        k = f"{t['dataset']}({t['n_sev']} severity points)"
        split.setdefault(k, {"n": 0, "strict": 0, "severities": t["severities"]})
        split[k]["n"] += 1
        split[k]["strict"] += int(t["strict"])

    out = {
        "script": "sm_equivalence.py",
        "purpose": ("prove sm_stats reproduces the published f14 audit before "
                    "any fresh number is computed with it"),
        "published_file": os.path.basename(args.published),
        "checks": [{"name": k, "recomputed": g, "published": w,
                    "agree": not any(k == b[0] for b in bad)}
                   for k, g, w in checks],
        "all_agree": not bad,
        "pooled_published_figure_split_by_dataset": split,
    }
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, sort_keys=True, default=float)

    for k, g, w in checks:
        mark = "OK " if not any(k == b[0] for b in bad) else "FAIL"
        gs = f"{g:.6f}" if isinstance(g, float) else str(g)
        ws = f"{w:.6f}" if isinstance(w, float) else str(w)
        print(f"[sm:equiv] {mark} {k:32s} recomputed={gs:>12s} published={ws:>12s}")
    print()
    print("[sm:equiv] the pooled '23 of 60' figure, split by what it actually tests:")
    for k, v in sorted(split.items()):
        print(f"[sm:equiv]   {k:34s} {v['strict']:2d}/{v['n']:2d} strictly "
              f"increasing over severities {v['severities']}")
    if bad:
        raise SystemExit(f"[sm:equiv] PORT NOT PROVEN: {bad}")
    print("\n[sm:equiv] PORT PROVEN: sm_stats reproduces the published f14 audit exactly")


if __name__ == "__main__":
    main()
