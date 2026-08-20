#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage 1 analysis: does same-network measurement change delta_feat, and does
it change what delta_feat is FOR?

Reads only the crossed measurement matrix (`crossed_{dataset}_s{m}.json`) and
the frozen episode manifest.  No adaptation records are required, which is the
point: the two most damaging published findings about delta_feat -- its
severity behaviour and its within-cell relation to the source model's labelled
frozen loss -- involve no test-time adaptation at all, so they can be re-tested
from the source networks alone.

ARMS.  For an episode whose adaptation ran on source seed s:
    MATCHED          measured through network s
    PUBLISHED-STYLE  measured through network 0, for every s
    GENERIC-WRONG    mean over the two complete derangements
                     P1: 0->1, 1->2, 2->0    P2: 0->2, 1->0, 2->1
MATCHED vs PUBLISHED-STYLE is the measurement-rule contrast.
MATCHED vs GENERIC-WRONG asks whether being on *a* wrong network matters, with
measurement-network identity balanced.
PUBLISHED-STYLE vs GENERIC-WRONG asks whether seed 0 is an ATYPICAL wrong
network -- a question no two-arm design can pose.

PRIMARY ENDPOINT (section 5.1 of DESIGN.md).  For every actually-mismatched
(cell, source seed) pair with s in {1,2},

    dr_{c,s} = rho_i( d_{i,s}, L_{i,s} ) - rho_i( d_{i,0}, L_{i,s} )

within cell c, where L_{i,s} is the labelled frozen loss of the network the
episode actually ran on.  This is sharp for a reason the raw difference
distribution is not: within-cell Spearman is ALREADY invariant to any
per-network offset and positive rescaling, so an objection that claims the
published median -0.144 arose from cross-network measurement cannot rescue the
claim by pointing at large raw cosine-distance differences.  They need genuine
image-order disagreement between networks, and that is what dr measures.

The raw per-episode difference distribution is retained as a MECHANISM
diagnostic and is explicitly not the headline.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_stats as S  # noqa: E402

DERANGEMENTS = [{0: 1, 1: 2, 2: 0}, {0: 2, 1: 0, 2: 1}]
SEEDS = [0, 1, 2]


# ------------------------------------------------------------------ loading

