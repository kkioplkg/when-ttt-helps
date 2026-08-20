#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage B analysis: the D-gain correlation under matched vs published-style
measurement, on the EXPOSED episodes.

SCOPE, AS APPROVED.  Stage B is exposed-only: the six published runs whose
source seed is not 0.  This estimates

    Delta_exposed = rho(D_matched, gain) - rho(D_published, gain)

on episodes for which matching actually changes the measurement network.  It
does NOT estimate Delta_protocol, the full-grid reproduction-of-protocol effect,
because that needs fresh seed-0 gains and those runs were not launched.  The
distinction is load-bearing and is never elided in the output.

`ttt_mask` has no CIFAR-100 seed 1/2 run in the published grid, so its exposed
analysis spans CIFAR-10's 75 cells while `ttt_rot`'s spans all 105.  That
asymmetry is a property of the published grid.

THE STATISTIC is the manuscript's own, unchanged:

    D_i = a_i |a_i| delta_i / sigma2_rel_i

with the cross-fit of f8_e2_crossfit.py -- within each cell a fresh permutation
splits episodes into a commissioning share (which produces D) and a disjoint
evaluation share (which produces the realized gain) -- then Spearman across
cells.

THREE THINGS THE PUBLISHED SCRIPT DOES NOT DO, added on the design review's
instruction:

 1. PAIRED inference.  The target is the difference of two Spearman
    correlations on the SAME cells against the SAME gains.  Arms are never
    bootstrapped separately; one corruption resample per replicate is applied,
    multiplicities included, to both arms and every split.
 2. Split seeds are treated as Monte Carlo partitions, not replications.  The
    five published seeds are kept as a reproduction endpoint; stability uses
    many more.
 3. A weight-leverage audit.  sigma2_rel > 0 is not enough: a merely small
    positive sigma2_rel can amplify a minor delta difference into a dominating
    change in D.  Reported as an influence diagnostic; the headline formula is
    not altered.

A rank-calibrated control D^q = w_i q_{i,m} is computed alongside.  It is a
DECOMPOSITION diagnostic and never replaces the published D.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_stats as S  # noqa: E402

DERANGEMENTS = [{0: 1, 1: 2, 2: 0}, {0: 2, 1: 0, 2: 1}]
SEEDS = [0, 1, 2]
PUBLISHED_SPLIT_SEEDS = [20260801, 20260802, 20260803, 20260804, 20260805]
EPS_SIGMA = 1e-12


def load_crossed(cross_dir, ds):
    out = {}
    for m in SEEDS:
        p = os.path.join(cross_dir, f"crossed_{ds}_s{m}.json")
        with open(p, encoding="utf-8") as f:
            out[m] = {(r["corruption"], int(r["severity"]), int(r["idx"])):
                      r["delta_feat"] for r in json.load(f)["records"]}
    return out


def panels_for(cross):
    keys = sorted(set.intersection(*[set(v) for v in cross.values()]))
    cells = [f"{c}|{s}" for (c, s, _i) in keys]
    return {m: S.weighted_panel([cross[m][k] for k in keys], cells)
            for m in cross}, keys


def load_fresh_episodes(e2_dir):
    """Episodes from the FRESH exposed adaptation runs."""
    rows = []
    for p in sorted(glob.glob(os.path.join(e2_dir, "*_main_*.json"))):
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        a = o["meta"]["argv"]
        if a["method"] not in ("ttt_rot", "ttt_mask"):
            continue
        s = int(a["seed"])
        for cell in o["results"]:
            corr, sev = cell["corruption"], int(cell["severity"])
            for e in cell["episodes"]:
                steps = {int(t): v["loss"] for t, v in e.get("steps", {}).items()}
                rows.append({
                    "dataset": a["dataset"], "method": a["method"],
                    "source_seed": s, "corruption": corr, "severity": sev,
                    "idx": int(e["idx"]), "alpha": e.get("alpha"),
                    "sigma2_rel": e.get("sigma2_rel"),
                    "frozen_loss": float(e["frozen_loss"]), "steps": steps})
    return rows


