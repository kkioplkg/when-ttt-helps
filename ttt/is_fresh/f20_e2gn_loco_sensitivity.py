"""F20 -- leave-one-corruption-out sensitivity for the E2 architecture control.

WHAT THIS CHECKS
`f16_e2_gn_analysis.py` reports four headline rank correlations on one common
cell population (CIFAR-10-C, 15 corruptions x severities {1,3,5} = 45 cells):

    entropy @ ResNet-26+GN     (the architecture control, f15 records)
    entropy @ WRN-28-10+BN     (the published negative regime, original E2)
    ttt_rot @ ResNet-26+GN     (positive regime, original E2)
    ttt_mask @ ResNet-26+GN    (positive regime, original E2)

Those numbers come with corruption-clustered bootstrap intervals, which bound
sampling variation across corruptions but do NOT answer the deletion
question: *is any single corruption family driving the sign?*  A
clustered bootstrap can be tight while one influential cluster still carries
the correlation, because the bootstrap keeps that cluster in a large majority
of its resamples.

WHAT THIS SCRIPT DOES
Recomputes the per-cell statistics from the RAW per-episode records --
`results/is_fresh/e2_gn/` for the entropy-on-GN arm and the ORIGINAL
`results/e2/` records for the entropy-on-BN and the two stochastic arms -- under
the unchanged f8/f16 commissioning-to-evaluation cross-fit, and then deletes one
corruption cluster at a time:

    for each of the 15 corruptions c:
        rows_{-c} = the 42 cells whose corruption is not c
        rho_{-c}  = Spearman(phase, gain) over rows_{-c}

repeated at the same five split seeds (20260801--20260805) f16 uses, so each
fold value is a mean over five splits and is directly comparable to the
all-15-corruption headline. Reported per arm: the full-sample rho, and the
min / max / median of the 15 fold values, plus the largest single-fold swing
and whether ANY fold flips the sign of the headline correlation.

Both statistics are run, because the manuscript's architecture-control
paragraph uses both:
    phase_loss = alpha_sgn|alpha_sgn| * delta_proxy / sigma^2  (primary, Table 5)
    phase_feat = alpha_sgn|alpha_sgn| * delta_feat / sigma^2    (secondary)

both built by f8_e2_crossfit.phase_value, including the declared sigma^2 -> 0
rank limit on the zero-gradient-noise (entropy / pseudo-label) arms.

A corruption-clustered bootstrap over the 14 SURVIVING clusters is run inside
each fold (fresh seed 20260817, disjoint from every seed used anywhere else in
this suite) so the fold is reported as an interval and not only as a point.

VERDICT FIELDS
  any_fold_flips_sign        -- the deletion diagnostic proper
  any_fold_ci_contains_zero  -- the weaker "sign no longer resolved" condition
  max_abs_deviation          -- largest |rho_{-c} - rho_full| over the 15 folds

OUTPUT
  f20_e2gn_loco_sensitivity.json
"""
import argparse
import json
import os

import numpy as np

import common as C
import f8_e2_crossfit as F8
import f16_e2_gn_analysis as F16

BOOT_SEED = 20260817          # fresh; not used by any other script in the suite


# ------------------------------------------------------------------ folds

def fold_rho(rows, ykey, drop=None):
    sub = [r for r in rows if drop is None or r["corruption"] != drop]
    return F8.spearman([r["phase"] for r in sub], [r[ykey] for r in sub]), sub


def fold_ci(rows, ykey, drop, n_boot, rng):
    sub = [r for r in rows if r["corruption"] != drop]
    return F8.clustered_bootstrap(sub, ykey, n_boot, rng)