def load_crossed(cross_dir, dataset):
    """{m: {(corr, sev, idx): (delta_feat, frozen_loss, frozen_correct)}}"""
    out = {}
    for m in SEEDS:
        p = os.path.join(cross_dir, f"crossed_{dataset}_s{m}.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            o = json.load(f)
        out[m] = {(r["corruption"], int(r["severity"]), int(r["idx"])):
                  (r["delta_feat"], r["frozen_loss"], r["frozen_correct"])
                  for r in o["records"]}
    return out


def build_panels(cross, dataset):
    """Equal-cell-weighted reference panel per measurement network.

    Every network is scored on exactly the same tuples (the manifest union), so
    the panels are directly comparable and mu/sd/CDF differences between them
    are network properties, not sampling differences.
    """
    keys = sorted(set.intersection(*[set(v) for v in cross.values()]))
    cell_ids = [f"{c}|{s}" for (c, s, _i) in keys]
    panels = {}
    for m, tab in cross.items():
        vals = [tab[k][0] for k in keys]
        panels[m] = S.weighted_panel(vals, cell_ids)
    return panels, keys


# ------------------------------------------------------------------ episodes

def episode_rows(manifest, cross, panels, dataset, method):
    """One row per published episode, carrying every arm's measurement."""
    rows = []
    for key, cells in manifest["runs"].items():
        ds, meth, seed = key.split("|")
        if ds != dataset or meth != method:
            continue
        s = int(seed)
        for ck, idxs in cells.items():
            corr, sev = ck.split("|")
            sev = int(sev)
            for i in idxs:
                k = (corr, sev, int(i))
                if any(k not in cross[m] for m in SEEDS):
                    continue
                d = {m: cross[m][k][0] for m in SEEDS}
                L = {m: cross[m][k][1] for m in SEEDS}
                ok = {m: cross[m][k][2] for m in SEEDS}
                q = {m: float(S.panel_q(panels[m], d[m])) for m in SEEDS}
                z = {m: (d[m] - panels[m]["mu"]) / (panels[m]["sd"] + 1e-12)
                     for m in SEEDS}
                rows.append({
                    "dataset": ds, "method": meth, "source_seed": s,
                    "corruption": corr, "severity": sev, "idx": int(i),
                    "cell": ck,
                    "exposed": s != 0,          # was this episode mismeasured?
                    "d_matched": d[s], "d_published": d[0],
                    "d_wrong": float(np.mean([d[P[s]] for P in DERANGEMENTS])),
                    "q_matched": q[s], "q_published": q[0],
                    "z_matched": z[s], "z_published": z[0],
                    "L_matched": L[s], "correct_matched": ok[s],
                })
    return rows


# ------------------------------------------------------------------ endpoints

def primary_concordance(rows, arm_a="d_matched", arm_b="d_published",
                        exposed_only=True):
    """Per-(cell, source seed) paired difference of within-cell Spearman
    against the SAME network's labelled frozen loss."""
    # THE GROUP KEY MUST CARRY THE DATASET.  `cell` is "corruption|severity",
    # which COLLIDES between CIFAR-10 and CIFAR-100 at severities 3 and 5 --
    # the two severities the CIFAR-100 grid runs.  Grouping on cell alone
    # silently merged the two datasets into one within-cell correlation,
    # pooling a 10-class and a 100-class problem with different loss scales and
    # different feature geometries, and collapsing ttt_rot's 210 (cell, seed)
    # pairs to 150.  The rank-calibrated control is what exposed it: within a
    # merged group q is no longer a single monotone transform of d, so
    # rho(q, L) diverged from rho(d, L) for ttt_rot while staying exactly equal
    # for the CIFAR-10-only ttt_mask.  That invariance is now asserted below.
    groups = {}
    for r in rows:
        if exposed_only and not r["exposed"]:
            continue
        groups.setdefault((r["dataset"], r["cell"], r["source_seed"]), []).append(r)
    out = []
    for (ds, cell, s), g in sorted(groups.items()):
        L = [r["L_matched"] for r in g]
        ra = S.spearman([r[arm_a] for r in g], L)
        rb = S.spearman([r[arm_b] for r in g], L)
        if ra is None or rb is None:
            continue
        out.append({"dataset": ds, "cell": cell, "corruption": cell.split("|")[0],
                    "severity": int(cell.split("|")[1]), "source_seed": s,
                    "n": len(g), "rho_a": ra, "rho_b": rb, "delta": ra - rb})
    return out


def severity_monotonicity(rows, arm):
    """The published severity statistic, recomputed under one arm.

    Reported SPLIT BY DATASET, because the published pooled figure conflates a
    genuine five-severity test (CIFAR-10) with a two-point test (CIFAR-100,
    whose stochastic grid runs severities 3 and 5 only). See DESIGN.md section 9.
    """
    by = {}
    for r in rows:
        by.setdefault((r["dataset"], r["corruption"]), {}) \
          .setdefault(r["severity"], []).append(r[arm])
    out = []
    for (ds, corr), sev_map in sorted(by.items()):
        sevs = sorted(sev_map)
        means = [float(np.mean(sev_map[s])) for s in sevs]
        allv = [v for s in sevs for v in sev_map[s]]
        alls = [s for s in sevs for _ in sev_map[s]]
        out.append({
            "dataset": ds, "corruption": corr, "severities": sevs,
            "n_severity_points": len(sevs),
            "mean_by_severity": means,
            "strictly_increasing": bool(all(b > a for a, b in zip(means, means[1:]))),
            "rho_severity_episode": S.spearman(alls, allv),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cross-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--boot-seed", type=int, default=20260801)
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)

    all_rows, per_dataset = [], {}
    for ds in ("cifar10", "cifar100"):
        cross = load_crossed(args.cross_dir, ds)
        if len(cross) != 3:
            print(f"[sm:analysis] {ds}: have {sorted(cross)} of 3 networks -- skip")
            continue
        panels, keys = build_panels(cross, ds)
        per_dataset[ds] = {
            "n_common_observations": len(keys),
            "panel": {str(m): {"mu": panels[m]["mu"], "sd": panels[m]["sd"]}
                      for m in SEEDS},
        }
        for meth in ("ttt_rot", "ttt_mask"):
            all_rows += episode_rows(manifest, cross, panels, ds, meth)

    if not all_rows:
        raise SystemExit("no episode rows: the crossed matrix is incomplete")

    out = {"script": "sm_analysis.py", "per_dataset": per_dataset,
           "n_rows": len(all_rows),
           "n_exposed": int(sum(1 for r in all_rows if r["exposed"])),
           "results": {}}

    # ---- WIRING NULLS: must hold exactly, or nothing else is meaningful ---
    seed0 = [r for r in all_rows if not r["exposed"]]
    bad = [r for r in seed0 if r["d_matched"] != r["d_published"]]
    out["wiring_null_seed0_arms_identical"] = {
        "n_seed0_rows": len(seed0), "n_disagreeing": len(bad), "pass": not bad}
    assert not bad, ("WIRING NULL FAILED: MATCHED and PUBLISHED-STYLE differ on "
                     f"{len(bad)} seed-0 episodes, where they are identical by "
                     "construction")

    # ---- WIRING NULL 2: rank-calibration invariance -----------------------
    # Within one (dataset, cell, source seed) group the measurement network is
    # fixed, so q = F_m(d) is a STRICTLY MONOTONE transform of d and Spearman
    # against L must be bit-identical.  Any divergence means the grouping has
    # pooled observations measured through different networks or scored on
    # different panels -- which is exactly the dataset-collision bug this
    # assertion was added to catch, after the rank-calibrated arm diverged for
    # ttt_rot (two datasets merged) while matching exactly for the
    # CIFAR-10-only ttt_mask.
    inv_bad = []
    for meth in ("ttt_rot", "ttt_mask"):
        rows = [r for r in all_rows if r["method"] == meth]
        if not rows:
            continue
        raw = {(r["dataset"], r["cell"], r["source_seed"]): r["rho_a"]
               for r in primary_concordance(rows, "d_matched", "d_published")}
        cal = {(r["dataset"], r["cell"], r["source_seed"]): r["rho_a"]
               for r in primary_concordance(rows, "q_matched", "q_published")}
        for k in sorted(set(raw) & set(cal)):
            if abs(raw[k] - cal[k]) > 1e-12:
                inv_bad.append((meth, k, raw[k], cal[k]))
    out["wiring_null_rank_calibration_invariance"] = {
        "n_violations": len(inv_bad), "pass": not inv_bad,
        "examples": inv_bad[:5]}
    assert not inv_bad, (
        "RANK-CALIBRATION INVARIANCE FAILED in "
        f"{len(inv_bad)} groups (e.g. {inv_bad[0]}): within a fixed "
        "(dataset, cell, source seed) group q is a strictly monotone transform "
        "of d, so the two Spearman values must be identical. A divergence "
        "means the grouping pooled different measurement networks or panels.")

    # ---- PRIMARY: same-network labelled-risk concordance ------------------
    # expected (cell, seed) counts, from the published grid: every exposed run
    # contributes its own cells, and nothing is silently merged.
    EXPECTED_PAIRS = {"ttt_rot": (75 + 30) * 2, "ttt_mask": 75 * 2}
    for meth in ("ttt_rot", "ttt_mask"):
        rows = [r for r in all_rows if r["method"] == meth]
        if not rows:
            continue
        block = {}
        for label, (a, b) in {
                "matched_vs_published": ("d_matched", "d_published"),
                "matched_vs_genericwrong": ("d_matched", "d_wrong"),
                "published_vs_genericwrong": ("d_published", "d_wrong"),
                # rank-calibrated control: removes any monotone per-network
                # recalibration, isolating genuine image-order disagreement
                "matched_vs_published_rankcal": ("q_matched", "q_published"),
        }.items():
            per_cell = primary_concordance(rows, a, b, exposed_only=True)
            if not per_cell:
                continue
            want = EXPECTED_PAIRS[meth]
            assert len(per_cell) == want, (
                f"{meth}/{label}: {len(per_cell)} (dataset, cell, seed) pairs, "
                f"expected {want} from the published grid. A mismatch means "
                f"pairs were merged or dropped.")

            def med(sub, _pc=per_cell):
                v = [r["delta"] for r in sub]
                return float(np.median(v)) if v else None

            block[label] = {
                "n_cell_seed_pairs": len(per_cell),
                "median_delta": med(per_cell),
                "distribution": S.describe([r["delta"] for r in per_cell],
                                           "delta_within_cell_rho"),
                "rho_a": S.describe([r["rho_a"] for r in per_cell], "rho_arm_a"),
                "rho_b": S.describe([r["rho_b"] for r in per_cell], "rho_arm_b"),
                "bootstrap": S.paired_cluster_bootstrap(
                    per_cell, med, args.n_boot, args.boot_seed),
                "loco": S.loco(per_cell, med),
                "per_cell": per_cell,
            }
        out["results"][meth] = block

    # ---- MECHANISM diagnostic: the raw difference distribution ------------
    exp = [r for r in all_rows if r["exposed"]]
    out["mechanism_raw_difference"] = {
        "note": ("retained as a MECHANISM diagnostic only. A large raw "
                 "difference is not evidence that cross-model measurement "
                 "explains the proxy's published failure, because within-cell "
                 "Spearman is invariant to per-network offset and positive "
                 "scaling. The primary endpoint is the concordance change."),
        "matched_minus_published": S.describe(
            [r["d_matched"] - r["d_published"] for r in exp], "raw"),
        "rank_calibrated": S.describe(
            [r["q_matched"] - r["q_published"] for r in exp], "q"),
        "standardised": S.describe(
            [r["z_matched"] - r["z_published"] for r in exp], "z"),
        "episode_spearman_matched_vs_published": S.spearman(
            [r["d_matched"] for r in exp], [r["d_published"] for r in exp]),
    }

    # ---- SEVERITY endpoint, split by dataset ------------------------------
    sev = {}
    for arm in ("d_matched", "d_published", "d_wrong"):
        per = severity_monotonicity(all_rows, arm)
        byds = {}
        for r in per:
            k = r["dataset"]
            byds.setdefault(k, {"n": 0, "strict": 0, "n_sev_points": r["n_severity_points"]})
            byds[k]["n"] += 1
            byds[k]["strict"] += int(r["strictly_increasing"])
        sev[arm] = {"by_dataset": byds, "per_corruption": per}
    out["severity"] = sev

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=float)

    # ---- console summary --------------------------------------------------
    print(f"[sm:analysis] rows={out['n_rows']} exposed={out['n_exposed']}")
    print(f"[sm:analysis] wiring null (seed-0 arms identical): "
          f"{out['wiring_null_seed0_arms_identical']['pass']}")
    for meth, block in out["results"].items():
        for label, b in block.items():
            ci = b.get("bootstrap") or {}
            print(f"[sm:analysis] {meth:9s} {label:34s} "
                  f"median dRho={b['median_delta']:+.4f} "
                  f"[{ci.get('lo', float('nan')):+.4f},{ci.get('hi', float('nan')):+.4f}] "
                  f"over {b['n_cell_seed_pairs']} cell-seed pairs")
    for arm, v in sev.items():
        s = ", ".join(f"{k}: {d['strict']}/{d['n']} ({d['n_sev_points']} sev pts)"
                      for k, d in sorted(v["by_dataset"].items()))
        print(f"[sm:analysis] severity strictly-increasing, {arm:12s}: {s}")
    print(f"[sm:analysis] wrote {args.out}")


if __name__ == "__main__":
    main()
