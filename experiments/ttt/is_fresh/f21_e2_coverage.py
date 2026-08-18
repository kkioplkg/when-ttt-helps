"""F21 -- coverage and excluded-group characterisation for the E2 entropy
sign-separation result.

WHY THIS SCRIPT EXISTS
----------------------
The manuscript reports that the sign of the per-episode entropy alignment
alpha_ent separates confidently-right from confidently-wrong episodes
exactly (100% / 0%).  That statement is conditional on a selection: it is
computed on the episodes whose frozen max-softmax confidence clears 0.7.
An exact separation reported without its coverage is unfalsifiable, so the
coverage of that selection is foregrounded here and the excluded episodes are
characterised, which is what lets a reader tell whether the relation is
untestable outside the selected band or merely noisier there.

WHAT IS COMPUTED
  * coverage: how many of the 7,680 pooled episodes clear the threshold;
  * for the retained and excluded groups: frozen accuracy, confidence range,
    the alpha_ent distribution, and the fraction with alpha_ent < 0;
  * the sign rule's agreement with correctness -- P(alpha_ent < 0 | wrong),
    P(alpha_ent < 0 | right), and the accuracy of "predict wrong iff
    alpha_ent < 0" -- on the excluded group and per confidence band, which is
    what decides "graceful degradation" versus "untestable".

DATA
  Re-analysis of the ORIGINAL E2 calibration records, unchanged:
      experiments/results/e2/cifar10_tent_calib_s0.json
      experiments/results/e2/cifar100_tent_calib_s0.json
  pooled over the 15 corruptions of each, temp_scaled=False cells only (the
  same pooling the manuscript and figure F6 use).  No simulation, no random
  numbers, no seeds: this script draws none and adds none.

REPRODUCTION CHECK
  The retained group must reproduce the published counts and fractions
  exactly (n = 2873 confident-right, n = 1554 confident-wrong, frac
  alpha_ent < 0 equal to 0.0 and 1.0 respectively); a mismatch exits
  non-zero.
"""
import json
import os

import numpy as np

import common as C

CONF = 0.7
SRCS = [
    os.path.join(C.RESULTS_DIR, "..", "e2", "cifar10_tent_calib_s0.json"),
    os.path.join(C.RESULTS_DIR, "..", "e2", "cifar100_tent_calib_s0.json"),
]
# Provenance is recorded ARCHIVE-RELATIVE, never as an absolute local path:
# release_archive.zip stores these records under experiments/results/e2/, and
# an absolute build-machine string in a shipped JSON is machine-specific noise
# that a reader cannot resolve.  The invariant is enforced repository-wide by
# the absolute-path gate.
REPO_ROOT = os.path.abspath(os.path.join(C.RESULTS_DIR, "..", "..", ".."))


def rel(path):
    return os.path.relpath(os.path.abspath(path), REPO_ROOT).replace("\\", "/")