def loco_arm(cells, method, stat_key, seeds, commission, n_boot, how="mean",
             ykey="gain_final"):
    """Leave-one-corruption-out over the 15 clusters for one arm."""
    per_seed_rows = {}
    for s in seeds:
        per_seed_rows[s] = F8.build_rows(
            cells, method, np.random.default_rng(s + 1), commission,
            stat_key, how)
    corrs = sorted({r["corruption"] for r in per_seed_rows[seeds[0]]})
    n_cells = len(per_seed_rows[seeds[0]])

    full_by_seed = [fold_rho(per_seed_rows[s], ykey)[0] for s in seeds]
    full = C.mean_range(full_by_seed)
    # reference interval computed on the SAME rows and the SAME bootstrap
    # stream as the folds, so "fold CI contains zero" can be compared against
    # a like-for-like all-15-cluster interval rather than against f16's
    # five-split-seed average.
    ci_full = F8.clustered_bootstrap(per_seed_rows[seeds[0]], ykey, n_boot,
                                     np.random.default_rng(BOOT_SEED))

    folds = []
    for c in corrs:
        vals, n_kept = [], None
        for s in seeds:
            rho, sub = fold_rho(per_seed_rows[s], ykey, drop=c)
            n_kept = len(sub)
            if rho is not None:
                vals.append(rho)
        mr = C.mean_range(vals)
        ci = fold_ci(per_seed_rows[seeds[0]], ykey, c, n_boot,
                     np.random.default_rng(BOOT_SEED))
        folds.append({"held_out": c, "n_cells_kept": n_kept,
                      "rho": mr,
                      "delta_vs_full": (None if mr is None or full is None
                                        else mr["mean"] - full["mean"]),
                      "ci_clustered_14": ci})

    vals = [f["rho"]["mean"] for f in folds if f["rho"] is not None]
    sign_full = np.sign(full["mean"]) if full else 0.0
    flips = [f["held_out"] for f in folds
             if f["rho"] is not None
             and np.sign(f["rho"]["mean"]) != sign_full]
    zero_ci = [f["held_out"] for f in folds
               if f["ci_clustered_14"]
               and f["ci_clustered_14"]["lo"] <= 0.0 <= f["ci_clustered_14"]["hi"]]
    devs = [abs(f["delta_vs_full"]) for f in folds
            if f["delta_vs_full"] is not None]
    i_min = int(np.argmin(vals)) if vals else None
    i_max = int(np.argmax(vals)) if vals else None
    i_dev = int(np.argmax(devs)) if devs else None
    return {
        "method": method, "statistic": stat_key, "aggregation": how,
        "target": ykey, "n_cells_full": n_cells, "n_clusters": len(corrs),
        "seeds": list(seeds), "commission_share": commission,
        "rho_full": full,
        "ci_full_15_same_stream": ci_full,
        "full_ci_contains_zero": (
            bool(ci_full and ci_full["lo"] <= 0.0 <= ci_full["hi"])),
        "loco_min": {"value": min(vals) if vals else None,
                     "held_out": folds[i_min]["held_out"] if vals else None},
        "loco_max": {"value": max(vals) if vals else None,
                     "held_out": folds[i_max]["held_out"] if vals else None},
        "loco_median": float(np.median(vals)) if vals else None,
        "max_abs_deviation": {
            "value": max(devs) if devs else None,
            "held_out": folds[i_dev]["held_out"] if devs else None},
        "any_fold_flips_sign": bool(flips),
        "folds_flipping_sign": flips,
        "any_fold_ci_contains_zero": bool(zero_ci),
        "folds_whose_ci_contains_zero": zero_ci,
        "folds": folds,
    }


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commission", type=float, default=0.5)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--out-name", default="f20_e2gn_loco_sensitivity.json")
    args = ap.parse_args()

    gn = F16.restrict(F16.load_gn_cells())
    orig = F16.restrict(F8.load_cells())
    print(f"[f20] e2_gn: {len(gn)} cells, "
          f"{sum(len(v) for v in gn.values())} episodes", flush=True)
    print(f"[f20] original E2 matched subset: {len(orig)} cells per method",
          flush=True)

    # (label, cells, method, statistic)
    plan = [
        ("entropy_gn_loss", gn, "tent_gn", "phase_loss"),
        ("entropy_bn_loss", orig, "tent", "phase_loss"),
        ("ttt_rot_loss", orig, "ttt_rot", "phase_loss"),
        ("ttt_mask_loss", orig, "ttt_mask", "phase_loss"),
        ("entropy_gn_feat", gn, "tent_gn", "phase_feat"),
        ("ttt_rot_feat", orig, "ttt_rot", "phase_feat"),
        ("ttt_mask_feat", orig, "ttt_mask", "phase_feat"),
        ("pl_bn_loss", orig, "pl", "phase_loss"),
    ]
    arms = {}
    for label, cells, meth, stat in plan:
        arms[label] = loco_arm(cells, meth, stat, args.seeds,
                               args.commission, args.n_boot)
        a = arms[label]
        print(f"[f20] {label:17s} n={a['n_cells_full']:3d} "
              f"full {a['rho_full']['mean']:+.3f}  "
              f"LOCO min {a['loco_min']['value']:+.3f} "
              f"({a['loco_min']['held_out']})  "
              f"median {a['loco_median']:+.3f}  "
              f"max {a['loco_max']['value']:+.3f} "
              f"({a['loco_max']['held_out']})  "
              f"maxdev {a['max_abs_deviation']['value']:.3f}  "
              f"sign-flip: {a['any_fold_flips_sign']}  "
              f"CI-crosses-0: fold {a['any_fold_ci_contains_zero']} / "
              f"full {a['full_ci_contains_zero']}", flush=True)

    headline = ("entropy_gn_loss", "entropy_bn_loss", "ttt_rot_loss",
                "ttt_mask_loss")
    verdict = {
        "question": ("does deleting any one of the 15 corruption clusters "
                     "change the sign of the four headline E2 "
                     "architecture-control correlations?"),
        "headline_arms": list(headline),
        "any_headline_fold_flips_sign": bool(
            any(arms[k]["any_fold_flips_sign"] for k in headline)),
        "headline_arms_with_a_sign_flip": {
            k: arms[k]["folds_flipping_sign"] for k in headline
            if arms[k]["any_fold_flips_sign"]},
        "any_headline_fold_ci_contains_zero": bool(
            any(arms[k]["any_fold_ci_contains_zero"] for k in headline)),
        "headline_arms_with_a_zero_crossing_ci": {
            k: arms[k]["folds_whose_ci_contains_zero"] for k in headline
            if arms[k]["any_fold_ci_contains_zero"]},
        "headline_arms_whose_FULL_ci_already_contains_zero": [
            k for k in headline if arms[k]["full_ci_contains_zero"]],
        "headline_arms_where_deletion_ALONE_loses_the_sign": [
            k for k in headline
            if arms[k]["any_fold_ci_contains_zero"]
            and not arms[k]["full_ci_contains_zero"]],
        "headline_summary": {
            k: {"full": arms[k]["rho_full"]["mean"],
                "loco_min": arms[k]["loco_min"]["value"],
                "loco_min_held_out": arms[k]["loco_min"]["held_out"],
                "loco_median": arms[k]["loco_median"],
                "loco_max": arms[k]["loco_max"]["value"],
                "loco_max_held_out": arms[k]["loco_max"]["held_out"],
                "max_abs_deviation": arms[k]["max_abs_deviation"]["value"]}
            for k in headline},
        "secondary_feat_arms": {
            k: {"full": arms[k]["rho_full"]["mean"],
                "loco_min": arms[k]["loco_min"]["value"],
                "loco_median": arms[k]["loco_median"],
                "loco_max": arms[k]["loco_max"]["value"],
                "any_fold_flips_sign": arms[k]["any_fold_flips_sign"],
                "folds_flipping_sign": arms[k]["folds_flipping_sign"],
                "any_fold_ci_contains_zero":
                    arms[k]["any_fold_ci_contains_zero"],
                "full_ci_contains_zero": arms[k]["full_ci_contains_zero"],
                "folds_whose_ci_contains_zero":
                    arms[k]["folds_whose_ci_contains_zero"]}
            for k in ("entropy_gn_feat", "ttt_rot_feat", "ttt_mask_feat")},
    }
    C.save({"script": "f20_e2gn_loco_sensitivity.py",
            "answers": ("leave-one-corruption-out deletion diagnostic "
                        "for the E2 architecture control"),
            "inputs": {
                "entropy_gn": C.rel(os.path.join(
                    F16.GN_DIR, "cifar10_tent_main_s20260806.json")),
                "other_arms": "experiments/results/e2/*_main_s{0,1,2}.json",
                "delta_feat": "experiments/results/e5/delta_feat_*.json"},
            "matched_subset": {"dataset": "cifar10",
                               "severities": list(F16.SEVERITIES),
                               "n_cells": 45, "n_clusters": 15},
            "protocol": ("f8/f16 commissioning-to-evaluation cross-fit at five "
                         "split seeds; per fold the held-out corruption's 3 "
                         "cells are removed and Spearman is recomputed on the "
                         "remaining 42; the within-fold interval is a "
                         "corruption-clustered bootstrap over the 14 surviving "
                         "clusters"),
            "bootstrap_seed": BOOT_SEED,
            "arms": arms, "verdict": verdict},
           args.out_name)
    print(f"[f20] verdict: {json.dumps(verdict['headline_summary'], indent=1)}",
          flush=True)
    print(f"[f20] any headline fold flips sign: "
          f"{verdict['any_headline_fold_flips_sign']}", flush=True)
    print("[f20] DONE", flush=True)


if __name__ == "__main__":
    main()
