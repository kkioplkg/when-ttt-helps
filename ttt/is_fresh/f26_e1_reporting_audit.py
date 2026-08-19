"""F26 -- reporting audit of the headline E1 numbers (the E1 gates in Table T4
and Section 5.1, plus the E4 alignment census).

WHY THIS SCRIPT EXISTS
----------------------
Six of the audited items are E1 numbers whose LABEL and
whose COMPUTATION disagree, or which report a mean of per-seed extrema as if
it were an extremum.  Nothing has to be re-simulated to settle them: the
per-seed f3/f7/f10 JSONs already on disk carry every quantity.  This script
recomputes them from those archived records and writes one JSON that the
manuscript, the T4 generator and the appendix can all be checked against.

ITEMS SETTLED

  (1) T4 row (a) is labelled sup_t |Ehat(t)-E(t)| / E(t) but f7 computes
      max_t |Ehat-E| / max_t E.  Both are reported here, per seed and as
      means, so the label can be matched to whichever statistic is kept.

  (2) T4 row (b) reports 0.979 (0.999 resolved) under the label "held-out
      sign accuracy of alpha^2 delta^2 / sigma^2 vs eta/2", i.e. the FIXED
      theory rule.  Those two values are f10's FITTED-threshold accuracies.
      This script evaluates the fixed rule itself -- predict "adapt" iff
      phase > eta/2, no fitting anywhere -- on the same odd-indexed holdout
      cells, and also on all 625 cells, with and without the 3-SE resolution
      restriction.

  (3) "the worst of the 12,030 (cell, step) comparisons deviates by 3.35
      standard errors": 3.35 is the MEAN over five seeds of the per-seed
      maximum, and 12,030 = 30 cells x 401 steps is the per-seed count.  The
      true maximum over all seeds and the total comparison count are
      computed here.

  (4) "worst cell 0.021" (optimal-stopping relative gap) is likewise a mean
      of per-seed worst cells; the true worst single cell-run is computed.

  (6) "Every miss is a near-boundary cell whose true gain is within
      simulation noise of zero."  The |z| = |gain| / SE(gain) distribution
      over the misses is computed, under both the fitted and the fixed rule,
      so the largest miss can be reported instead of asserted away.

  (7) "Measured alignment is positive throughout (alpha_sgn in [0.24, 0.46])"
      for E4.  That interval is the range of the four PER-DOMAIN MEANS; the
      per-document records contain negative alignments.  The per-document
      census is computed here.

  (9) The blanket "12,000 replicates per cell" for E1.  The replicate count
      actually used by each headline analysis is read back out of the
      records.

INPUTS (archived, read-only)
    results/is_fresh/f7_curve_match_seed*.json
    results/is_fresh/f10_oracle_grid_seed*.json
    results/is_fresh/f3_optimal_stopping_seed*.json
    results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json

OUTPUT
    f26_e1_reporting_audit.json
"""
import argparse
import glob
import json
import os

import numpy as np

import common as C

ETA_OVER_2 = C.ETA / 2.0


def _load(pattern):
    out = []
    for p in sorted(glob.glob(os.path.join(C.RESULTS_DIR, pattern))):
        with open(p, encoding="utf-8") as f:
            out.append((os.path.basename(p), json.load(f)))
    assert out, f"no records matched {pattern}"
    return out


# ---------------------------------------------------------------- items 1, 3

def curve_match_audit():
    recs = _load("f7_curve_match_seed*.json")
    pub, pw, se_max, n_cmp = [], [], [], 0
    for _fn, o in recs:
        pub.append(o["worst_rel_err_published_norm"])
        pw.append(o["worst_rel_err_pointwise"])
        se_max.append(o["worst_err_in_se_units"])
        n_cmp += o["n_cells"] * (o["T"] + 1)
    return {
        "n_seeds": len(recs),
        "n_cells_per_seed": recs[0][1]["n_cells"],
        "n_steps_per_cell": recs[0][1]["T"] + 1,
        "n_comparisons_per_seed": recs[0][1]["n_cells"] * (recs[0][1]["T"] + 1),
        "n_comparisons_all_seeds": n_cmp,
        "n_replicates_per_cell": recs[0][1]["n_rep"],
        "published_normalisation_max_absdiff_over_max_theory": {
            "per_seed": pub, "mean": float(np.mean(pub)),
            "max": float(np.max(pub))},
        "pointwise_sup_t_absdiff_over_theory": {
            "per_seed": pw, "mean": float(np.mean(pw)),
            "max": float(np.max(pw))},
        "max_deviation_in_SE_units": {
            "per_seed": se_max,
            "mean_of_per_seed_maxima": float(np.mean(se_max)),
            "true_max_over_all_seeds": float(np.max(se_max))},
    }