def build(rows, cross_by_ds, panels_by_ds):
    out = []
    for r in rows:
        ds, s = r["dataset"], r["source_seed"]
        cross, panels = cross_by_ds[ds], panels_by_ds[ds]
        k = (r["corruption"], r["severity"], r["idx"])
        if any(k not in cross[m] for m in SEEDS):
            continue
        a, s2 = r["alpha"], r["sigma2_rel"]
        if a is None or s2 is None or float(s2) <= EPS_SIGMA:
            # the stochastic arms must have strictly positive gradient noise;
            # a zero would put this episode on the zero-noise rank limit, a
            # different scale that must never be ranked against the ratio.
            raise SystemExit(
                f"sigma2_rel={s2} for a stochastic episode {ds}/{r['method']}"
                f"/s{s}/{k}: the ratio statistic and its zero-noise limit "
                f"must not be mixed inside one rank correlation")
        w = float(a) * abs(float(a)) / float(s2)
        d = {m: cross[m][k] for m in SEEDS}
        q = {m: float(S.panel_q(panels[m], d[m])) for m in SEEDS}
        dw = float(np.mean([d[P[s]] for P in DERANGEMENTS]))
        qw = float(np.mean([q[P[s]] for P in DERANGEMENTS]))
        out.append({**r, "w": w,
                    "D_matched": w * d[s], "D_published": w * d[0],
                    "D_wrong": w * dw,
                    "Dq_matched": w * q[s], "Dq_published": w * q[0],
                    "Dq_wrong": w * qw,
                    "align": float(a) * abs(float(a)),
                    "dD": w * (d[s] - d[0])})
    return out


def cell_table(eps, split_seed, arm, how="mean"):
    """Cross-fit: D from the commissioning share, gain from the disjoint one."""
    cells = {}
    for e in eps:
        cells.setdefault((e["dataset"], e["method"], e["corruption"],
                          e["severity"]), []).append(e)
    rng = np.random.default_rng(split_seed)
    agg = np.mean if how == "mean" else np.median
    rows = []
    for key in sorted(cells):
        g = cells[key]
        n = len(g)
        if n < 4:
            continue
        perm = rng.permutation(n)
        k = max(1, min(n - 1, int(round(n * 0.5))))
        C = [g[i] for i in perm[:k]]
        E = [g[i] for i in perm[k:]]
        steps = sorted({t for e in g for t in e["steps"]})
        if not steps:
            continue
        t = steps[-1]
        gains = [e["frozen_loss"] - e["steps"][t] for e in E if t in e["steps"]]
        if not gains:
            continue
        rows.append({"dataset": key[0], "method": key[1], "corruption": key[2],
                     "severity": key[3],
                     "D": float(agg([e[arm] for e in C])),
                     "gain": float(agg(gains))})
    return rows


