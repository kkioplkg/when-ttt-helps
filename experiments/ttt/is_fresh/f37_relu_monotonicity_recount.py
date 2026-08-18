"""F37 -- what "monotone in alpha at 5 of 5 seeds" actually means.

WHY THIS SCRIPT EXISTS
----------------------
Both documents reported that in the off-model ReLU stress test the mean
relative gain is "monotone in alpha at 5 of 5 seeds".  The producing
script f6_relu_multiseed.py sets its per-seed flag with

    mono = all(mean_gain[i+1] >= mean_gain[i] - 0.02 for i in ...)

so the flag is TOLERANCE-monotonicity at 0.02, not monotonicity.  Under
the ordinary mathematical meaning of the word the printed claim is FALSE:
the sequence is nondecreasing at only ONE of the five seeds.

This script recounts both readings from the RETAINED per-seed records --
`f6_relu_multiseed_seed*.json`, the lowest-level retained observation for
this part -- and never from the summary's own `monotone` flags, which are
the object under audit.  It reports what each reading gives, the largest
adjacent reversal, and the tolerance at which each count changes, so the
replacement sentence can be written from a measurement rather than from a
recollection.

WHAT IS CHECKED
  A. THE RECORDS AGREE WITH THE SUMMARY on the per-seed mean relative gain
     by alpha, to floating point.  Everything below is computed from the
     per-seed records; the summary is used only to confirm they are the
     same numbers, so a defect in the summary cannot hide inside the
     recount.
  B. EXACT MONOTONICITY, per seed: whether g(alpha_{i+1}) >= g(alpha_i)
     at every adjacent pair, with the worst adjacent difference.
  C. TOLERANCE MONOTONICITY at the code's own 0.02, per seed, and the
     reproduction of the printed "5 of 5".
  D. THE LARGEST ADJACENT REVERSAL over all seeds and pairs, which is the
     number the replacement sentence should carry, together with the seed
     and the alpha pair that realize it.
  E. THE TOLERANCE PROFILE: for a ladder of tolerances, how many seeds
     pass.  This locates 0.02 relative to the data -- it is roughly three
     orders of magnitude larger than the largest reversal, which is why
     the flag is uninformative about monotonicity and informative about
     the absence of a LARGE reversal.
  F. WHAT SURVIVES, stated as a measurement: the ordering is preserved at
     every seed to within the largest observed reversal, and the
     alpha = 1 versus alpha = 0 margin -- the part of the stress test that
     carries the scientific reading -- is recomputed and is positive at
     every seed by a margin many orders of magnitude larger than any
     reversal.

No random numbers are drawn and no experiment is rerun: this is a recount
of retained records.

Usage: python f37_relu_monotonicity_recount.py
Writes experiments/results/is_fresh/f37_relu_monotonicity_recount.json
"""
from __future__ import annotations

import json
import os

import numpy as np

import common as C

SEEDS = [20260801, 20260802, 20260803, 20260804, 20260805]
ALPHAS = ["0.0", "0.25", "0.5", "0.75", "1.0"]
CODE_TOLERANCE = 0.02