# ------------------------------------------------------------------- item 4

def stopping_audit():
    recs = _load("f3_optimal_stopping_seed*.json")
    worst = [o["max_rel_gap_measured"] for _fn, o in recs]
    return {
        "n_seeds": len(recs),
        "n_cells_per_seed": recs[0][1]["n_cells"],
        "n_replicates_per_cell": recs[0][1]["n_rep"],
        "worst_cell_relative_gap": {
            "per_seed": worst,
            "mean_of_per_seed_worst": float(np.mean(worst)),
            "true_worst_single_cell_run": float(np.max(worst))},
    }


# ---------------------------------------------------------------- items 2, 6

def boundary_audit():
    """Fixed theory rule vs fitted threshold, and the miss distribution."""
    recs = _load("f10_oracle_grid_seed*.json")
    per_seed = []
    for _fn, o in recs:
        ph = np.asarray(o["phase_stat"], float).ravel()
        g1 = np.asarray(o["gain_onestep"], float).ravel()
        se1 = np.asarray(o["gain_onestep_se"], float).ravel()
        lab = (g1 > 0).astype(int)
        z = np.abs(g1) / np.maximum(se1, 1e-30)
        resolved = z > 3.0
        thr_fit = o["fitted_threshold_onestep"]

        hold = np.zeros(len(ph), bool)
        hold[1::2] = True

        def acc(pred, mask):
            m = mask
            return (float((pred[m] == lab[m]).mean()), int(m.sum()))

        pred_fixed = (ph > ETA_OVER_2).astype(int)
        pred_fit = (ph > thr_fit).astype(int)

        a_fix_h, n_fix_h = acc(pred_fixed, hold)
        a_fix_hr, n_fix_hr = acc(pred_fixed, hold & resolved)
        a_fix_a, n_fix_a = acc(pred_fixed, np.ones(len(ph), bool))
        a_fix_ar, n_fix_ar = acc(pred_fixed, resolved)
        a_fit_h, _ = acc(pred_fit, hold)
        a_fit_hr, _ = acc(pred_fit, hold & resolved)

        miss_fixed = (pred_fixed != lab)
        miss_fit_hold = (pred_fit != lab) & hold
        per_seed.append({
            "seed": o["seed"], "n_cells": len(ph),
            "n_replicates_per_cell": o["n_rep"],
            "fitted_threshold_onestep": thr_fit,
            "fixed_rule_holdout_accuracy": a_fix_h,
            "n_holdout": n_fix_h,
            "fixed_rule_holdout_accuracy_resolved3se": a_fix_hr,
            "n_holdout_resolved": n_fix_hr,
            "fixed_rule_all_cells_accuracy": a_fix_a, "n_all": n_fix_a,
            "fixed_rule_all_cells_accuracy_resolved3se": a_fix_ar,
            "n_all_resolved": n_fix_ar,
            "fitted_rule_holdout_accuracy": a_fit_h,
            "fitted_rule_holdout_accuracy_resolved3se": a_fit_hr,
            "n_misses_fixed_all_cells": int(miss_fixed.sum()),
            "max_abs_z_of_a_miss_fixed_all_cells": (
                float(z[miss_fixed].max()) if miss_fixed.any() else None),
            "n_misses_fixed_with_abs_z_gt_3": int((miss_fixed & (z > 3)).sum()),
            "n_misses_fitted_holdout": int(miss_fit_hold.sum()),
            "max_abs_z_of_a_miss_fitted_holdout": (
                float(z[miss_fit_hold].max()) if miss_fit_hold.any() else None),
            "n_misses_fitted_holdout_with_abs_z_gt_3": int(
                (miss_fit_hold & (z > 3)).sum()),
        })

    def agg(key):
        v = [r[key] for r in per_seed if r[key] is not None]
        return {"per_seed": v, "mean": float(np.mean(v)),
                "min": float(np.min(v)), "max": float(np.max(v))} if v else None

    return {
        "n_seeds": len(per_seed),
        "fixed_rule": "predict adapt iff alpha^2 delta^2 / sigma^2 > eta/2",
        "eta_over_2": ETA_OVER_2,
        "fixed_rule_holdout_accuracy": agg("fixed_rule_holdout_accuracy"),
        "fixed_rule_holdout_accuracy_resolved3se": agg(
            "fixed_rule_holdout_accuracy_resolved3se"),
        "fixed_rule_all_cells_accuracy": agg("fixed_rule_all_cells_accuracy"),
        "fixed_rule_all_cells_accuracy_resolved3se": agg(
            "fixed_rule_all_cells_accuracy_resolved3se"),
        "fitted_rule_holdout_accuracy": agg("fitted_rule_holdout_accuracy"),
        "fitted_rule_holdout_accuracy_resolved3se": agg(
            "fitted_rule_holdout_accuracy_resolved3se"),
        "max_abs_z_of_a_miss_fixed_all_cells": agg(
            "max_abs_z_of_a_miss_fixed_all_cells"),
        "max_abs_z_of_a_miss_fitted_holdout": agg(
            "max_abs_z_of_a_miss_fitted_holdout"),
        "n_misses_fixed_with_abs_z_gt_3": agg("n_misses_fixed_with_abs_z_gt_3"),
        "n_misses_fitted_holdout_with_abs_z_gt_3": agg(
            "n_misses_fitted_holdout_with_abs_z_gt_3"),
        "per_seed": per_seed,
    }


