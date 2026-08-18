"""F29 -- E4 document-clustered percentile intervals from ONE POOLED
10,000-draw bootstrap distribution.  Supersedes the interval endpoints of
`f11_e4_cluster_ci.py`; every point estimate is unchanged.

WHY THIS SCRIPT EXISTS
----------------------
`f11_e4_cluster_ci.py` runs FIVE independent document-clustered bootstraps
(`B = 2000`, RNG seeds 20260806..20260810), takes the 2.5 / 97.5 percentile
pair of each, and reports the arithmetic MEAN of the five lower endpoints and
the arithmetic mean of the five upper endpoints:

    los = [p[kind][which][0] for p in per_boot]      # five lower endpoints
    his = [p[kind][which][1] for p in per_boot]      # five upper endpoints
    return {"lo": mean(los), "hi": mean(his), ...}

Appendix C of the manuscript discloses this correctly ("endpoints averaged
over five bootstrap seeds").  Several other sites did not: they described the
E4 brackets as a single document-clustered percentile interval with no
endpoint averaging.  A mean of five percentile endpoints is not itself a
percentile of any distribution, so those sites named an object the analysis
did not compute.

This is a strictly milder defect than the E2 one it superficially resembles.
E2's `lo_mean`/`hi_mean` average across five distinct DATA splits and
therefore mix five different estimands; the E2 pairs are consequently called
*split-averaged clustered endpoints* and are NOT called intervals anywhere.
The five E4 streams differ only in the bootstrap RNG: they are five Monte
Carlo estimates of the SAME bootstrap-law endpoint, so averaging them is a
variance-reduction device for one common target rather than a blend of
estimands.  That is why the correction below is available at all.

WHAT THIS SCRIPT COMPUTES INSTEAD
---------------------------------
The five streams are POOLED.  Every resample drawn by the five RNG seeds is
concatenated into a single empirical distribution of

    5 streams x B = 2000 draws = 10,000 draws

per quantity, and ONE 2.5 / 97.5 percentile pair is read off it.  The result
is a genuine document-clustered percentile interval at B = 10,000, so the
name the documents use is the name of the object that is computed.

The draws are not merely statistically equivalent to f11's -- they are the
SAME DRAWS.  `bootstrap_draws()` below reproduces f11's RNG call sequence
exactly (same `default_rng(seed)`, same three constructions in the same
order, same number of `integers()` calls with the same shapes), and returns
the per-draw statistic vectors instead of collapsing each stream to a
percentile pair.  The reproduction check `max_endpoint_gap_vs_f11_per_stream`
asserts that re-deriving f11's averaged endpoints from these vectors returns
f11's archived numbers to 1e-12.  The only thing that changes between f11 and
f29 is therefore the RULE APPLIED TO THE DRAWS -- mean-of-five-percentiles
versus one-percentile-of-the-pool -- and nothing about the data, the
estimand, the estimator or the resampling scheme.

WHAT MOVES, AND WHAT CANNOT MOVE
--------------------------------
Point estimates are untouched: `rho_pooled_rows`, `rho_seed_averaged`,
`rho_by_seed`, `ppl_improvement_pooled` and the variance decomposition are
recomputed here and asserted equal to f11's to 1e-12.  Only interval
endpoints and the widths and design effects derived from them can move, and
only by Monte Carlo noise of order 1/sqrt(B).  `max_endpoint_shift_vs_f11`
records the largest such move over every reported endpoint; the assertion
below fails the build if any endpoint moves by more than `--max-shift`
(default 0.01), because a larger move would mean the five streams were not
sampling one common law and pooling would be the wrong operation.

The per-stream endpoints are retained under `per_stream_endpoints` and the
across-stream spread under `mc_endpoint_range`, demoted from "the reported
interval" to what they always were: a Monte Carlo diagnostic showing that no
endpoint depends on one RNG draw.

DATA (original records only; nothing is re-run, no new experiment)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json
  experiments/results/is_fresh/f11_e4_cluster_ci.json   (audit trail, read
                                                         only, for the
                                                         reproduction checks)

Usage: python f29_e4_pooled_ci.py
Writes experiments/results/is_fresh/f29_e4_pooled_ci.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import common as C
import f11_e4_cluster_ci as F11

DOMAINS = F11.DOMAINS
BOOT_SEEDS = list(F11.BOOT_SEEDS)          # 20260806..20260810, unchanged
B = F11.B                                  # 2000 per stream, unchanged
KINDS = ("naive_iid_rows", "cluster_nested", "cluster_seedavg")
QUANTS = ("rho", "impr")


def bootstrap_draws(dom_recs, boot_seed, b=B):
    """One stream's raw draws, in f11's exact RNG call order.

    Returns {kind: {"rho": ndarray(b), "impr": ndarray(b)}}.  This is
    `f11.bootstrap_domain` with the final `_ci()` collapse removed; the three
    constructions are generated in the same order from the same `Generator`,
    so draw i of stream s here is bit-for-bit draw i of stream s there.
    """
    rng = np.random.default_rng(boot_seed)
    docs = sorted(dom_recs)
    rows = F11._flatten(dom_recs, docs)
    n_rows, n_docs = len(rows), len(docs)
    avg = F11._seedavg(dom_recs, docs)

    ph_rows = np.array([r["phase_v2"] for r in rows])
    gn_rows = np.array([r["gain"] for r in rows])
    fz_rows = np.array([r["frozen_ce"] for r in rows])
    al_rows = np.array([r["alta_ce"] for r in rows])

    by_doc = {}
    for i, r in enumerate(rows):
        by_doc.setdefault(r["doc"], []).append(i)
    doc_blocks = [np.asarray(by_doc[d], int) for d in docs]

    ph_avg = np.array([r["phase_v2"] for r in avg])
    gn_avg = np.array([r["gain"] for r in avg])
    fz_avg = np.array([r["frozen_ce"] for r in avg])
    al_avg = np.array([r["alta_ce"] for r in avg])

    out = {}

    # (1) published construction: i.i.d. over the pooled rows
    rho_v, imp_v = [], []
    for _ in range(b):
        idx = rng.integers(0, n_rows, n_rows)
        rho_v.append(F11.spearman(ph_rows[idx], gn_rows[idx]))
        imp_v.append(F11.ppl_improvement(fz_rows[idx], al_rows[idx]))
    out["naive_iid_rows"] = {"rho": np.asarray(rho_v, float),
                             "impr": np.asarray(imp_v, float),
                             "n_units": n_rows}

    # (2) clustered, seeds nested inside the resampled document
    rho_v, imp_v = [], []
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        idx = np.concatenate([doc_blocks[k] for k in pick])
        rho_v.append(F11.spearman(ph_rows[idx], gn_rows[idx]))
        imp_v.append(F11.ppl_improvement(fz_rows[idx], al_rows[idx]))
    out["cluster_nested"] = {"rho": np.asarray(rho_v, float),
                             "impr": np.asarray(imp_v, float),
                             "n_units": n_docs}

    # (3) clustered, seeds averaged within document
    rho_v, imp_v = [], []
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        rho_v.append(F11.spearman(ph_avg[pick], gn_avg[pick]))
        imp_v.append(F11.ppl_improvement(fz_avg[pick], al_avg[pick]))
    out["cluster_seedavg"] = {"rho": np.asarray(rho_v, float),
                              "impr": np.asarray(imp_v, float),
                              "n_units": n_docs}
    return out


def _pct(v):
    """The percentile pair of ONE distribution -- the whole point of f29."""
    x = np.asarray([t for t in v if np.isfinite(t)], float)
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi), int(len(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    ap.add_argument("--max-shift", type=float, default=0.01)
    # a reduced verify run must not clobber the archived record that
    # fig_f8_domains.py, Section 5.4 and r9_reconcile.py read.
    ap.add_argument("--out-name", default="f29_e4_pooled_ci.json")
    ap.add_argument("--no-audit", action="store_true",
                    help="skip the f11 cross-checks (reduced verify runs, "
                         "where the draw count differs from the archive)")
    args = ap.parse_args()

    recs = F11.load_e4()
    assert set(recs) >= set(DOMAINS), f"missing domains: {set(DOMAINS)-set(recs)}"

    audit = None
    if not args.no_audit:
        with open(os.path.join(C.RESULTS_DIR, "f11_e4_cluster_ci.json"),
                  encoding="utf-8") as fh:
            audit = json.load(fh)

    out = {
        "script": "f29_e4_pooled_ci.py",
        "supersedes": "f11_e4_cluster_ci.py (interval endpoints only)",
        "finding": ("the E4 brackets "
                    "were the arithmetic mean of five per-stream percentile "
                    "endpoints while several sites described them as a single "
                    "document-clustered percentile interval"),
        "correction": ("the five B = 2000 streams are pooled into one "
                       "10,000-draw empirical distribution per quantity and "
                       "one 2.5/97.5 percentile pair is read off it"),
        "kind": "re-analysis of the ORIGINAL E4/E5 records; no new experiment",
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "statistic": ("spearman(alpha|alpha| delta_v2 / sigma2_rel, "
                      "frozen_cont_ce - alta_cont_ce)"),
        "n_bootstrap_per_stream": args.b,
        "bootstrap_seeds": args.boot_seeds,
        "n_pooled_draws": args.b * len(args.boot_seeds),
        "protocol": ("document-clustered percentile bootstrap, 500 document "
                     "clusters with the three adaptation seeds nested; the "
                     "five RNG streams are pooled into one distribution and "
                     "the reported endpoints are genuine percentiles of it, "
                     "with no averaging of endpoints"),
        "published_intervals_checked_against": F11.PUBLISHED_RHO_CI,
        "domains": {},
    }

    max_repro_gap = 0.0            # naive construction vs the published CI
    max_stream_gap = 0.0           # re-derived f11 endpoints vs f11's archive
    max_point_gap = 0.0            # point estimates vs f11's archive
    max_shift = 0.0                # pooled endpoints vs f11's averaged ones
    shift_where = None

    for dom in DOMAINS:
        dr = recs[dom]
        docs = sorted(dr)
        rows = F11._flatten(dr, docs)
        seeds = sorted({r["seed"] for r in rows})
        ph = np.array([r["phase_v2"] for r in rows])
        gn = np.array([r["gain"] for r in rows])
        fz = np.array([r["frozen_ce"] for r in rows])
        al = np.array([r["alta_ce"] for r in rows])
        avg = F11._seedavg(dr, docs)

        rho_pooled = F11.spearman(ph, gn)
        rho_seedavg = F11.spearman([r["phase_v2"] for r in avg],
                                   [r["gain"] for r in avg])
        rho_by_seed = {}
        for s in seeds:
            sub = [r for r in rows if r["seed"] == s]
            rho_by_seed[str(s)] = F11.spearman([r["phase_v2"] for r in sub],
                                               [r["gain"] for r in sub])
        impr_pooled = F11.ppl_improvement(fz, al)

        streams = [bootstrap_draws(dr, bs, args.b) for bs in args.boot_seeds]

        d = {
            "n_documents": len(docs), "n_seeds": len(seeds),
            "n_rows": len(rows),
            "rho_pooled_rows": rho_pooled,
            "rho_seed_averaged": rho_seedavg,
            "rho_by_seed": rho_by_seed,
            "ppl_improvement_pooled": impr_pooled,
            "variance_decomposition": F11.variance_decomposition(dr),
        }

        for quant, field in (("rho", "rho_ci"), ("impr", "impr_ci")):
            block = {}
            for kind in KINDS:
                pool = np.concatenate([s[kind][quant] for s in streams])
                lo, hi, n_used = _pct(pool)
                per_stream = [_pct(s[kind][quant])[:2] for s in streams]
                los = [p[0] for p in per_stream]
                his = [p[1] for p in per_stream]
                block[kind] = {
                    "lo": lo, "hi": hi, "width": float(hi - lo),
                    "n_units": streams[0][kind]["n_units"],
                    "n_draws": int(len(pool)),
                    "n_draws_finite": n_used,
                    # Monte Carlo diagnostics -- NOT the reported interval
                    "per_stream_endpoints": [[float(a), float(b)]
                                             for a, b in per_stream],
                    "mc_endpoint_range": {
                        "lo": [float(np.min(los)), float(np.max(los))],
                        "hi": [float(np.min(his)), float(np.max(his))]},
                    "superseded_mean_of_stream_endpoints": {
                        "lo": float(np.mean(los)), "hi": float(np.mean(his))},
                }
            for kind in ("cluster_nested", "cluster_seedavg"):
                denom = block["naive_iid_rows"]["width"]
                block[kind]["design_effect_vs_naive"] = float(
                    block[kind]["width"] / max(denom, 1e-12))
            d[field] = block

        out["domains"][dom] = d

        # ---------------------------------------------------- audit checks
        if audit is not None:
            a = audit["domains"][dom]
            for key in ("rho_pooled_rows", "rho_seed_averaged",
                        "ppl_improvement_pooled"):
                max_point_gap = max(max_point_gap, abs(d[key] - a[key]))
            for s in rho_by_seed:
                max_point_gap = max(max_point_gap,
                                    abs(rho_by_seed[s] - a["rho_by_seed"][s]))
            for field in ("rho_ci", "impr_ci"):
                for kind in KINDS:
                    ms = d[field][kind]["superseded_mean_of_stream_endpoints"]
                    max_stream_gap = max(
                        max_stream_gap,
                        abs(ms["lo"] - a[field][kind]["lo"]),
                        abs(ms["hi"] - a[field][kind]["hi"]))
                    for end in ("lo", "hi"):
                        sh = abs(d[field][kind][end] - a[field][kind][end])
                        if sh > max_shift:
                            max_shift, shift_where = sh, (
                                f"{dom}.{field}.{kind}.{end}")

        # ---- reproduction check against the published (pseudoreplicated) CI
        pr, plo, phi = F11.PUBLISHED_RHO_CI[dom]
        nlo = d["rho_ci"]["naive_iid_rows"]["lo"]
        nhi = d["rho_ci"]["naive_iid_rows"]["hi"]
        max_repro_gap = max(max_repro_gap, abs(nlo - plo), abs(nhi - phi),
                            abs(rho_pooled - pr))

        cn = d["rho_ci"]["cluster_nested"]
        ci = d["impr_ci"]["cluster_nested"]
        print(f"[f29] {dom:9s} rho={rho_pooled:+.3f}  pooled clustered "
              f"[{cn['lo']:+.6f}, {cn['hi']:+.6f}]  "
              f"(f11 mean-of-5 [{cn['superseded_mean_of_stream_endpoints']['lo']:+.6f}, "
              f"{cn['superseded_mean_of_stream_endpoints']['hi']:+.6f}])  "
              f"x{cn['design_effect_vs_naive']:.3f} wider;  impr "
              f"[{ci['lo']:.6f}, {ci['hi']:.6f}]", flush=True)

    out["max_reproduction_gap_vs_published"] = max_repro_gap
    assert max_repro_gap <= 0.02, (
        f"the naive construction does not reproduce the published intervals "
        f"(max endpoint gap {max_repro_gap:.4f})")

    out["headline"] = {
        dom: {
            "rho": out["domains"][dom]["rho_pooled_rows"],
            "ci_published_pseudoreplicated": list(F11.PUBLISHED_RHO_CI[dom][1:]),
            "ci_document_clustered": [
                out["domains"][dom]["rho_ci"]["cluster_nested"]["lo"],
                out["domains"][dom]["rho_ci"]["cluster_nested"]["hi"]],
            "impr": out["domains"][dom]["ppl_improvement_pooled"],
            "impr_ci_document_clustered": [
                out["domains"][dom]["impr_ci"]["cluster_nested"]["lo"],
                out["domains"][dom]["impr_ci"]["cluster_nested"]["hi"]],
            "n_documents": out["domains"][dom]["n_documents"],
            "n_rows": out["domains"][dom]["n_rows"],
        } for dom in DOMAINS}

    if audit is not None:
        out["audit_vs_f11"] = {
            "max_point_estimate_gap": max_point_gap,
            "max_endpoint_gap_vs_f11_per_stream": max_stream_gap,
            "max_endpoint_shift_vs_f11": max_shift,
            "max_endpoint_shift_location": shift_where,
            "note": ("per_stream gap ~0 proves f29 replays f11's exact draws; "
                     "shift is therefore attributable to the endpoint rule "
                     "alone"),
        }
        assert max_point_gap <= 1e-12, (
            f"point estimates moved ({max_point_gap:.3e}); pooling must not "
            f"touch them")
        assert max_stream_gap <= 1e-12, (
            f"re-derived per-stream endpoints do not reproduce f11's archived "
            f"means (max gap {max_stream_gap:.3e}); the RNG call sequence is "
            f"not being replayed and the pooled draws are not f11's draws")
        assert max_shift <= args.max_shift, (
            f"a pooled endpoint moved by {max_shift:.5f} at {shift_where}, "
            f"beyond the {args.max_shift} Monte Carlo tolerance; the five "
            f"streams would not be sampling one common bootstrap law")
        print(f"[f29] audit vs f11: points {max_point_gap:.2e}, per-stream "
              f"endpoints {max_stream_gap:.2e}, max pooled-vs-averaged "
              f"endpoint shift {max_shift:.6f} at {shift_where}", flush=True)

    C.save(out, args.out_name)
    print("[f29] DONE", flush=True)


if __name__ == "__main__":
    main()
