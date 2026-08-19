"""f39 -- E3 retrospective selector: recompute it from the RELEASED arrays alone.

WHY THIS SCRIPT EXISTS
----------------------
Until this release, the E3 selector's admissibility test could not be rerun by
a reader.  The test compares the per-step *mean replica prediction vectors*
    pi_bar_t  in  R^32,   t = 0, 1, ..., 20,
against bands kappa*(s(u)+s(t)) built from the replica dispersion
sequence s(.), so it consumes BOTH arrays and not the vectors alone.
The vectors were not retained: the records stored only the selected index
t_hat, the dispersion sequence s(.) and the continuation cross-entropies.  Every
aggregate reported *at* the stored t_hat was therefore reconstructible, but
t_hat itself was not.  The supplement said so, and this script is what makes
that sentence obsolete.

`experiments/results/is_fresh/e3_vectors/<tag>_vectors.npz` now carries, per
document, the frozen prediction vector `pred0`, the twenty mean replica
prediction vectors `pi_bar`, the dispersion sequence `s` and the selected index
`t_hat` that the run itself recorded.  This script reads ONLY those arrays --
no GPT-2, no corpora, no GPU, no checkpoint -- reruns the admissibility scan of
`core/alta.py` on them, and asks whether the released arrays reproduce each
run's own selection.

THE LOAD-BEARING NUMBER is `selfcheck`: released arrays vs the same run's own
t_hat.  If that is not exactly 1.0, the release does not make the selector
recomputable, whatever else agrees.  The separate, weaker `vs_retained`
comparison -- against the published RTX 2080 Ti record in
`experiments/results/e4/` -- is cross-hardware agreement, reported with the
signed distance from the decision boundary at every disagreement so that a
near-tie is distinguishable from a divergent trajectory.

Usage:  python f39_e3_vector_selfcheck.py [--out PATH]
"""
import argparse
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VECDIR = os.path.join(REPO, "results", "is_fresh", "e3_vectors")
RETDIR = os.path.join(REPO, "results", "e4")
OUT = os.path.join(REPO, "results", "is_fresh",
                   "f39_e3_vector_selfcheck.json")

# The three constants of the selector, as specified in supplement S7.3.  KAPPA
# is the band multiplier of the admissibility test.  EPS is the floating-point
# tolerance `core/alta.py` adds to the band, reproduced here so the scan is the
# scan and not a lookalike -- the published runs were produced WITH it, so a
# self-check run without it would be checking a different rule.
#
# THE SPECIFICATION NAMES IT TOO.  It once did not: the supplement stated the
# literal non-strict inequality while both implementations added EPS, and a
# reader implementing the printed rule was implementing something the runs had
# not executed.  The supplement now states the tolerance.  It decides nothing
# here -- the two scans agree on all 6,000 released documents, and the smallest
# |band - distance| over every (t, u) pair in the corpus is 3.1e-08, four
# orders of magnitude above EPS -- but "changes no answer" is a fact about
# these arrays, not a licence to leave the two descriptions disagreeing.
KAPPA = 1.5
EPS = 1e-12


def scan_t_hat(P, S, kappa=KAPPA):
    """The admissibility scan of core/alta.py, plus boundary diagnostics.

    Step t is admissible iff for every later step u > t the movement
    ||pi_bar_u - pi_bar_t|| stays inside the replica-noise band
    kappa*(s(u) + s(t)).  t_hat is the SMALLEST admissible step, and T_max if
    none is.  The smallest |signed slack| over all (t, u) is returned as well:
    a near-zero value places the decision arbitrarily close to the boundary,
    which is what lets a mismatch be reported as a measured near-tie rather
    than asserted to be one.  It does not identify the CAUSE of a mismatch;
    that would need the published run's trajectories, which were not kept.
    """
    n = len(P)
    t_hat, decided = n - 1, False
    all_abs, all_norm = [], []
    for i in range(n):
        diffs = np.linalg.norm(P[i + 1:] - P[i], axis=1)
        bands = kappa * (S[i + 1:] + S[i])
        slack = bands + EPS - diffs
        if len(slack):
            all_abs.append(np.abs(slack))
            with np.errstate(divide="ignore", invalid="ignore"):
                all_norm.append(np.abs(slack) / np.where(bands > 0, bands, np.nan))
        if (len(slack) == 0 or np.all(slack >= 0)) and not decided:
            t_hat, decided = i, True
    m_abs = float(np.min(np.concatenate(all_abs))) if all_abs else float("inf")
    na = np.concatenate(all_norm) if all_norm else np.array([np.nan])
    m_norm = float(np.nanmin(na)) if np.any(~np.isnan(na)) else float("nan")
    return t_hat, m_abs, m_norm