# ------------------------------------------------------------------- item 9

def replicate_census():
    """Replicates per cell actually used by each E1 headline analysis."""
    out = {}
    for tag, pat, what in (
            ("f7", "f7_curve_match_seed*.json", "risk-curve identity (T4 a)"),
            ("f10", "f10_oracle_grid_seed*.json",
             "phase boundary / one-step, oracle and selected gains (T4 b)"),
            ("f3", "f3_optimal_stopping_seed*.json",
             "optimal stopping (T4 c)"),
            ("f4", "f4_alta_measured_oracle_seed*.json",
             "ALTA vs measured oracle (T4 d)"),
            ("f5", "f5_batch_variance_seed*.json", "batch scaling (T4 f)"),
            ("f6", "f6_relu_multiseed_seed*.json", "nonconvex ReLU (T4 e)")):
        try:
            recs = _load(pat)
        except AssertionError:
            continue
        o = recs[0][1]
        n = (o.get("n_rep") or o.get("n_rep_per_cell")
             or o.get("n_replicates") or o.get("n_oracle_rep"))
        rec = {"analysis": what, "n_replicates_per_cell": n,
               "n_cells": o.get("n_cells"), "n_seeds": len(recs)}
        if o.get("n_alta_episodes") is not None:
            rec["n_alta_episodes_per_cell"] = o["n_alta_episodes"]
        if o.get("n_rows") is not None:
            rec["n_rows"] = o["n_rows"]
        out[tag] = rec
    return out


# ------------------------------------------------------------------- item 7

E4_DIR = os.path.join(os.path.dirname(C.RESULTS_DIR), "e4")