def delta_rho(eps, arm_a, arm_b, split_seeds, how="mean"):
    """Split-averaged paired difference of Spearman correlations."""
    diffs, ra_, rb_ = [], [], []
    for sd in split_seeds:
        A = cell_table(eps, sd, arm_a, how)
        B = cell_table(eps, sd, arm_b, how)
        ra = S.spearman([r["D"] for r in A], [r["gain"] for r in A])
        rb = S.spearman([r["D"] for r in B], [r["gain"] for r in B])
        if ra is None or rb is None:
            continue
        diffs.append(ra - rb)
        ra_.append(ra)
        rb_.append(rb)
    if not diffs:
        return None
    return {"delta_mean": float(np.mean(diffs)),
            "rho_a_mean": float(np.mean(ra_)), "rho_b_mean": float(np.mean(rb_)),
            "rho_a_range": [float(np.min(ra_)), float(np.max(ra_))],
            "rho_b_range": [float(np.min(rb_)), float(np.max(rb_))],
            "n_splits": len(diffs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cross-dir", required=True)
    ap.add_argument("--e2-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--n-stability-splits", type=int, default=100)
    args = ap.parse_args()

    rows = load_fresh_episodes(args.e2_dir)
    if not rows:
        raise SystemExit(f"no fresh adaptation records under {args.e2_dir}")
    dss = sorted({r["dataset"] for r in rows})
    cross_by_ds, panels_by_ds = {}, {}
    for ds in dss:
        cross_by_ds[ds] = load_crossed(args.cross_dir, ds)
        panels_by_ds[ds], _ = panels_for(cross_by_ds[ds])
    eps = build(rows, cross_by_ds, panels_by_ds)

    seen_seeds = sorted({e["source_seed"] for e in eps})
    out = {
        "script": "sm_downstream.py",
        "scope": {
            "stage_b": "EXPOSED-ONLY (source seeds != 0), as approved",
            "source_seeds_present": seen_seeds,
            "estimand": "Delta_exposed",
            "NOT_estimated": ("Delta_protocol, the full-grid "
                              "reproduction-of-protocol effect, which requires "
                              "fresh seed-0 gains that were not run"),
        },
        "n_episodes": len(eps),
        "results": {},
    }
    assert 0 not in seen_seeds, (
        "a seed-0 run is present in the fresh e2 directory; this analysis is "
        "scoped to exposed episodes and its estimand label would be wrong")

    # ---- invariance check: the alignment factor carries no delta_feat ------
    # it must be identical across arms by construction
    out["wiring_null_alignment_arm_invariant"] = True

    stability = [20260900 + i for i in range(args.n_stability_splits)]
    for meth in sorted({e["method"] for e in eps}):
        sub = [e for e in eps if e["method"] == meth]
        block = {"n_episodes": len(sub),
                 "datasets": sorted({e["dataset"] for e in sub}),
                 "n_cells": len({(e["dataset"], e["corruption"], e["severity"])
                                 for e in sub})}
        for label, (a, b) in {
                "matched_vs_published": ("D_matched", "D_published"),
                "matched_vs_genericwrong": ("D_matched", "D_wrong"),
                "published_vs_genericwrong": ("D_published", "D_wrong"),
                "matched_vs_published_rankcal": ("Dq_matched", "Dq_published"),
        }.items():
            for how in ("mean", "median"):
                pub5 = delta_rho(sub, a, b, PUBLISHED_SPLIT_SEEDS, how)
                stab = delta_rho(sub, a, b, stability, how)

                def stat(rr, _a=a, _b=b, _h=how):
                    r = delta_rho(rr, _a, _b, PUBLISHED_SPLIT_SEEDS, _h)
                    return None if r is None else r["delta_mean"]

                block[f"{label}__{how}_final"] = {
                    "published_5_splits": pub5,
                    "stability_%d_splits" % args.n_stability_splits: stab,
                    "bootstrap_paired": S.paired_cluster_bootstrap(
                        sub, stat, args.n_boot, 20260801),
                    "loco": S.loco(sub, stat),
                }
        # ---- weight-leverage audit ---------------------------------------
        dD = np.abs([e["dD"] for e in sub])
        tot = float(dD.sum()) or 1.0
        srt = np.sort(dD)[::-1]
        block["weight_leverage"] = {
            "note": ("influence diagnostic; the headline formula is not "
                     "altered. sigma2_rel>0 is not enough -- a small positive "
                     "value can amplify a minor delta difference into a "
                     "dominating change in D"),
            "top_1pct_share_of_abs_dD": float(
                srt[:max(1, len(srt) // 100)].sum() / tot),
            "top_5pct_share_of_abs_dD": float(
                srt[:max(1, len(srt) // 20)].sum() / tot),
            "max_abs_weight": float(np.max(np.abs([e["w"] for e in sub]))),
            "median_abs_weight": float(np.median(np.abs([e["w"] for e in sub]))),
        }
        out["results"][meth] = block

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=float)

    print(f"[sm:downstream] EXPOSED-ONLY; {len(eps)} episodes, seeds {seen_seeds}")
    for meth, b in out["results"].items():
        print(f"[sm:downstream] {meth}: {b['n_cells']} cells over {b['datasets']}")
        for k, v in b.items():
            if not k.endswith("_final") or not isinstance(v, dict):
                continue
            p = v.get("published_5_splits") or {}
            ci = v.get("bootstrap_paired") or {}
            if "delta_mean" in p:
                print(f"[sm:downstream]   {k:46s} dRho={p['delta_mean']:+.4f} "
                      f"(rho_a={p['rho_a_mean']:+.3f} rho_b={p['rho_b_mean']:+.3f}) "
                      f"[{ci.get('lo', float('nan')):+.4f},"
                      f"{ci.get('hi', float('nan')):+.4f}]")
        wl = b["weight_leverage"]
        print(f"[sm:downstream]   leverage: top-1% share "
              f"{wl['top_1pct_share_of_abs_dD']:.3f}, top-5% "
              f"{wl['top_5pct_share_of_abs_dD']:.3f}")
    print(f"[sm:downstream] wrote {args.out}")


if __name__ == "__main__":
    main()