def load(name):
    with open(os.path.join(C.RESULTS_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    per_seed_records = {s: load(f"f6_relu_multiseed_seed{s}.json")
                        for s in SEEDS}
    summary = load("f6_relu_multiseed_summary.json")

    # ---------------- A. the records agree with the summary
    worst_gap = 0.0
    for i, s in enumerate(SEEDS):
        for a in ALPHAS:
            fr = per_seed_records[s]["mean_relgain_by_alpha"][a]
            fs = summary["mean_relgain_by_alpha"][a]["values"][i]
            worst_gap = max(worst_gap, abs(fr - fs))
    agreement = {
        "claim": ("the per-seed records and the summary carry the same mean "
                  "relative gains, so recounting from the records audits the "
                  "summary rather than assuming it"),
        "n_values_compared": len(SEEDS) * len(ALPHAS),
        "largest_absolute_difference": worst_gap,
        "summary_seed_order_matches_record_seeds": bool(
            summary["seeds"] == SEEDS),
    }

    # ---------------- B/C/D. the two readings, per seed
    rows = []
    reversals = []
    for s in SEEDS:
        g = [per_seed_records[s]["mean_relgain_by_alpha"][a] for a in ALPHAS]
        diffs = [g[i + 1] - g[i] for i in range(len(g) - 1)]
        worst = min(diffs)
        worst_i = int(np.argmin(diffs))
        rows.append({
            "seed": s,
            "mean_relgain_by_alpha": {a: g[i] for i, a in enumerate(ALPHAS)},
            "adjacent_differences": diffs,
            "exactly_nondecreasing": bool(worst >= 0.0),
            "nondecreasing_to_tolerance_0p02": bool(
                worst >= -CODE_TOLERANCE),
            "worst_adjacent_difference": worst,
            "worst_adjacent_pair": [ALPHAS[worst_i], ALPHAS[worst_i + 1]],
            "flag_recorded_in_the_record": bool(
                per_seed_records[s]["monotone"]),
        })
        if worst < 0.0:
            reversals.append((-worst, s, ALPHAS[worst_i], ALPHAS[worst_i + 1]))

    n_exact = sum(1 for r in rows if r["exactly_nondecreasing"])
    n_tol = sum(1 for r in rows if r["nondecreasing_to_tolerance_0p02"])
    n_flag = sum(1 for r in rows if r["flag_recorded_in_the_record"])
    reversals.sort(reverse=True)
    largest = reversals[0] if reversals else (0.0, None, None, None)

    counts = {
        "printed_claim": "monotone in alpha at 5 of 5 seeds",
        "n_seeds_exactly_nondecreasing": n_exact,
        "n_seeds_nondecreasing_to_the_code_tolerance_0p02": n_tol,
        "n_seeds_whose_recorded_flag_is_true": n_flag,
        "code_criterion": ("f6_relu_multiseed.py sets monotone := all("
                           "g[i+1] >= g[i] - 0.02), i.e. NO DECREASE LARGER "
                           "THAN 0.02 -- not monotonicity"),
        "largest_adjacent_reversal": largest[0],
        "largest_adjacent_reversal_seed": largest[1],
        "largest_adjacent_reversal_alpha_pair": [largest[2], largest[3]],
        "n_seeds_with_at_least_one_reversal": len(reversals),
    }

    # ---------------- E. the tolerance profile
    ladder = [0.0, 1e-6, 1e-5, 2e-5, 3.5e-5, 1e-4, 1e-3, 1e-2, 2e-2]
    profile = []
    for tol in ladder:
        profile.append({
            "tolerance": tol,
            "n_seeds_passing": int(sum(
                1 for r in rows if r["worst_adjacent_difference"] >= -tol)),
        })
    tolerance_profile = {
        "ladder": profile,
        "ratio_code_tolerance_to_largest_reversal": (
            float(CODE_TOLERANCE / largest[0]) if largest[0] > 0 else None),
        "reading": ("0.02 is far above every observed reversal, so the flag "
                    "certifies the ABSENCE OF A LARGE REVERSAL and says "
                    "nothing about monotonicity"),
    }

    # ---------------- F. what survives
    margins = []
    for s in SEEDS:
        g = per_seed_records[s]["mean_relgain_by_alpha"]
        margins.append(g["1.0"] - g["0.0"])
    survives = {
        "claim": ("the alpha=1 versus alpha=0 margin is the part of the "
                  "stress test that carries the scientific reading, and it "
                  "is unaffected"),
        "per_seed_margin_alpha1_minus_alpha0": margins,
        "n_seeds_with_positive_margin": int(sum(1 for m in margins if m > 0)),
        "min_margin": float(min(margins)),
        "mean_margin": float(np.mean(margins)),
        "ratio_min_margin_to_largest_reversal": (
            float(min(margins) / largest[0]) if largest[0] > 0 else None),
        "replacement_sentence": (
            "relative gain nondecreasing in alpha to the code-defined "
            "tolerance 0.02 at 5 of 5 seeds; exactly nondecreasing at 1 of 5, "
            f"with the largest adjacent reversal {largest[0]:.2e}"),
    }

    out = {
        "script": "f37_relu_monotonicity_recount.py",
        "kind": ("recount from retained per-seed records; nothing simulated, "
                 "no random numbers drawn"),
        "sources": [f"f6_relu_multiseed_seed{s}.json" for s in SEEDS]
                   + ["f6_relu_multiseed_summary.json (agreement check only)"],
        "finding": ("'monotone in alpha at 5 of 5 seeds' is false under the "
                    "ordinary meaning of monotone: the sequence is exactly "
                    "nondecreasing at 1 of 5 seeds.  The producing script's "
                    "flag is tolerance-monotonicity at 0.02, which 5 of 5 "
                    "seeds satisfy.  The largest adjacent reversal is "
                    f"{largest[0]:.3e}, at seed {largest[1]}"),
        "A_records_agree_with_the_summary": agreement,
        "B_C_D_per_seed": rows,
        "counts": counts,
        "E_tolerance_profile": tolerance_profile,
        "F_what_survives": survives,
    }

    # ---------------- assertions
    assert agreement["summary_seed_order_matches_record_seeds"], (
        "the summary's seed order does not match the records, so the "
        "value-by-value comparison would be comparing different seeds")
    assert agreement["largest_absolute_difference"] == 0.0, (
        "the per-seed records and the summary disagree on a mean relative "
        "gain -- the recount would then be auditing a different object")
    assert n_flag == len(SEEDS) and n_tol == len(SEEDS), (
        "the recorded flags do not reproduce as tolerance-monotonicity at "
        "0.02, so the diagnosis of what the flag means would be wrong")
    assert n_exact < len(SEEDS), (
        "the sequences ARE exactly nondecreasing at every seed -- if this "
        "fires the printed claim is true and nothing needs repairing")
    assert largest[0] > 0.0, "no reversal found, contradicting n_exact < 5"
    assert largest[0] < CODE_TOLERANCE, (
        "a reversal exceeds the code tolerance, which would make the "
        "recorded flags themselves wrong")
    assert survives["n_seeds_with_positive_margin"] == len(SEEDS), (
        "the alpha=1 vs alpha=0 margin is not positive at every seed, so "
        "the surviving reading would be wrong too")

    C.save(out, "f37_relu_monotonicity_recount.json")

    print(f"[f37] 1/3 the per-seed records and the summary agree exactly on "
          f"all {agreement['n_values_compared']} mean relative gains "
          f"(largest difference {agreement['largest_absolute_difference']:.1e}), "
          f"so the recount audits the summary instead of assuming it.")
    print(f"[f37] 2/3 'MONOTONE AT 5 OF 5' IS FALSE: exactly nondecreasing at "
          f"{n_exact} of {len(SEEDS)} seeds.  The producing script's flag is "
          f"g[i+1] >= g[i] - 0.02, satisfied at {n_tol} of {len(SEEDS)}.  "
          f"Largest adjacent reversal {largest[0]:.3e}, at seed {largest[1]} "
          f"between alpha={largest[2]} and alpha={largest[3]}; "
          f"{counts['n_seeds_with_at_least_one_reversal']} of {len(SEEDS)} "
          f"seeds have at least one reversal.  The code tolerance is "
          f"{tolerance_profile['ratio_code_tolerance_to_largest_reversal']:.0f}x "
          f"the largest reversal.")
    print(f"[f37] 3/3 WHAT SURVIVES: the alpha=1 minus alpha=0 margin is "
          f"positive at {survives['n_seeds_with_positive_margin']} of "
          f"{len(SEEDS)} seeds, smallest {survives['min_margin']:.4g} -- "
          f"{survives['ratio_min_margin_to_largest_reversal']:.0f}x the "
          f"largest reversal.  Replacement sentence: "
          f"\"{survives['replacement_sentence']}\".")
    print("[f37] DONE", flush=True)


if __name__ == "__main__":
    main()