BANDS = [(0.0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
         (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.001)]


def load():
    eps = []
    for src in SRCS:
        with open(os.path.abspath(src), encoding="utf-8") as f:
            d = json.load(f)
        for cell in d["results"]["cells"]:
            if cell["temp_scaled"]:
                continue
            for e in cell["episodes"]:
                eps.append((float(e["alpha_ent"]),
                            float(e["confidence"]),
                            int(e["correct"])))
    return eps


def _rank(a):
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), float)
    sa = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sa[j + 1] == sa[i]:
            j += 1
        r[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return r


def spearman(x, y):
    """Spearman rank correlation with average ranks for ties (no scipy)."""
    rx, ry = _rank(x) - _rank(x).mean(), _rank(y) - _rank(y).mean()
    den = (rx ** 2).sum() ** 0.5 * (ry ** 2).sum() ** 0.5
    return float(np.dot(rx, ry) / den) if den > 0 else None


def describe(group):
    a = np.array([g[0] for g in group], float)
    c = np.array([g[1] for g in group], float)
    y = np.array([g[2] for g in group], int)
    wrong, right = y == 0, y == 1
    out = {
        "n": int(len(group)),
        "accuracy": float(y.mean()),
        "confidence_mean": float(c.mean()),
        "confidence_min": float(c.min()),
        "confidence_max": float(c.max()),
        "alpha_mean": float(a.mean()),
        "alpha_median": float(np.median(a)),
        "alpha_q05": float(np.quantile(a, 0.05)),
        "alpha_q95": float(np.quantile(a, 0.95)),
        "alpha_min": float(a.min()),
        "alpha_max": float(a.max()),
        "frac_alpha_negative": float((a < 0).mean()),
        "frac_abs_alpha_below_0.1": float((np.abs(a) < 0.1).mean()),
        "sign_rule_accuracy": float(((a < 0) == (y == 0)).mean()),
    }
    out["P_alpha_neg_given_wrong"] = (
        float((a[wrong] < 0).mean()) if wrong.any() else None)
    out["P_alpha_neg_given_right"] = (
        float((a[right] < 0).mean()) if right.any() else None)
    out["n_wrong"] = int(wrong.sum())
    out["n_right"] = int(right.sum())
    # undefined when the group is all-right or all-wrong (zero variance)
    out["pearson_alpha_correct"] = (
        float(np.corrcoef(a, y)[0, 1]) if y.std() > 0 and a.std() > 0
        else None)
    out["spearman_alpha_correct"] = (
        spearman(a, y) if y.std() > 0 and a.std() > 0 else None)
    return out


def main():
    eps = load()
    retained = [g for g in eps if g[1] >= CONF]
    excluded = [g for g in eps if g[1] < CONF]

    out = {
        "source_records": [rel(s) for s in SRCS],
        "confidence_threshold": CONF,
        "n_episodes_total": len(eps),
        "n_retained": len(retained),
        "n_excluded": len(excluded),
        "coverage": len(retained) / len(eps),
        "excluded_share": len(excluded) / len(eps),
        "retained": describe(retained),
        "excluded": describe(excluded),
        "excluded_correct": describe([g for g in excluded if g[2] == 1]),
        "excluded_wrong": describe([g for g in excluded if g[2] == 0]),
        "all_episodes": describe(eps),
        "by_confidence_band": {},
    }
    for lo, hi in BANDS:
        grp = [g for g in eps if lo <= g[1] < hi]
        if grp:
            out["by_confidence_band"][f"[{lo:.1f},{hi:.1f})"] = describe(grp)

    # ---- reproduction check against the published retained-group numbers
    r = out["retained"]
    assert r["n_right"] == 2873, r["n_right"]
    assert r["n_wrong"] == 1554, r["n_wrong"]
    assert r["P_alpha_neg_given_wrong"] == 1.0, r["P_alpha_neg_given_wrong"]
    assert r["P_alpha_neg_given_right"] == 0.0, r["P_alpha_neg_given_right"]
    assert out["n_episodes_total"] == 7680, out["n_episodes_total"]
    # the manuscript's rho(alpha_ent, correct) = 0.863 is the Spearman
    # correlation over ALL 7,680 episodes, not over the selected subset
    assert abs(out["all_episodes"]["spearman_alpha_correct"] - 0.863) < 5e-4, \
        out["all_episodes"]["spearman_alpha_correct"]
    out["reproduction_check"] = (
        "retained group reproduces n=2873 right / 1554 wrong and the "
        "100%/0% sign fractions quoted in the manuscript; the all-episode "
        "Spearman rho(alpha_ent, correct) reproduces the quoted 0.863")

    C.save(out, "f21_e2_coverage.json")

    e = out["excluded"]
    print(f"[f21] 1/3 coverage: {out['n_retained']}/{out['n_episodes_total']} "
          f"episodes clear confidence {CONF} "
          f"({100*out['coverage']:.1f}%); {out['n_excluded']} "
          f"({100*out['excluded_share']:.1f}%) are excluded.")
    print(f"[f21] 2/3 excluded group: frozen accuracy "
          f"{100*e['accuracy']:.1f}% (retained {100*r['accuracy']:.1f}%), "
          f"confidence in [{e['confidence_min']:.4f}, "
          f"{e['confidence_max']:.4f}], alpha_ent spans "
          f"[{e['alpha_min']:.3f}, {e['alpha_max']:.3f}] with 5-95% "
          f"[{e['alpha_q05']:.3f}, {e['alpha_q95']:.3f}] and only "
          f"{100*e['frac_abs_alpha_below_0.1']:.1f}% of it inside "
          f"|alpha_ent| < 0.1.")
    bands = " ".join(
        f"{k}:{100*v['sign_rule_accuracy']:.1f}%"
        for k, v in out["by_confidence_band"].items())
    print(f"[f21] 3/3 sign relation degrades gracefully: on the excluded "
          f"group P(alpha<0|wrong)={e['P_alpha_neg_given_wrong']:.3f}, "
          f"P(alpha<0|right)={e['P_alpha_neg_given_right']:.3f}, sign-rule "
          f"accuracy {100*e['sign_rule_accuracy']:.1f}% "
          f"(retained {100*r['sign_rule_accuracy']:.1f}%); by band {bands}")
    print("[f21] DONE", flush=True)


if __name__ == "__main__":
    main()
