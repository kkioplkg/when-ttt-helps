"""F31 -- E4 leave-one-domain-out proxy intervals from ONE POOLED 10,000-draw
bootstrap distribution.  Supersedes the interval endpoints of
`f12_e4_proxy_loo.py`; every point estimate, every selection and every
qualitative verdict is unchanged.

WHY THIS SCRIPT EXISTS
----------------------
`f12_e4_proxy_loo.py` runs FIVE independent document-clustered percentile
bootstraps on each held-out domain (`B = 2000`, RNG seeds 20260806..20260810),
takes the 2.5 / 97.5 percentile pair of each stream, and reports the
arithmetic MEAN of the five lower endpoints and the arithmetic mean of the
five upper endpoints:

    "heldout_ci_partial_rho_delta_v2_given_alignment": {
        "lo": float(np.mean([x[0] for x in pv2])),
        "hi": float(np.mean([x[1] for x in pv2]))}

The operation is disclosed in f12's own docstring ("endpoints averaged over
the five bootstrap seeds"), but the resulting pair is described as a
*document bootstrap interval* in `sections/experiments.tex`,
`appendix/experimental_details.tex` and `FRESH_RESULTS.md`.  A mean of five
percentile endpoints is not itself a percentile of any stated distribution,
so those sites name an object the analysis did not compute.  This is exactly
the defect `f29`/`f30` remove from `f11`/`f17`; the same remedy is applied
here rather than the relabelling.

WHAT THIS SCRIPT COMPUTES INSTEAD
---------------------------------
The five streams are POOLED.  Every resample drawn by the five RNG seeds is
concatenated into a single empirical distribution of

    5 streams x B = 2000 draws = 10,000 draws

per quantity, and ONE 2.5 / 97.5 percentile pair is read off it.  The result
is a genuine document-clustered percentile interval at B = 10,000.

The draws are not merely statistically equivalent to f12's -- they are the
SAME DRAWS.  `fold_draws()` below reproduces f12's RNG call sequence exactly
(same `default_rng(seed)`, one `integers(0, n, n)` call per draw, the same
five statistics computed from that one index vector in the same order) and
returns the per-draw statistic vectors instead of collapsing each stream to a
percentile pair.  `max_endpoint_gap_vs_f12_per_stream` asserts that
re-deriving f12's averaged endpoints from these vectors returns f12's
archived numbers to 1e-12.  The only thing that changes between f12 and f31
is therefore the RULE APPLIED TO THE DRAWS.

WHAT MOVES, AND WHAT CANNOT MOVE
--------------------------------
Point estimates are untouched: the per-fold selection (`selected_by_mean_rho`
and `selected_by_mean_rank`), the held-out correlations, the difficulty
baseline, the alignment-only correlation and both partial Spearman
correlations are recomputed here and asserted equal to f12's to 1e-12.  Only
interval endpoints can move, and only by Monte Carlo noise of order
1/sqrt(B); `max_endpoint_shift_vs_f12` records the largest such move and the
build fails if any endpoint moves by more than `--max-shift` (default 0.01).

THE FAVOURABLE-SIDE EXCLUSION COUNT
-----------------------------------
The count this script exists to make honest is

    n_folds_partial_rho_delta_v2_ci_excludes_zero

-- the number of held-out domains whose partial-Spearman interval for
delta_v2 given the alignment factor excludes zero on the favourable
(positive) side.  f12's archived record already reports **1** (PubMed, whose
averaged pair is [+0.001475, +0.183007]); several manuscript sites printed
**0**, which contradicts the record.  This script recomputes the count on the
pooled construction and asserts that the two constructions agree on it, so
the printed census cannot be a hand-typed number again.  The count is
reported for the pooled record and, separately, for the superseded averaged
record, and both are written into the JSON.

DATA (original records only; nothing is re-run, no new experiment)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json
  experiments/results/is_fresh/f12_e4_proxy_loo.json   (audit trail, read
                                                        only, for the
                                                        reproduction checks)

Usage: python f31_e4_proxy_pooled.py
Writes experiments/results/is_fresh/f31_e4_proxy_pooled.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import common as C
import f11_e4_cluster_ci as F11
import f12_e4_proxy_loo as F12

DOMAINS = F12.DOMAINS
BOOT_SEEDS = list(F12.BOOT_SEEDS)          # 20260806..20260810, unchanged
B = F12.B                                  # 2000 per stream, unchanged

# the five bootstrapped quantities, in f12's own naming, mapped to the f12
# record key whose averaged endpoints this script supersedes
QUANTS = {
    "selected": "heldout_ci_selected",
    "phase_v2": "heldout_ci_phase_v2",
    "selected_minus_phase_v2": "heldout_ci_selected_minus_phase_v2",
    "phase_v2_minus_alignment_only":
        "heldout_ci_phase_v2_minus_alignment_only",
    "partial_rho_delta_v2_given_alignment":
        "heldout_ci_partial_rho_delta_v2_given_alignment",
}


def fold_draws(t, v_sel, boot_seed, b=B):
    """One stream's raw draws for one held-out domain, in f12's RNG order.

    This is f12's inner bootstrap loop with the per-stream `_ci()` collapse
    removed.  One `rng.integers(0, n, n)` call per draw, exactly as f12 does,
    so draw i of stream s here is bit-for-bit draw i of stream s there.
    """
    rng = np.random.default_rng(boot_seed)
    n = len(t["gain"])
    vs, vp, vd, vda, vpart = [], [], [], [], []
    for _ in range(b):
        idx = rng.integers(0, n, n)
        a = F11.spearman(t[v_sel][idx], t["gain"][idx])
        b_ = F11.spearman(t["phase_v2"][idx], t["gain"][idx])
        c = F11.spearman(t["alpha_only"][idx], t["gain"][idx])
        p = F12.partial_spearman(t["delta_v2_raw"][idx], t["gain"][idx],
                                 t["alpha_only"][idx])
        if np.isfinite(a):
            vs.append(a)
        if np.isfinite(b_):
            vp.append(b_)
        if np.isfinite(a) and np.isfinite(b_):
            vd.append(a - b_)
        if np.isfinite(b_) and np.isfinite(c):
            vda.append(b_ - c)
        if np.isfinite(p):
            vpart.append(p)
    return {"selected": np.asarray(vs, float),
            "phase_v2": np.asarray(vp, float),
            "selected_minus_phase_v2": np.asarray(vd, float),
            "phase_v2_minus_alignment_only": np.asarray(vda, float),
            "partial_rho_delta_v2_given_alignment": np.asarray(vpart, float)}


def _pct(v):
    """The percentile pair of ONE distribution -- the whole point of f31."""
    x = np.asarray([t for t in v if np.isfinite(t)], float)
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi), int(len(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    ap.add_argument("--max-shift", type=float, default=0.01)
    ap.add_argument("--out-name", default="f31_e4_proxy_pooled.json")
    ap.add_argument("--no-audit", action="store_true",
                    help="skip the f12 cross-checks (reduced verify runs, "
                         "where the draw count differs from the archive)")
    args = ap.parse_args()

    recs = F11.load_e4()
    tabs = {d: F12.doc_table(recs[d]) for d in DOMAINS}

    audit = None
    if not args.no_audit:
        with open(os.path.join(C.RESULTS_DIR, "f12_e4_proxy_loo.json"),
                  encoding="utf-8") as fh:
            audit = json.load(fh)

    # ---- per-domain, per-variant Spearman on seed-averaged documents,
    #      recomputed exactly as f12 does so the fold selection is identical
    rho_tab = {d: {v: F11.spearman(tabs[d][v], tabs[d]["gain"])
                   for v in F12.VARIANTS} for d in DOMAINS}

    out = {
        "script": "f31_e4_proxy_pooled.py",
        "supersedes": "f12_e4_proxy_loo.py (interval endpoints only)",
        "finding": ("f12's held-out "
                    "brackets were the arithmetic mean of five per-stream "
                    "percentile endpoints while the manuscript described them "
                    "as a document bootstrap interval"),
        "correction": ("the five B = 2000 streams are pooled into one "
                       "10,000-draw empirical distribution per quantity and "
                       "one 2.5/97.5 percentile pair is read off it"),
        "kind": "re-analysis of the ORIGINAL E4/E5 records; no new experiment",
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "unit_of_analysis": "document (3 adaptation seeds averaged)",
        "n_bootstrap_per_stream": args.b,
        "bootstrap_seeds": args.boot_seeds,
        "n_pooled_draws": args.b * len(args.boot_seeds),
        "protocol": ("document-clustered percentile bootstrap on the 500 "
                     "seed-averaged documents of the held-out domain; the "
                     "five RNG streams are pooled into one distribution and "
                     "the reported endpoints are genuine percentiles of it, "
                     "with no averaging of endpoints"),
        "folds": {},
    }

    max_point_gap = 0.0        # point estimates vs f12's archive
    max_stream_gap = 0.0       # re-derived f12 endpoints vs f12's archive
    max_shift = 0.0            # pooled endpoints vs f12's averaged ones
    shift_where = None

    for held in DOMAINS:
        train = [d for d in DOMAINS if d != held]
        sel_mean = {v: float(np.nanmean([rho_tab[d][v] for d in train]))
                    for v in F12.VARIANTS}
        ranks = {v: [] for v in F12.VARIANTS}
        for d in train:
            order = sorted(F12.VARIANTS,
                           key=lambda v: -(rho_tab[d][v]
                                           if np.isfinite(rho_tab[d][v])
                                           else -9))
            for k, v in enumerate(order):
                ranks[v].append(k + 1)
        sel_rank = {v: float(np.mean(ranks[v])) for v in F12.VARIANTS}
        v_mean = max(sel_mean, key=lambda v: sel_mean[v])
        v_rank = min(sel_rank, key=lambda v: sel_rank[v])

        t = tabs[held]
        point = {
            "selected_by_mean_rho": v_mean,
            "selected_by_mean_rank": v_rank,
            "heldout_rho_selected": F11.spearman(t[v_mean], t["gain"]),
            "heldout_rho_selected_by_rank": F11.spearman(t[v_rank], t["gain"]),
            "heldout_rho_phase_v2": F11.spearman(t["phase_v2"], t["gain"]),
            "heldout_rho_difficulty_baseline_frozen_ce":
                F11.spearman(t["frozen_ce"], t["gain"]),
            "heldout_rho_alignment_only":
                F11.spearman(t["alpha_only"], t["gain"]),
            "heldout_partial_rho_delta_v2_given_alignment":
                F12.partial_spearman(t["delta_v2_raw"], t["gain"],
                                     t["alpha_only"]),
            "heldout_partial_rho_phase_v2_given_alignment":
                F12.partial_spearman(t["phase_v2"], t["gain"],
                                     t["alpha_only"]),
            "n_heldout_documents": int(len(t["gain"])),
        }

        streams = [fold_draws(t, v_mean, bs, args.b) for bs in args.boot_seeds]

        fold = dict(point)
        fold["train_domains"] = train
        fold["selected_is_delta_v2_family"] = v_mean in F12.V2_FAMILY
        fold["selected_is_papers_exact_proxy"] = v_mean == "phase_v2"

        for quant in QUANTS:
            pool = np.concatenate([s[quant] for s in streams])
            lo, hi, n_used = _pct(pool)
            per_stream = [_pct(s[quant])[:2] for s in streams]
            los = [p[0] for p in per_stream]
            his = [p[1] for p in per_stream]
            fold["pooled_ci_" + quant] = {
                "lo": lo, "hi": hi, "width": float(hi - lo),
                "n_draws": int(len(pool)), "n_draws_finite": n_used,
                # Monte Carlo diagnostics -- NOT the reported interval
                "per_stream_endpoints": [[float(a), float(b)]
                                         for a, b in per_stream],
                "mc_endpoint_range": {
                    "lo": [float(np.min(los)), float(np.max(los))],
                    "hi": [float(np.min(his)), float(np.max(his))]},
                "superseded_mean_of_stream_endpoints": {
                    "lo": float(np.mean(los)), "hi": float(np.mean(his))},
            }

        # ------------------------------------------------------ audit checks
        if audit is not None:
            a = audit["folds"][held]
            for key in ("heldout_rho_selected", "heldout_rho_selected_by_rank",
                        "heldout_rho_phase_v2",
                        "heldout_rho_difficulty_baseline_frozen_ce",
                        "heldout_rho_alignment_only",
                        "heldout_partial_rho_delta_v2_given_alignment",
                        "heldout_partial_rho_phase_v2_given_alignment"):
                max_point_gap = max(max_point_gap, abs(point[key] - a[key]))
            assert point["selected_by_mean_rho"] == a["selected_by_mean_rho"], (
                f"{held}: fold selection moved "
                f"({point['selected_by_mean_rho']} vs "
                f"{a['selected_by_mean_rho']}); f31 must replay f12's folds")
            assert point["selected_by_mean_rank"] == a["selected_by_mean_rank"]
            for quant, akey in QUANTS.items():
                ms = fold["pooled_ci_" + quant][
                    "superseded_mean_of_stream_endpoints"]
                max_stream_gap = max(max_stream_gap,
                                     abs(ms["lo"] - a[akey]["lo"]),
                                     abs(ms["hi"] - a[akey]["hi"]))
                for end in ("lo", "hi"):
                    sh = abs(fold["pooled_ci_" + quant][end] - a[akey][end])
                    if sh > max_shift:
                        max_shift, shift_where = sh, f"{held}.{quant}.{end}"

        out["folds"][held] = fold
        pv = fold["pooled_ci_partial_rho_delta_v2_given_alignment"]
        print(f"[f31] hold out {held:9s}: selected={v_mean:17s} -> held-out "
              f"rho={point['heldout_rho_selected']:+.3f} "
              f"[{fold['pooled_ci_selected']['lo']:+.6f}, "
              f"{fold['pooled_ci_selected']['hi']:+.6f}]; partial rho of "
              f"delta_v2 given alignment "
              f"={point['heldout_partial_rho_delta_v2_given_alignment']:+.6f} "
              f"[{pv['lo']:+.6f}, {pv['hi']:+.6f}]"
              f"{'  EXCLUDES ZERO (+)' if pv['lo'] > 0 else ''}", flush=True)

    # ------------------------------------------------------------- summary
    folds = out["folds"]
    n_v2 = sum(1 for f in folds.values() if f["selected_is_delta_v2_family"])
    n_exact = sum(1 for f in folds.values()
                  if f["selected_is_papers_exact_proxy"])
    ho = [folds[d]["heldout_rho_selected"] for d in DOMAINS]
    ho_paper = [folds[d]["heldout_rho_phase_v2"] for d in DOMAINS]
    ho_base = [folds[d]["heldout_rho_difficulty_baseline_frozen_ce"]
               for d in DOMAINS]
    ho_align = [folds[d]["heldout_rho_alignment_only"] for d in DOMAINS]
    ho_part = [folds[d]["heldout_partial_rho_delta_v2_given_alignment"]
               for d in DOMAINS]

    # THE census this script exists to make honest, on both constructions
    pooled_pos = [d for d in DOMAINS
                  if folds[d]["pooled_ci_partial_rho_delta_v2_given_alignment"]
                  ["lo"] > 0]
    pooled_neg = [d for d in DOMAINS
                  if folds[d]["pooled_ci_partial_rho_delta_v2_given_alignment"]
                  ["hi"] < 0]
    avg_pos = [d for d in DOMAINS
               if folds[d]["pooled_ci_partial_rho_delta_v2_given_alignment"]
               ["superseded_mean_of_stream_endpoints"]["lo"] > 0]
    avg_neg = [d for d in DOMAINS
               if folds[d]["pooled_ci_partial_rho_delta_v2_given_alignment"]
               ["superseded_mean_of_stream_endpoints"]["hi"] < 0]

    assert sorted(pooled_pos) == sorted(avg_pos), (
        f"pooling changed the favourable-side exclusion set: pooled "
        f"{sorted(pooled_pos)} vs endpoint-averaged {sorted(avg_pos)}")
    assert sorted(pooled_neg) == sorted(avg_neg), (
        f"pooling changed the adverse-side exclusion set: pooled "
        f"{sorted(pooled_neg)} vs endpoint-averaged {sorted(avg_neg)}")

    n_part_pos = len(pooled_pos)
    n_part_neg = len(pooled_neg)

    transfer_ok = min(ho_paper) > 0 and min(ho_paper) > max(ho_base)
    incremental_ok = n_part_pos == len(DOMAINS)
    if transfer_ok and n_v2 == len(DOMAINS) and incremental_ok:
        verdict = ("PASS: a delta_v2-family proxy is selected in every fold, "
                   "transfers positively to every untouched domain, and adds "
                   "signal over the alignment term alone")
    elif transfer_ok:
        verdict = (
            "PARTIAL: the frozen proxy transfers to every untouched domain "
            "and beats the document-difficulty baseline in every fold, so the "
            "correlations are NOT a post-selection artefact of the four "
            "domains; but the shift term delta_v2 is not what carries them -- "
            "the alignment/noise factor alpha|alpha|/sigma^2 alone matches or "
            "exceeds the full statistic, and delta_v2 adds NO CONSISTENT "
            "incremental within-domain signal once alignment is held fixed: "
            f"its pooled partial-Spearman interval excludes zero on the "
            f"favourable side in {n_part_pos} of {len(DOMAINS)} folds "
            f"({', '.join(pooled_pos) if pooled_pos else 'none'}) and on the "
            f"ADVERSE side in {n_part_neg} of {len(DOMAINS)} "
            f"({', '.join(pooled_neg) if pooled_neg else 'none'})")
    else:
        verdict = "FAIL: the frozen selection does not transfer; see per-fold detail"

    out["summary"] = {
        "n_folds": len(DOMAINS),
        "n_folds_selecting_delta_v2_family": n_v2,
        "n_folds_selecting_papers_exact_proxy": n_exact,
        "heldout_rho_selected": C.mean_range(ho),
        "heldout_rho_phase_v2": C.mean_range(ho_paper),
        "heldout_rho_difficulty_baseline": C.mean_range(ho_base),
        "heldout_rho_alignment_only": C.mean_range(ho_align),
        "heldout_partial_rho_delta_v2_given_alignment": C.mean_range(ho_part),
        "n_folds_partial_rho_delta_v2_ci_excludes_zero": n_part_pos,
        "folds_partial_rho_delta_v2_ci_excludes_zero_favourable": pooled_pos,
        "n_folds_partial_rho_delta_v2_ci_excludes_zero_adverse": n_part_neg,
        "folds_partial_rho_delta_v2_ci_excludes_zero_adverse": pooled_neg,
        "n_folds_partial_rho_delta_v2_ci_excludes_zero_superseded_averaged":
            len(avg_pos),
        "exclusion_verdicts_unchanged_by_pooling": True,
        "loss_proxy_equals_difficulty_baseline_within_domain": True,
        "verdict": verdict,
    }

    if audit is not None:
        out["audit_vs_f12"] = {
            "max_point_estimate_gap": max_point_gap,
            "max_endpoint_gap_vs_f12_per_stream": max_stream_gap,
            "max_endpoint_shift_vs_f12": max_shift,
            "max_endpoint_shift_location": shift_where,
            "f12_favourable_side_count": audit["summary"][
                "n_folds_partial_rho_delta_v2_ci_excludes_zero"],
            "note": ("per_stream gap ~0 proves f31 replays f12's exact draws; "
                     "shift is therefore attributable to the endpoint rule "
                     "alone"),
        }
        assert max_point_gap <= 1e-12, (
            f"point estimates moved ({max_point_gap:.3e}); pooling must not "
            f"touch them")
        assert max_stream_gap <= 1e-12, (
            f"re-derived per-stream endpoints do not reproduce f12's archived "
            f"means (max gap {max_stream_gap:.3e}); the RNG call sequence is "
            f"not being replayed and the pooled draws are not f12's draws")
        assert max_shift <= args.max_shift, (
            f"a pooled endpoint moved by {max_shift:.5f} at {shift_where}, "
            f"beyond the {args.max_shift} Monte Carlo tolerance; the five "
            f"streams would not be sampling one common bootstrap law")
        assert (audit["summary"]["n_folds_partial_rho_delta_v2_ci_excludes_zero"]
                == n_part_pos), (
            f"the favourable-side count disagrees between constructions: f12 "
            f"{audit['summary']['n_folds_partial_rho_delta_v2_ci_excludes_zero']} "
            f"vs f31 {n_part_pos}")
        print(f"[f31] audit vs f12: points {max_point_gap:.2e}, per-stream "
              f"endpoints {max_stream_gap:.2e}, max pooled-vs-averaged "
              f"endpoint shift {max_shift:.6f} at {shift_where}", flush=True)

    C.save(out, args.out_name)
    print(f"[f31] {verdict}")
    print(f"[f31] partial-rho interval excludes zero on the FAVOURABLE side "
          f"in {n_part_pos}/{len(DOMAINS)} folds "
          f"({', '.join(pooled_pos) if pooled_pos else 'none'}) and on the "
          f"ADVERSE side in {n_part_neg}/{len(DOMAINS)} "
          f"({', '.join(pooled_neg) if pooled_neg else 'none'})")
    print("[f31] DONE", flush=True)


if __name__ == "__main__":
    main()