def slack_at(P, S, t, kappa=KAPPA):
    """Signed slack of the ONE inequality two disagreeing runs fell across.

    t_hat is the smallest admissible step, so two runs that disagree must
    disagree about the admissibility of the EARLIER of their two answers.
    Evaluating the test there is the sharp diagnostic; evaluating it at the
    later step is uninformative because the later step is usually admissible in
    both runs.
    """
    diffs = np.linalg.norm(P[t + 1:] - P[t], axis=1)
    bands = kappa * (S[t + 1:] + S[t])
    if len(diffs) == 0:
        return float("inf"), float("inf")
    slack = bands + EPS - diffs
    k = int(np.argmin(slack))
    band = bands[k]
    return float(slack[k]), (float(slack[k] / band) if band > 0 else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--vecdir", default=VECDIR)
    ap.add_argument("--retdir", default=RETDIR)
    args = ap.parse_args()

    rep = {"kappa": KAPPA, "eps": EPS, "jobs": [],
           "source": "experiments/results/is_fresh/e3_vectors/*_vectors.npz"}
    n_all = self_ok = ret_ok = 0
    mismatches = []
    worst_norm_slack = 0.0
    min_norm_margin = float("inf")
    ppl_rows = []

    paths = sorted(glob.glob(os.path.join(args.vecdir, "*_vectors.npz")))
    assert paths, f"no released vector files under {args.vecdir}"
    for p in paths:
        tag = os.path.basename(p).replace("_vectors.npz", "")
        z = np.load(p)
        pred0, pi_bar, s, that = z["pred0"], z["pi_bar"], z["s"], z["t_hat"]
        n = len(that)
        # the published record for the same (domain, seed), for the weaker
        # cross-hardware comparison only
        retp = os.path.join(args.retdir, f"{tag}.json")
        ret = json.load(open(retp, encoding="utf-8"))["records"] if \
            os.path.exists(retp) else None
        # this rerun's own per-document record, released beside the arrays
        newp = os.path.join(args.vecdir, f"{tag}.json")
        new = json.load(open(newp, encoding="utf-8"))["records"] if \
            os.path.exists(newp) else None

        c_self = c_ret = 0
        job_mis, mm_abs, mm_norm = [], float("inf"), float("inf")
        for i in range(n):
            P = np.concatenate([pred0[i][None, :], pi_bar[i]], axis=0)
            S = s[i]
            t_re, a, nm = scan_t_hat(P, S)
            mm_abs, mm_norm = min(mm_abs, a), min(mm_norm, nm)
            if t_re == int(that[i]):
                c_self += 1
            else:
                job_mis.append({"doc": int(z["doc"][i]), "kind": "selfcheck",
                                "recomputed": int(t_re),
                                "released_t_hat": int(that[i]),
                                "min_abs_margin": a, "min_norm_margin": nm})
            if ret is not None:
                t_r = int(ret[i]["alta"]["t_hat"])
                if t_re == t_r:
                    c_ret += 1
                else:
                    td = min(int(t_re), t_r)
                    sa, sn = slack_at(P, S, td)
                    worst_norm_slack = max(worst_norm_slack, abs(sn))
                    job_mis.append({"doc": int(z["doc"][i]), "kind": "vs_retained",
                                    "recomputed": int(t_re), "retained": t_r,
                                    "t_disputed": td, "slack_at_disputed_t": sa,
                                    "slack_at_disputed_t_normalised": sn,
                                    "admitted_by_this_run": bool(sa >= 0)})
        n_all += n
        self_ok += c_self
        ret_ok += c_ret
        min_norm_margin = min(min_norm_margin, mm_norm)
        mismatches += [m for m in job_mis if m["kind"] == "vs_retained"]

        row = {"tag": tag, "n_docs": n,
               "selfcheck_matches": c_self, "selfcheck_rate": c_self / n,
               "vs_retained_matches": c_ret, "vs_retained_rate": c_ret / n,
               "min_abs_boundary_margin": mm_abs,
               "min_normalised_boundary_margin": mm_norm,
               "mismatches": job_mis[:40],
               "arrays": {k: {"shape": list(np.shape(z[k])),
                              "dtype": str(np.asarray(z[k]).dtype)}
                          for k in ("pred0", "pi_bar", "s", "t_hat", "doc")}}
        if new is not None and ret is not None:
            ce_new = float(np.mean([r["fixed"]["20"] for r in new]))
            ce_ret = float(np.mean([r["fixed"]["20"] for r in ret]))
            row["ppl20_rerun"] = float(np.exp(ce_new))
            row["ppl20_retained"] = float(np.exp(ce_ret))
            row["ppl20_abs_diff"] = abs(row["ppl20_rerun"] - row["ppl20_retained"])
            row["ppl20_agree_to_4dp"] = bool(
                round(row["ppl20_rerun"], 4) == round(row["ppl20_retained"], 4))
            ppl_rows.append(row["ppl20_agree_to_4dp"])
        rep["jobs"].append(row)
        print(f"{tag}: n={n} selfcheck {c_self}/{n} vs_retained {c_ret}/{n} "
              f"min|norm margin|={mm_norm:.3e}", flush=True)

    rep["totals"] = {
        "n_documents": n_all,
        "selfcheck_matches": self_ok,
        "selfcheck_rate": self_ok / n_all,
        "selfcheck_exact": bool(self_ok == n_all),
        "vs_retained_matches": ret_ok,
        "vs_retained_rate": ret_ok / n_all,
        "n_mismatches_vs_retained": len(mismatches),
        "worst_abs_normalised_slack_at_disputed_step": worst_norm_slack,
        "min_normalised_boundary_margin": min_norm_margin,
        "n_jobs_ppl20_agree_to_4dp": int(sum(ppl_rows)),
        "n_jobs_with_ppl20_comparison": len(ppl_rows),
        "mismatch_directions": {
            "admitted_here_rejected_there":
                int(sum(1 for m in mismatches if m["admitted_by_this_run"])),
            "rejected_here_admitted_there":
                int(sum(1 for m in mismatches if not m["admitted_by_this_run"]))},
    }
    rep["mismatches_vs_retained"] = mismatches
    # The claim the release makes.  Asserted, not merely printed: a release in
    # which the arrays do not rebuild the selector must fail this script rather
    # than emit a quiet number.
    assert rep["totals"]["selfcheck_exact"], (
        "the released arrays do not reproduce every run's own t_hat "
        f"({self_ok}/{n_all}); the selector is NOT recomputable from this "
        "release and the submission must not say that it is")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    t = rep["totals"]
    print()
    print(f"[f39] release-only self-check {t['selfcheck_matches']}/"
          f"{t['n_documents']} ({100*t['selfcheck_rate']:.2f}%) -- EXACT")
    print(f"[f39] vs the retained RTX 2080 Ti record {t['vs_retained_matches']}/"
          f"{t['n_documents']} ({100*t['vs_retained_rate']:.2f}%), "
          f"{t['n_mismatches_vs_retained']} mismatches, worst |normalised "
          f"slack| {t['worst_abs_normalised_slack_at_disputed_step']:.3e}")
    print(f"[f39] fixed-budget ppl@20 agrees to 4 dp on "
          f"{t['n_jobs_ppl20_agree_to_4dp']}/{t['n_jobs_with_ppl20_comparison']}"
          f" jobs")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
