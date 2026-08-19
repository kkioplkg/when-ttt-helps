#!/usr/bin/env python
"""Derived analysis, written at manuscript-integration time (not on the compute host).

Why this file exists
--------------------
`analyze_p2.py` reports the Jacobian condition number under the *literal*
Loewner reading of Assumption 5.4,

    J J^T  >=  mu_J^2 Pi      (Loewner, on all of R^K),

because that is the reading DESIGN.md froze for the measurement suite, and
because it is the conservative one: it never understates kappa_J.  It also
records the *restricted* constant

    Pi J J^T Pi  >=  mu_J^2 Pi   (Loewner, on range(Pi) only),

per episode, as `mu_J_restricted`, so that the gap between the two readings
can be quantified -- but it does not report the condition number that the
restricted reading implies.

The manuscript states Assumption 5.4 in the form its own proof consumes.  The
proof of Proposition 5.5 (Supplementary Material, Section S4, Step 3
"pullback") uses the assumption only through the compression

    mu_J^2 Pi  <=  Pi J J^T Pi  <=  L_J^2 Pi,

with both gradient vectors lying in range(Pi); the literal Loewner form is
never used anywhere else in the proof.  The restricted form is therefore the
hypothesis the proposition actually needs, and it is the weaker of the two
(the literal form implies it).  Printing the literal kappa_J beside a
restricted-form assumption would be citing a constant the statement does not
define, so this script computes the matching one.

Note on direction: the restricted reading is the reading *most favourable to
Proposition 5.5* -- it yields the smaller kappa_J, hence the larger certified
lower bound.  Reporting it therefore strengthens rather than weakens the
paper's negative finding, and both readings are reported so the gap is visible.

Output: json/KAPPA_RESTRICTED.json

Usage, with the pinned interpreter recorded in
paper/is2/provenance/BUILD_INTERPRETER.md:

    <python> code/analyze_kappa_restricted.py

run from the results directory root, experiments/results/is_fresh/closure.
Needs records/, which is held in the side archive closure_records.zip.
"""

import glob
import gzip
import json
import os
import statistics as st
import sys

STEP = "0"  # t = 0, the step analyze_p2.py reports as the headline

# The certificate funnel is measured at five steps, and the manuscript's
# sentence about the two ranges failing to meet quantifies over ALL of them --
# "anywhere in the suite" -- not over the headline step alone.  Computing the
# separation at t = 0 only and printing it as a suite-wide claim would be a
# scope error of exactly the kind this suite exists to avoid, and it was one:
# the smallest restricted kappa_J at t = 0 is 1.113, while pooled over every
# measured step it is 1.079.  The separation survives either way, but the
# printed number is the pooled one, so the separation block below quantifies
# over every step present in the records rather than over STEP.


