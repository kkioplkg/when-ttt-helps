"""Verify a vector-logging E3 rerun against the retained published record.

Checks, per (domain, seed):

  A. document identity   frozen_cont_ce (t=0, no adaptation, no RNG involved)
                         is a pure function of the document and the weights, so
                         a mismatch here means a DIFFERENT DOCUMENT SET, not
                         float noise. This is the sharpest available guard for
                         the two corpora that had to be re-downloaded.
  B. dispersion          s(t) recomputed from the new prediction vectors vs the
                         retained alta.dispersion array (retained at full
                         precision for all 21 steps). This is the direct test
                         that the new vectors are the ones the published
                         selector consumed.
  C. t_hat               recomputed from the new vectors by the same
                         admissibility scan vs the retained alta.t_hat, plus
                         the decision margin at the deciding step so a
                         mismatch can be reported as near-tie or as real.
  D. trajectory          per-replica per-step continuation CE, and the
                         fixed-budget t=20 headline aggregate.

Usage:
  python verify_vectors.py --new-dir DIR --retained-dir DIR [--domains ...]
"""
import argparse
import glob
import json
import os

import numpy as np

KAPPA = 1.5


def recompute_dispersion(tails, pred0):
    """tails (K, steps, 32), pred0 (32,) -> (pi_bar (steps+1,32), s (steps+1,))."""
    K, T, D = tails.shape
    mean = tails.mean(axis=0)                       # (T, D)
    s = np.sqrt(((tails - mean[None]) ** 2).sum(axis=2).mean(axis=0))  # (T,)
    P = np.concatenate([pred0[None, :], mean], axis=0)   # (T+1, D)
    S = np.concatenate([[0.0], s])                       # (T+1,)
    return P, S


def slack_at(P, S, t, kappa=KAPPA):
    """Worst (most negative) admissibility slack at step t in THIS run.

    Because t_hat is the SMALLEST admissible t, two runs that disagree must
    disagree about the admissibility of the EARLIER of their two answers,
    t_disputed = min(t_new, t_retained): one run admitted it, the other did not.
    Evaluating this at t_disputed is therefore the sharp diagnostic -- its
    magnitude is the distance from the decision boundary of the single
    inequality the two runs fell on opposite sides of. Evaluating it at the
    later step instead is uninformative, because the later step is typically
    admissible in both runs.
    """
    diffs = np.linalg.norm(P[t + 1:] - P[t], axis=1)
    bands = kappa * (S[t + 1:] + S[t])
    if len(diffs) == 0:
        return float("inf"), float("inf")
    slack = bands + 1e-12 - diffs
    k = int(np.argmin(slack))
    band = bands[k]
    return float(slack[k]), float(slack[k] / band) if band > 0 else float("nan")


