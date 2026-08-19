"""F16 -- correlation analysis for the architecture-controlled entropy run (f15).

WHAT THIS CHECKS
The published E2 comparison changes four things at once between the regime whose
phase-statistic/gain correlation is POSITIVE (ttt_rot / ttt_mask on
ResNet-26+GN) and the regime whose correlation is strongly NEGATIVE (tent / pl
on WRN-28-10+BN): objective, architecture, normalisation layer and source model.
`f15_e2_entropy_gn.py` removed the architecture/normalisation/source part of the
confound by running the ENTROPY objective on ResNet-26+GN under the unchanged
original E2 episodic protocol.  This script measures the correlation over those
records and puts it beside the two references that make it interpretable:

    tent @ ResNet-26+GN   (new, f15)          objective contrast vs ttt_*
    tent @ WRN-28-10+BN   (original E2)       architecture contrast, and the
                                              source of the published negative
                                              correlation
    ttt_rot / ttt_mask @ ResNet-26+GN         the positive regime

Every reference is recomputed here on the SUBSET the new run covers -- CIFAR-10,
15 corruptions, severities {1, 3, 5}, 45 cells -- so no comparison is made
across different cell populations.  The full-grid published values are also
reported for continuity.

PROTOCOL
Identical to f8 / f8b: within each cell a fresh-seed permutation splits the
episodes 50/50 into a COMMISSIONING share (which defines the phase statistic)
and a disjoint EVALUATION share (which defines the realized gain); best step
chosen on commissioning and scored on evaluation; seeds 20260801..20260805,
mean and range; corruption-clustered bootstrap over the 15 corruptions.

STATISTICS
All statistic construction is imported from f8_e2_crossfit.py, including the
SIGNED alignment factor alpha_sgn|alpha_sgn| the manuscript defines and the
declared sigma^2 -> 0 rank limit used on the zero-gradient-noise arms (every
entropy episode, on both architectures, carries sigma2_rel == 0).  The loss
proxy is never recomputed inline here: an inline `alpha**2` drops the
alignment sign, and the sign is the whole content of the statistic.
  phase_loss = alpha_sgn|alpha_sgn| * delta_proxy / sigma^2 -- the statistic
      Figure 4(c) plots for the deterministic objectives; self-contained in the
      episode records, so it is the primary quantity here.
  phase_feat = alpha|alpha| * delta_feat / sigma^2 -- reported as a SECONDARY
      quantity.  For the stochastic arms delta_feat is the published E5
      measurement, made on the very source models those episodes were adapted
      from.  For tent_gn it is `f38_e2gn_deltafeat_fresh.py`'s remeasurement on
      the fresh seed-20260806 model over the fresh episodes' own indices, so
      all 11,520 of them carry a value.
      Until is2-R12 tent_gn instead JOINED the published seed-0 delta_feat by
      (corruption, severity, idx).  That join was across source models AND
      sparse: the fresh run drew its own indices, so only 300 of 11,520
      episodes matched -- 5-9 per cell, about 3 after the commissioning split
      -- while the arm still reported 256 episodes/cell.  `--dfeat-source
      legacy` reproduces it; `statistic_support` in every arm now measures the
      difference, and nothing selects it by default.

OUTPUT
  f16_e2_gn_{tag}_seed{seed}.json   per-seed rows per arm
  f16_e2_gn_summary.json            aggregate + verdict fields
  (with --out-prefix f23_e2_gn, the corrected signed-statistic rerun that is
   the record of record for Table T5 and Figure 4(c))

WHAT `ci_{how}_{tag}_clustered` MEANS
  `lo_mean` / `hi_mean` are the arithmetic MEANS, across the five split
  seeds, of the lower and of the upper endpoint of the five separately
  computed corruption-clustered 95% bootstrap intervals.  They are SPLIT-
  AVERAGED CLUSTERED ENDPOINTS, not the endpoints of one interval with 95%
  coverage for the split-averaged estimator: averaging interval endpoints
  does not in general preserve the nominal coverage of the constituent
  intervals.  The console line, the manuscript (Table T5, Figure 4,
  Appendix C) and `r9_reconcile.py` all use the term "split-averaged
  clustered endpoints"; the phrase "clustered 95% CI" must not be used for
  this pair.  `lo_min` / `hi_max` are the extreme per-split endpoints.
"""
import argparse
import json
import os
import re

import numpy as np

import common as C
import f8_e2_crossfit as F8

GN_DIR = os.path.join(C.RESULTS_DIR, "e2_gn")
SEVERITIES = (1, 3, 5)
EPS_SIGMA = F8.EPS_SIGMA


# ------------------------------------------------------------------ loading

FRESH_DFEAT = os.path.join(
    GN_DIR, "delta_feat_fresh_cifar10_resnet26ttt_s20260806.json")