def e4_alignment_census():
    """Per-DOCUMENT alignment distribution behind the E4 "[0.24, 0.46]" range."""
    per_domain = {}
    for fn in sorted(os.listdir(E4_DIR)):
        if "_ln_s" not in fn or not fn.endswith(".json"):
            continue
        dom = fn.split("_ln_")[0]
        with open(os.path.join(E4_DIR, fn), encoding="utf-8") as f:
            o = json.load(f)
        vals = []

        def walk(x):
            if isinstance(x, dict):
                a = x.get("alpha")
                if isinstance(a, (int, float)):
                    vals.append(float(a))
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)

        walk(o)
        per_domain.setdefault(dom, []).extend(vals)

    out, all_v = {}, []
    for dom, v in sorted(per_domain.items()):
        a = np.asarray(v, float)
        all_v.append(a)
        out[dom] = {"n_records": int(a.size), "mean": float(a.mean()),
                    "min": float(a.min()), "max": float(a.max()),
                    "n_negative": int((a < 0).sum()),
                    "frac_negative": float((a < 0).mean())}
    a = np.concatenate(all_v)
    means = [out[d]["mean"] for d in out]
    return {
        "per_domain": out,
        "range_of_per_domain_means": [float(min(means)), float(max(means))],
        "pooled_n_records": int(a.size),
        "pooled_min": float(a.min()), "pooled_max": float(a.max()),
        "pooled_n_negative": int((a < 0).sum()),
        "pooled_frac_negative": float((a < 0).mean()),
        "note": ("the manuscript's [0.24, 0.46] is the range of the four "
                 "per-domain means; per-document alignments include negative "
                 "values in every domain"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-name", default="f26_e1_reporting_audit.json")
    args = ap.parse_args()

    audit = {
        "script": "f26_e1_reporting_audit.py",
        "answers": ("E1 reporting audit: per-seed worst-cell excess, mean of "
                    "per-seed maxima, holdout and resolved-cell accuracy, and "
                    "the comparison-count census"),
        "inputs": ("archived per-seed results/is_fresh/f{3,7,10}_*_seed*.json; "
                   "nothing is re-simulated"),
        "item1_and_3_curve_match": curve_match_audit(),
        "item4_optimal_stopping": stopping_audit(),
        "item2_and_6_phase_boundary": boundary_audit(),
        "item7_e4_alignment_census": e4_alignment_census(),
        "item9_replicate_census": replicate_census(),
    }
    C.save(audit, args.out_name)

    c = audit["item1_and_3_curve_match"]
    b = audit["item2_and_6_phase_boundary"]
    s = audit["item4_optimal_stopping"]
    print(f"[f26] (1) max|dE|/max E  mean {c['published_normalisation_max_absdiff_over_max_theory']['mean']:.5f}; "
          f"sup_t |dE|/E mean {c['pointwise_sup_t_absdiff_over_theory']['mean']:.5f}")
    print(f"[f26] (3) SE deviation: mean of per-seed maxima "
          f"{c['max_deviation_in_SE_units']['mean_of_per_seed_maxima']:.3f}, "
          f"TRUE max {c['max_deviation_in_SE_units']['true_max_over_all_seeds']:.3f}; "
          f"{c['n_comparisons_per_seed']:,} comparisons per seed, "
          f"{c['n_comparisons_all_seeds']:,} in total")
    print(f"[f26] (4) worst stopping gap: mean of per-seed worst "
          f"{s['worst_cell_relative_gap']['mean_of_per_seed_worst']:.4f}, "
          f"TRUE worst {s['worst_cell_relative_gap']['true_worst_single_cell_run']:.4f}")
    print(f"[f26] (2) FIXED rule holdout {b['fixed_rule_holdout_accuracy']['mean']:.4f} "
          f"({b['fixed_rule_holdout_accuracy']['min']:.4f}-"
          f"{b['fixed_rule_holdout_accuracy']['max']:.4f}), resolved "
          f"{b['fixed_rule_holdout_accuracy_resolved3se']['mean']:.4f}; "
          f"FITTED rule holdout {b['fitted_rule_holdout_accuracy']['mean']:.4f}, "
          f"resolved {b['fitted_rule_holdout_accuracy_resolved3se']['mean']:.4f}")
    print(f"[f26] (2) FIXED rule, all 625 cells "
          f"{b['fixed_rule_all_cells_accuracy']['mean']:.4f}, resolved "
          f"{b['fixed_rule_all_cells_accuracy_resolved3se']['mean']:.4f}")
    print(f"[f26] (6) largest |z| among misses: fixed rule / all cells "
          f"{b['max_abs_z_of_a_miss_fixed_all_cells']['max']:.3f}; "
          f"fitted rule / holdout "
          f"{b['max_abs_z_of_a_miss_fitted_holdout']['max']:.3f}")
    e4 = audit["item7_e4_alignment_census"]
    print(f"[f26] (7) E4 per-domain mean alignment range "
          f"{e4['range_of_per_domain_means'][0]:.3f}-"
          f"{e4['range_of_per_domain_means'][1]:.3f}; per-document range "
          f"{e4['pooled_min']:.3f}-{e4['pooled_max']:.3f}, "
          f"{e4['pooled_n_negative']}/{e4['pooled_n_records']} negative "
          f"({100*e4['pooled_frac_negative']:.2f}%)")
    print(f"[f26] (9) replicate census: "
          f"{ {k: v['n_replicates_per_cell'] for k, v in audit['item9_replicate_census'].items()} }")
    print("[f26] DONE", flush=True)


if __name__ == "__main__":
    main()