def quant(sorted_vals, p):
    """Nearest-rank percentile on an already-sorted list; matches analyze_p2.py."""
    if not sorted_vals:
        return None
    k = max(0, min(len(sorted_vals) - 1, int(round(p / 100.0 * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def summarize(vals):
    s = sorted(vals)
    return {
        "n": len(s),
        "min": s[0],
        "p5": quant(s, 5),
        "p50": st.median(s),
        "p95": quant(s, 95),
        "max": s[-1],
        "mean": sum(s) / len(s),
    }


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    groups = {}
    every = {}          # per objective, pooled over EVERY measured step
    by_step = {}        # per (objective, step), for the stability statement
    steps_seen = set()
    inputs = []
    for path in sorted(glob.glob(os.path.join("records", "p2_*_mom0.jsonl.gz"))):
        base = os.path.basename(path)
        obj = "tent" if "_tent_" in base else "ttt_rot"
        inputs.append(path.replace(os.sep, "/"))
        g = groups.setdefault(
            obj, {"kappa_literal": [], "kappa_restricted": [], "ratio": [], "kappa_crit": []}
        )
        e = every.setdefault(obj, {"kappa_restricted": [], "kappa_crit": []})
        with gzip.open(path, "rt") as fh:
            for line in fh:
                rec = json.loads(line)
                jac = rec.get("jacobian", {})
                for step, j in jac.items():
                    steps_seen.add(int(step))
                    kr = j["L_J"] / j["mu_J_restricted"]
                    e["kappa_restricted"].append(kr)
                    by_step.setdefault((obj, int(step)), []).append(kr)
                    if j.get("kappa_crit") is not None:
                        e["kappa_crit"].append(j["kappa_crit"])
                j = jac.get(STEP)
                if not j:
                    continue
                g["kappa_literal"].append(j["kappa_J"])
                g["kappa_restricted"].append(j["L_J"] / j["mu_J_restricted"])
                g["ratio"].append(j["mu_J_restricted"] / j["mu_J_literal"])
                if j.get("kappa_crit") is not None:
                    g["kappa_crit"].append(j["kappa_crit"])

    out = {
        "step": int(STEP),
        "optimizer": "plain SGD (momentum 0), the recursion Supplement S2 assumes",
        "inputs": inputs,
        "definitions": {
            "kappa_literal": "L_J / mu_J(literal), mu_J(literal)^2 = lambda_min of the "
            "Schur complement of J J^T onto span{grad_z H, p - q}; the reading "
            "DESIGN.md froze for the measurement suite.",
            "kappa_restricted": "L_J / mu_J(restricted), mu_J(restricted)^2 = "
            "lambda_min(Pi J J^T Pi) on range(Pi); the reading the Proposition 5.5 "
            "proof consumes in its pullback step.",
            "kappa_crit": "the largest kappa_J at which the Proposition 5.5 lower "
            "bound would still be positive at this instance; defined only where the "
            "logit-space bracket Z >= 0.",
        },
        "by_objective": {},
    }

    out["steps_measured"] = sorted(steps_seen)
    for obj, g in sorted(groups.items()):
        entry = {k: summarize(v) for k, v in g.items() if v}
        # The decisive comparison: the certificate fires only if kappa_J <=
        # kappa_crit.  Quantified over EVERY measured step, not over STEP,
        # because that is the range the manuscript's sentence quantifies over.
        kr = sorted(every[obj]["kappa_restricted"])
        kc = sorted(every[obj]["kappa_crit"])
        entry["separation"] = {
            "over": "all measured steps",
            "n_kappa_restricted": len(kr),
            "n_kappa_crit": len(kc),
            "min_kappa_restricted": kr[0],
            "max_kappa_crit": kc[-1] if kc else None,
            "disjoint": (kc[-1] < kr[0]) if kc else None,
            "note": "the smallest measured kappa_J under the restricted (most "
            "favourable) reading still exceeds the largest kappa_crit anywhere in "
            "the suite, which is why LB > 0 fires on no instance.",
        }
        out["by_objective"][obj] = entry

    # How far the median moves across the measured steps.  The manuscript
    # prints the medians at the first adapted step and needs a bound on the
    # rest, or a reader cannot tell whether the number is a snapshot of a
    # drifting quantity.  Reported as (max - min) / max over the steps.
    medians_by_step = {}
    moves = {}
    for obj in sorted(groups):
        med = {s: st.median(by_step[(obj, s)])
               for s in sorted(steps_seen) if (obj, s) in by_step}
        medians_by_step[obj] = med
        hi, lo = max(med.values()), min(med.values())
        moves[obj] = (hi - lo) / hi
    out["median_kappa_restricted_by_step"] = medians_by_step
    out["max_relative_median_move_across_steps"] = {
        "by_objective": moves,
        "max": max(moves.values()),
        "definition": "(max - min) / max of the per-step medians, per "
        "objective; the reported figure is the larger of the two.",
    }

    # And pooled over both objectives, which is what "anywhere in the suite"
    # means when the sentence names no objective.
    pooled_kr = sorted(v for e in every.values() for v in e["kappa_restricted"])
    pooled_kc = sorted(v for e in every.values() for v in e["kappa_crit"])
    out["separation_all_steps_both_objectives"] = {
        "over": "all measured steps, both objectives, plain SGD",
        "n_kappa_restricted": len(pooled_kr),
        "n_kappa_crit": len(pooled_kc),
        "min_kappa_restricted": pooled_kr[0],
        "max_kappa_crit": pooled_kc[-1],
        "disjoint": pooled_kc[-1] < pooled_kr[0],
        "note": "this is the pair the manuscript prints. kappa_crit is defined "
        "only where the logit-space bracket Z >= 0, which is why its count is "
        "smaller than the condition number's.",
    }

    dest = os.path.join("json", "KAPPA_RESTRICTED.json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote", dest)
    for obj, e in out["by_objective"].items():
        print(
            "  %-8s kappa_literal p50=%.4f  kappa_restricted p50=%.4f  "
            "min_restricted=%.4f  max_kappa_crit=%.6f  disjoint=%s"
            % (
                obj,
                e["kappa_literal"]["p50"],
                e["kappa_restricted"]["p50"],
                e["separation"]["min_kappa_restricted"],
                e["separation"]["max_kappa_crit"],
                e["separation"]["disjoint"],
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