def load_fresh_dfeat():
    """delta_feat measured by f38 on the FRESH seed-20260806 source model.

    Returns ({(corruption, severity, idx): delta_feat}, provenance) or
    (None, None) when f38 has not been run.  This file lives in the e2_gn
    record directory and NOT in results/e5/, because F8.load_delta_feat()
    merges every results/e5/delta_feat_*.json into one (dataset, arch) map and
    a fresh-model file there would overwrite the published values the
    ttt_rot / ttt_mask arms are built from.
    """
    if not os.path.exists(FRESH_DFEAT):
        return None, None
    with open(FRESH_DFEAT, encoding="utf-8") as f:
        o = json.load(f)
    return ({(r["corruption"], int(r["severity"]), int(r["idx"])):
             float(r["delta_feat"]) for r in o["records"]},
            {"file": C.rel(FRESH_DFEAT), "model_seed": o.get("model_seed"),
             "source": o.get("source")})


def load_gn_cells(dfeat_source="fresh"):
    """Same cell schema as F8.load_cells, for the f15 e2_gn records.

    `dfeat_source` selects where delta_feat comes from:

      "fresh"  -- f38's remeasurement on the fresh seed-20260806 source model
                  over the fresh episode indices.  Every one of the 11,520
                  episodes carries a value, so the feature-proxy arm has the
                  same 256 observations per cell as the loss-proxy arm.  This
                  is the default and the record of record.
      "legacy" -- the cross-source-model join to the ORIGINAL E5 (cifar10,
                  resnet26ttt) file, measured on the published seed-0 model
                  over the PUBLISHED episode indices.  Only 300 of the 11,520
                  fresh episodes match it (5-9 per cell).  Retained so that
                  the superseded analysis stays reproducible and its sparsity
                  stays measurable; never the default.
    """
    if dfeat_source == "fresh":
        dfeat, _ = load_fresh_dfeat()
        if dfeat is None:
            raise SystemExit(
                f"{C.rel(FRESH_DFEAT)} is missing: run "
                "f38_e2gn_deltafeat_fresh.py first, or pass "
                "--dfeat-source legacy to reproduce the superseded "
                "cross-source-model join.")
    elif dfeat_source == "legacy":
        dfeat = F8.load_delta_feat().get(("cifar10", "resnet26ttt"), {})
    else:
        raise ValueError(dfeat_source)
    cells = {}
    for fn in sorted(os.listdir(GN_DIR)):
        if not re.match(r"cifar\d+_.*_main_s\d+\.json$", fn):
            continue
        with open(os.path.join(GN_DIR, fn), encoding="utf-8") as f:
            o = json.load(f)
        argv = o.get("meta", {}).get("argv", {})
        if argv.get("mode", "main") != "main":
            continue
        ds = argv["dataset"]
        for cell in o.get("results", []):
            corr, sev = cell["corruption"], int(cell["severity"])
            key = (ds, "tent_gn", corr, sev)
            for e in cell.get("episodes", []):
                df = (dfeat.get((corr, sev, int(e["idx"])))
                      if e.get("idx") is not None else None)
                rec = F8._episode_stats(e.get("alpha"), e.get("sigma2_rel"),
                                        df, e.get("delta_proxy"))
                rec["frozen_loss"] = e["frozen_loss"]
                rec["steps"] = {int(t): v["loss"]
                                for t, v in e.get("steps", {}).items()}
                cells.setdefault(key, []).append(rec)
    F8.assert_noise_homogeneous(cells)
    return cells


def restrict(cells, dataset="cifar10", severities=SEVERITIES):
    return {k: v for k, v in cells.items()
            if k[0] == dataset and int(k[3]) in severities}


# ------------------------------------------------------------------ analysis

def statistic_support(cells, method, statistic):
    """How many episodes per cell actually CARRY the statistic being ranked.

    `n_episodes_per_cell` counts adaptation episodes in the cell.  When the
    statistic is joined from another record set rather than measured in the
    adaptation loop, those two numbers are not the same: `F8.agg` silently
    drops episodes whose value is None, so a cell can contribute a phase value
    computed from a handful of observations while reporting 256 episodes.
    This function measures the difference, so that the support of every
    correlation is a retained number rather than an inference from the loading
    code.  A table that prints episodes/cell for a joined statistic without
    printing this is overstating its own sample.
    """
    per_cell = [sum(1 for e in eps
                    if e.get(statistic) is not None
                    and np.isfinite(e[statistic]))
                for k, eps in sorted(cells.items()) if k[1] == method]
    if not per_cell:
        return None
    a = np.asarray(per_cell)
    return {"total": int(a.sum()), "per_cell_min": int(a.min()),
            "per_cell_max": int(a.max()), "per_cell_mean": float(a.mean()),
            "per_cell_median": int(np.median(a)), "n_cells": int(a.size),
            "n_cells_empty": int((a == 0).sum())}