def scan_t_hat(P, S, kappa=KAPPA):
    """Same admissibility scan as core/alta.py, plus boundary-margin diagnostics.

    The admissibility test is a Boolean on the signed slack
        m(t,u) = kappa*(s(u)+s(t)) - ||pi_bar_u - pi_bar_t||,
    admissible at t iff m(t,u) >= 0 for every u > t. A near-zero |m| means the
    decision sits arbitrarily close to the boundary, so the minimum |m| over
    all (t,u) -- absolute and normalised by the band width -- is recorded, and
    a t_hat mismatch can then be reported as a measured near-tie, or as a
    slack too large for that reading. A near-tie is what the number shows; it
    is not evidence that the disagreement AROSE from arithmetic perturbation,
    which these arrays cannot establish either way.
    """
    n = len(P)
    t_hat = n - 1
    margin = None
    all_abs, all_norm = [], []
    for i in range(n):
        diffs = np.linalg.norm(P[i + 1:] - P[i], axis=1)
        bands = kappa * (S[i + 1:] + S[i])
        slack = bands + 1e-12 - diffs
        if len(slack):
            all_abs.append(np.abs(slack))
            with np.errstate(divide="ignore", invalid="ignore"):
                all_norm.append(np.abs(slack) / np.where(bands > 0, bands, np.nan))
        if len(slack) == 0 or np.all(slack >= 0):
            if margin is None:
                t_hat = i
                margin = float(slack.min()) if len(slack) else float("inf")
    m_abs = float(np.min(np.concatenate(all_abs))) if all_abs else float("inf")
    n_all = np.concatenate(all_norm) if all_norm else np.array([np.nan])
    m_norm = float(np.nanmin(n_all)) if np.any(~np.isnan(n_all)) else float("nan")
    return t_hat, margin, m_abs, m_norm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-dir", required=True)
    ap.add_argument("--retained-dir", required=True)
    ap.add_argument("--adapt", default="ln")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    report = {"kappa": KAPPA, "jobs": []}
    for npz_path in sorted(glob.glob(os.path.join(args.new_dir, "*_vectors.npz"))):
        tag = os.path.basename(npz_path).replace("_vectors.npz", "")
        new_json = os.path.join(args.new_dir, f"{tag}.json")
        ret_json = os.path.join(args.retained_dir, f"{tag}.json")
        if not (os.path.exists(new_json) and os.path.exists(ret_json)):
            print(f"[skip] {tag}: missing json")
            continue
        z = np.load(npz_path)
        new = json.load(open(new_json, encoding="utf-8"))
        ret = json.load(open(ret_json, encoding="utf-8"))
        nrec, rrec = new["records"], ret["records"]
        n = min(len(nrec), len(rrec))

        d_frozen, d_disp, d_ce, d_ce20 = [], [], [], []
        d_disp_ret = []
        that_new_vs_ret, that_recomp_vs_new = 0, 0
        mismatch_rows, selfcheck_fail = [], []
        margins_abs, margins_norm = [], []
        for i in range(n):
            a, b = nrec[i], rrec[i]
            d_frozen.append(abs(a["frozen_cont_ce"] - b["frozen_cont_ce"]))
            d_ce.append(np.abs(np.asarray(a["cont_ce"]) -
                               np.asarray(b["cont_ce"])).max())
            d_ce20.append(abs(a["fixed"]["20"] - b["fixed"]["20"]))
            P, S = recompute_dispersion(z["tails"][i], z["pred0"][i])
            d_disp.append(np.abs(S - np.asarray(a["alta"]["dispersion"])).max())
            d_disp_ret.append(np.abs(S - np.asarray(b["alta"]["dispersion"])).max())
            t_re, marg, m_abs, m_norm = scan_t_hat(P, S)
            margins_abs.append(m_abs)
            margins_norm.append(m_norm)
            if t_re == a["alta"]["t_hat"]:
                that_recomp_vs_new += 1
            else:
                selfcheck_fail.append(
                    {"doc": i, "t_hat_recomputed": int(t_re),
                     "t_hat_this_run": int(a["alta"]["t_hat"]),
                     "min_abs_margin": m_abs, "min_norm_margin": m_norm})
            if t_re == b["alta"]["t_hat"]:
                that_new_vs_ret += 1
            else:
                t_ret = int(b["alta"]["t_hat"])
                t_disp = min(int(t_re), t_ret)
                s_at, s_at_n = slack_at(P, S, t_disp)
                mismatch_rows.append({"doc": i, "t_hat_recomputed": int(t_re),
                                      "t_hat_retained": t_ret,
                                      # the step whose admissibility the two
                                      # runs disagree about, and this run's
                                      # signed distance from that boundary
                                      "t_disputed": t_disp,
                                      "slack_at_disputed_t": s_at,
                                      "slack_at_disputed_t_normalised": s_at_n,
                                      "admitted_by_this_run": bool(s_at >= 0),
                                      "deciding_slack_at_new_t": marg,
                                      "min_abs_margin": m_abs,
                                      "min_norm_margin": m_norm})

        job = {
            "tag": tag, "n_docs": n,
            "A_frozen_ce_max_abs": float(np.max(d_frozen)),
            "A_frozen_ce_median_abs": float(np.median(d_frozen)),
            "A_frozen_ce_p95_abs": float(np.percentile(d_frozen, 95)),
            "A_frozen_ce_p99_abs": float(np.percentile(d_frozen, 99)),
            "A_frozen_ce_frac_within_1e4": float(np.mean(np.asarray(d_frozen) < 1e-4)),
            "A_frozen_ce_frac_within_1e3": float(np.mean(np.asarray(d_frozen) < 1e-3)),
            "A_frozen_ce_frac_within_1e2": float(np.mean(np.asarray(d_frozen) < 1e-2)),
            "B_dispersion_vs_own_run_max_abs": float(np.max(d_disp)),
            "B_dispersion_vs_retained_max_abs": float(np.max(d_disp_ret)),
            "B_dispersion_vs_retained_mean_abs": float(np.mean(d_disp_ret)),
            # The release-only self-check: do the RELEASED arrays alone
            # reproduce this run's own selector? If this is not 1.0 the release
            # does not close the finding, whatever the historical agreement is.
            "C_selfcheck_release_reproduces_own_t_hat": that_recomp_vs_new,
            "C_selfcheck_rate": that_recomp_vs_new / n,
            "C_selfcheck_failures": selfcheck_fail[:40],
            "C_t_hat_recomputed_eq_retained": that_new_vs_ret,
            "C_t_hat_match_rate_vs_retained": that_new_vs_ret / n,
            "C_mismatches": mismatch_rows[:40],
            "C_min_abs_boundary_margin": float(np.min(margins_abs)),
            "C_median_min_abs_boundary_margin": float(np.median(margins_abs)),
            "C_min_normalised_boundary_margin": float(np.nanmin(margins_norm)),
            "D_cont_ce_max_abs": float(np.max(d_ce)),
            "D_fixed20_max_abs": float(np.max(d_ce20)),
            "D_fixed20_mean_new": float(np.mean([r["fixed"]["20"] for r in nrec[:n]])),
            "D_fixed20_mean_retained": float(np.mean([r["fixed"]["20"] for r in rrec[:n]])),
            "D_alta_mean_new": float(np.mean([r["alta"]["cont_ce"] for r in nrec[:n]])),
            "D_alta_mean_retained": float(np.mean([r["alta"]["cont_ce"] for r in rrec[:n]])),
        }
        job["D_fixed20_ppl_new"] = float(np.exp(job["D_fixed20_mean_new"]))
        job["D_fixed20_ppl_retained"] = float(np.exp(job["D_fixed20_mean_retained"]))
        report["jobs"].append(job)
        print(f"{tag}: n={n} "
              f"frozenCE_maxabs={job['A_frozen_ce_max_abs']:.3e} "
              f"disp_vs_ret_maxabs={job['B_dispersion_vs_retained_max_abs']:.3e} "
              f"contCE_maxabs={job['D_cont_ce_max_abs']:.3e} "
              f"selfcheck={job['C_selfcheck_rate']:.4f} "
              f"t_hat_match={job['C_t_hat_match_rate_vs_retained']:.4f} "
              f"ppl20 {job['D_fixed20_ppl_new']:.4f} vs {job['D_fixed20_ppl_retained']:.4f}",
              flush=True)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