def arm(cells, method, statistic, seeds, commission, n_boot, tag,
        out_prefix="f16_e2_gn"):
    """Same-sample + cross-fit Spearman for one (cells, method) arm."""
    same = F8.analyse(cells, method, seeds[0], 1.0, statistic, 0)
    runs = [F8.analyse(cells, method, s, commission, statistic, n_boot)
            for s in seeds]
    for r, s in zip(runs, seeds):
        C.save(r, f"{out_prefix}_{tag}_seed{s}.json")
    supp = statistic_support(cells, method, statistic)
    out = {"method": method, "tag": tag, "statistic": statistic,
           "seeds": seeds, "commission_share": commission,
           "n_cells": runs[0]["n_cells_mean"],
           "n_episodes_per_cell": int(np.median(
               [r["n_episodes"] for r in runs[0]["rows_mean"]])),
           "statistic_support": supp,
           "n_statistic_obs_per_cell": supp["per_cell_median"] if supp else None,
           "same_sample": {k: v for k, v in same.items()
                           if k.startswith("rho_") or k.startswith("n_cells")}}
    for how in ("mean", "median"):
        for t in ("final", "best_crossfit", "best_in_sample"):
            k = f"rho_{how}_{t}"
            out[k] = C.mean_range([r[k] for r in runs])
            cis = [r.get(f"ci_{how}_{t}") for r in runs]
            cis = [c for c in cis if c]
            if cis:
                out[f"ci_{how}_{t}_clustered"] = {
                    "lo_mean": float(np.mean([c["lo"] for c in cis])),
                    "hi_mean": float(np.mean([c["hi"] for c in cis])),
                    "lo_min": float(np.min([c["lo"] for c in cis])),
                    "hi_max": float(np.max([c["hi"] for c in cis])),
                    "n_clusters": cis[0]["n_clusters"],
                    "n_boot": cis[0]["n_boot"]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commission", type=float, default=0.5)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--out-prefix", default="f16_e2_gn")
    ap.add_argument("--dfeat-source", default="fresh",
                    choices=["fresh", "legacy"],
                    help="where the tent_gn feature proxy comes from; see "
                         "load_gn_cells")
    args = ap.parse_args()
    P = args.out_prefix

    gn = restrict(load_gn_cells(args.dfeat_source))
    orig_full = F8.load_cells()
    orig = restrict(orig_full)
    print(f"[f16] e2_gn: {len(gn)} cells, "
          f"{sum(len(v) for v in gn.values())} episodes", flush=True)
    print(f"[f16] original E2 matched subset (cifar10, sev {SEVERITIES}): "
          f"{len(orig)} cells per method", flush=True)

    arms = {}
    # primary statistic: the loss proxy, as in Figure 4(c)
    arms["tent_gn_loss"] = arm(gn, "tent_gn", "phase_loss", args.seeds,
                               args.commission, args.n_boot, "tent_gn_loss", P)
    arms["tent_wrn_loss"] = arm(orig, "tent", "phase_loss", args.seeds,
                                args.commission, args.n_boot, "tent_wrn_loss", P)
    arms["pl_wrn_loss"] = arm(orig, "pl", "phase_loss", args.seeds,
                              args.commission, args.n_boot, "pl_wrn_loss", P)
    # STATISTIC CONTROL: the same loss proxy applied to the stochastic arms on
    # the same cells, so any difference between the arms cannot be a property
    # of which proxy was used.
    for m in ("ttt_rot", "ttt_mask"):
        arms[f"{m}_loss"] = arm(orig, m, "phase_loss", args.seeds,
                                args.commission, args.n_boot, f"{m}_loss", P)
    # secondary: the feature proxy.  For tent_gn this is f38's remeasurement
    # on the fresh source model (--dfeat-source fresh, the default); the
    # stochastic arms keep the published E5 values, which were measured on the
    # SEED-0 source model and are joined to episodes by corruption, severity
    # and index -- NOT one to one with the model each episode was adapted in.
    # Those episodes are pooled over three separately trained source seeds, so
    # 66.7% of the rotation episodes and 58.8% of the masking episodes carry a
    # feature distance from a different network.  This comment said the
    # opposite until the manuscript's disclosure was checked against the
    # records; the seed-resolved measurement cannot be rebuilt here because the
    # per-seed source checkpoints were not retained.
    arms["tent_gn_feat"] = arm(gn, "tent_gn", "phase_feat", args.seeds,
                               args.commission, args.n_boot, "tent_gn_feat", P)
    for m in ("ttt_rot", "ttt_mask"):
        arms[f"{m}_feat"] = arm(orig, m, "phase_feat", args.seeds,
                                args.commission, args.n_boot, f"{m}_feat", P)

    if args.dfeat_source == "fresh":
        _, prov = load_fresh_dfeat()
        dfeat_prov = {
            "tent_gn": dict(prov, kind="fresh remeasurement",
                            note=("delta_feat measured by "
                                  "f38_e2gn_deltafeat_fresh.py on the same "
                                  "seed-20260806 source model the fresh "
                                  "episodes were adapted from, over those "
                                  "episodes' own indices; every episode "
                                  "carries a value")),
            "ttt_rot/ttt_mask": {
                "file": "results/e5/delta_feat_cifar10_resnet26ttt.json",
                "kind": "published measurement",
                "note": ("measured on the SEED-0 source model and joined "
                         "by corruption/severity/index; these episodes are "
                         "pooled over three source-model seeds, so 66.7% of "
                         "the rotation episodes and 58.8% of the masking "
                         "episodes carry a feature distance from a different "
                         "network than the one adapted in them. The "
                         "seed-resolved measurement cannot be rebuilt: the "
                         "per-seed source checkpoints were not retained")}}
    else:
        dfeat_prov = {"tent_gn": {
            "file": "results/e5/delta_feat_cifar10_resnet26ttt.json",
            "kind": "SUPERSEDED cross-source-model join",
            "note": ("published seed-0 delta_feat joined by (corruption, "
                     "severity, idx) to episodes adapted from a fresh "
                     "seed-20260806 model; only 300 of 11,520 fresh episodes "
                     "match, 5-9 per cell")}}

    gnv = arms["tent_gn_loss"]["rho_mean_final"]["mean"]
    wrnv = arms["tent_wrn_loss"]["rho_mean_final"]["mean"]
    ci = arms["tent_gn_loss"]["ci_mean_final_clustered"]
    verdict = {
        "question": ("holding the cell population fixed, how does the "
                     "phase-statistic/gain rank correlation move when the "
                     "ARCHITECTURE changes at fixed objective, and when the "
                     "OBJECTIVE changes at fixed architecture?"),
        "tent_gn_rho_mean_final_crossfit": gnv,
        "tent_wrn_rho_mean_final_crossfit_matched_subset": wrnv,
        "tent_gn_clustered_ci_mean_final": [ci["lo_mean"], ci["hi_mean"]],
        "tent_gn_ci_excludes_zero": bool(ci["lo_mean"] * ci["hi_mean"] > 0),
        "architecture_contrast_same_objective_abs_gap": abs(gnv - wrnv),
        "same_sign_across_architectures": bool(gnv * wrnv > 0),
        "statistic_control_stochastic_same_loss_proxy": {
            m: arms[f"{m}_loss"]["rho_mean_final"]["mean"]
            for m in ("ttt_rot", "ttt_mask")},
        "objective_contrast_same_arch_same_loss_proxy": {
            "tent_gn": gnv,
            "ttt_rot": arms["ttt_rot_loss"]["rho_mean_final"]["mean"],
            "ttt_mask": arms["ttt_mask_loss"]["rho_mean_final"]["mean"]},
        "objective_contrast_same_arch_same_feat_proxy": {
            "tent_gn": arms["tent_gn_feat"]["rho_mean_final"]["mean"],
            "ttt_rot": arms["ttt_rot_feat"]["rho_mean_final"]["mean"],
            "ttt_mask": arms["ttt_mask_feat"]["rho_mean_final"]["mean"]},
    }
    C.save({"script": "f16_e2_gn_analysis.py",
            "input_records": C.rel(os.path.join(
                GN_DIR, "cifar10_tent_main_s20260806.json")),
            "matched_subset": {"dataset": "cifar10",
                               "severities": list(SEVERITIES),
                               "n_cells": len(gn)},
            "protocol": ("commissioning/evaluation cross-fit identical to "
                         "f8_e2_crossfit.py; 5 split seeds; "
                         "corruption-clustered bootstrap"),
            "delta_feat_source": dfeat_prov,
            "arms": arms, "verdict": verdict},
           f"{P}_summary.json")

    for k, v in arms.items():
        r = v["rho_mean_final"]
        c = v.get("ci_mean_final_clustered", {})
        print(f"[f16] {k:16s} n={v['n_cells']:3d} "
              f"same-sample {v['same_sample']['rho_mean_final']:+.3f}  "
              f"cross-fit {r['mean']:+.3f} "
              f"[{r['min']:+.3f}, {r['max']:+.3f}]  "
              f"split-avg clustered endpoints "
              f"[{c.get('lo_mean', float('nan')):+.3f}, "
              f"{c.get('hi_mean', float('nan')):+.3f}]", flush=True)
    print(f"[f16] verdict: {json.dumps(verdict, indent=1)}", flush=True)


if __name__ == "__main__":
    main()
