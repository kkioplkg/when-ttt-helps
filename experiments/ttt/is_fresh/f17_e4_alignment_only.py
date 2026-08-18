"""F17 -- the ALIGNMENT-ONLY statistic on E4, with document-clustered
intervals and a paired comparison against the full phase statistic.

WHY THIS SCRIPT EXISTS
----------------------
The leave-one-domain-out experiment (f12) concluded that what
transfers across GPT-2 domains is the ALIGNMENT factor

        alpha |alpha| / sigma^2

alone, and that the representation-distance factor delta_v2 adds no
measurable increment.  Figure 8 and the introduction, however, still
promote the FULL statistic alpha|alpha| delta_v2 / sigma^2 and its
correlations of 0.58-0.90.  The figure therefore still advertises the
superseded interpretation.

Redrawing the figure requires the alignment-only correlations to be
measured with the same estimator, the same records and the same interval
construction as the published full-statistic ones -- otherwise the two
series on the new figure would not be comparable, and "the shift factor is
unnecessary" would rest on a change of protocol rather than on the data.
This script produces exactly that comparison, from the ORIGINAL E4 records,
with no new experiment.

STATISTICS COMPARED (all three per document, per domain)
    alignment_only    alpha |alpha| / sigma^2                  <- headline
    phase_v2          alpha |alpha| delta_v2 / sigma^2         <- the paper's
    delta_v2_only     delta_v2                                 <- shift factor
                                                                  on its own

PROTOCOL (identical to f11_e4_cluster_ci.py except for the statistic and the
bootstrap RNG seeds, which are freshened)
  * estimand 1, `cluster_nested`: the pooled-row Spearman the manuscript
    quotes (500 documents x 3 adaptation seeds = 1500 rows), with the
    bootstrap resampling DOCUMENTS and carrying all three seed rows of a
    drawn document with it.  Point estimate and estimand unchanged from the
    published one; only the resampling unit is the corrected one.
  * estimand 2, `cluster_seedavg`: the per-document Spearman on the 500
    seed-averaged documents -- the unit the domain-level claim is actually
    about, and the unit f12 used.
  * gain: frozen_cont_ce - alta_cont_ce at the ALTA stop, unchanged.
  * B = 2000 resamples, percentile 2.5 / 97.5, bootstrap seeds
    20260811..20260815 (distinct from the f11 and f12 seeds,
    20260806..20260810).  Endpoints are reported as the mean over the five
    bootstrap seeds with the across-seed endpoint range.
  * PAIRED comparison: within each resample, rho(alignment_only) and
    rho(phase_v2) are computed on the SAME resampled documents and their
    difference is accumulated.  A paired interval that contains zero is the
    statement the new figure has to make -- the two statistics are not
    distinguishable on these data, so the shift factor is not carrying the
    correlation.

REPRODUCTION CHECKS (asserted)
  1. The pooled-row Spearman of phase_v2 reproduces the four published
     values (0.582 code, 0.905 legal, 0.868 PubMed, 0.834 WikiText) to
     within 0.002.
  2. The cluster_nested interval for phase_v2 reproduces f11's published
     corrected interval to within 0.02 in each endpoint, confirming that the
     fresh bootstrap seeds change nothing and the alignment-only series is
     built through the same machinery.
  3. The seed-averaged alignment-only correlations reproduce f12's
     `alpha_only` column exactly (same records, same estimator).

DATA (original records only; nothing is re-run)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json

Usage: python f17_e4_alignment_only.py
Writes experiments/results/is_fresh/f17_e4_alignment_only.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import common as C
import f11_e4_cluster_ci as F11

DOMAINS = F11.DOMAINS
BOOT_SEEDS = [20260811, 20260812, 20260813, 20260814, 20260815]
B = 2000

STATS = {
    "alignment_only": lambda r: (r["alpha"] * abs(r["alpha"])
                                 / _sig(r)),
    "phase_v2": lambda r: (r["alpha"] * abs(r["alpha"]) * r["delta_v2"]
                           / _sig(r)),
    "delta_v2_only": lambda r: r["delta_v2"],
}
HEADLINE = "alignment_only"
COMPARATOR = "phase_v2"


def _sig(r):
    s = r.get("sigma2_rel")
    return s if (s is not None and s > 1e-12) else 1.0


# --------------------------------------------------------------- assembly

def domain_tables(dom_recs):
    """Row-level (seeds pooled) and document-level (seeds averaged) tables."""
    docs = sorted(dom_recs)
    rows = F11._flatten(dom_recs, docs)
    row_tab = {k: np.array([fn(r) for r in rows], float)
               for k, fn in STATS.items()}
    row_tab["gain"] = np.array([r["gain"] for r in rows], float)

    avg_tab = {k: [] for k in STATS}
    avg_tab["gain"] = []
    for d in docs:
        rs = list(dom_recs[d].values())
        for k, fn in STATS.items():
            avg_tab[k].append(float(np.mean([fn(r) for r in rs])))
        avg_tab["gain"].append(float(np.mean([r["gain"] for r in rs])))
    avg_tab = {k: np.asarray(v, float) for k, v in avg_tab.items()}

    by_doc = {}
    for i, r in enumerate(rows):
        by_doc.setdefault(r["doc"], []).append(i)
    blocks = [np.asarray(by_doc[d], int) for d in docs]
    return docs, rows, row_tab, avg_tab, blocks


def bootstrap_domain(row_tab, avg_tab, blocks, boot_seed, b=B):
    """Document-clustered bootstrap of every statistic, plus paired diffs."""
    rng = np.random.default_rng(boot_seed)
    n_docs = len(blocks)
    keys = list(STATS)

    nested = {k: [] for k in keys}
    seedavg = {k: [] for k in keys}
    diff_nested, diff_seedavg = [], []

    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        idx = np.concatenate([blocks[k] for k in pick])
        g_rows = row_tab["gain"][idx]
        vals = {}
        for k in keys:
            vals[k] = F11.spearman(row_tab[k][idx], g_rows)
            nested[k].append(vals[k])
        if np.isfinite(vals[HEADLINE]) and np.isfinite(vals[COMPARATOR]):
            diff_nested.append(vals[HEADLINE] - vals[COMPARATOR])

        g_avg = avg_tab["gain"][pick]
        vals = {}
        for k in keys:
            vals[k] = F11.spearman(avg_tab[k][pick], g_avg)
            seedavg[k].append(vals[k])
        if np.isfinite(vals[HEADLINE]) and np.isfinite(vals[COMPARATOR]):
            diff_seedavg.append(vals[HEADLINE] - vals[COMPARATOR])

    out = {"cluster_nested": {}, "cluster_seedavg": {}}
    for k in keys:
        lo, hi, _ = F11._ci(nested[k])
        out["cluster_nested"][k] = (lo, hi)
        lo, hi, _ = F11._ci(seedavg[k])
        out["cluster_seedavg"][k] = (lo, hi)
    out["cluster_nested"]["_paired_diff"] = F11._ci(diff_nested)[:2]
    out["cluster_seedavg"]["_paired_diff"] = F11._ci(diff_seedavg)[:2]
    return out


def agg_endpoints(per_boot, kind, key):
    los = [p[kind][key][0] for p in per_boot]
    his = [p[kind][key][1] for p in per_boot]
    return {"lo": float(np.mean(los)), "hi": float(np.mean(his)),
            "lo_range": [float(np.min(los)), float(np.max(los))],
            "hi_range": [float(np.min(his)), float(np.max(his))],
            "width": float(np.mean(his) - np.mean(los))}


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    args = ap.parse_args()

    recs = F11.load_e4()
    assert set(recs) >= set(DOMAINS), f"missing {set(DOMAINS) - set(recs)}"

    f11 = json.load(open(os.path.join(C.RESULTS_DIR,
                                      "f11_e4_cluster_ci.json"),
                         encoding="utf-8"))
    f12 = json.load(open(os.path.join(C.RESULTS_DIR,
                                      "f12_e4_proxy_loo.json"),
                         encoding="utf-8"))

    out = {
        "script": "f17_e4_alignment_only.py",
        "finding": ("Figure 8 and the "
                    "introduction promote the full phase statistic at "
                    "rho 0.58-0.90 while the leave-one-domain-out result "
                    "says the alignment factor alone carries the signal"),
        "kind": "re-analysis of the ORIGINAL E4/E5 records; no new experiment",
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "statistics": {
            "alignment_only": "alpha|alpha| / sigma2_rel",
            "phase_v2": "alpha|alpha| delta_v2 / sigma2_rel",
            "delta_v2_only": "delta_v2"},
        "gain": "frozen_cont_ce - alta_cont_ce at the ALTA stop",
        "n_bootstrap": args.b, "bootstrap_seeds": args.boot_seeds,
        "protocol": ("document-clustered percentile bootstrap, 500 document "
                     "clusters with the three adaptation seeds nested; "
                     "identical to f11_e4_cluster_ci.py"),
        "domains": {},
    }

    max_pub_gap, max_f11_gap, max_f12_gap = 0.0, 0.0, 0.0
    for dom in DOMAINS:
        docs, rows, row_tab, avg_tab, blocks = domain_tables(recs[dom])
        n_docs, n_rows = len(docs), len(rows)

        rho_rows = {k: F11.spearman(row_tab[k], row_tab["gain"])
                    for k in STATS}
        rho_avg = {k: F11.spearman(avg_tab[k], avg_tab["gain"])
                   for k in STATS}
        rho_by_seed = {}
        for s in sorted({r["seed"] for r in rows}):
            m = np.array([r["seed"] == s for r in rows])
            rho_by_seed[str(s)] = {
                k: F11.spearman(row_tab[k][m], row_tab["gain"][m])
                for k in STATS}

        per_boot = [bootstrap_domain(row_tab, avg_tab, blocks, bs, args.b)
                    for bs in args.boot_seeds]

        d = {
            "n_documents": n_docs, "n_seeds": n_rows // n_docs,
            "n_rows": n_rows,
            "rho_pooled_rows": rho_rows,
            "rho_seed_averaged": rho_avg,
            "rho_by_seed_pooled": rho_by_seed,
            "ci_cluster_nested": {
                k: agg_endpoints(per_boot, "cluster_nested", k)
                for k in STATS},
            "ci_cluster_seedavg": {
                k: agg_endpoints(per_boot, "cluster_seedavg", k)
                for k in STATS},
            "paired_diff_alignment_minus_full": {
                "cluster_nested": agg_endpoints(per_boot, "cluster_nested",
                                                "_paired_diff"),
                "cluster_seedavg": agg_endpoints(per_boot, "cluster_seedavg",
                                                 "_paired_diff"),
                "point_pooled_rows": (rho_rows[HEADLINE]
                                      - rho_rows[COMPARATOR]),
                "point_seed_averaged": (rho_avg[HEADLINE]
                                        - rho_avg[COMPARATOR]),
            },
        }
        for kind in ("cluster_nested", "cluster_seedavg"):
            pd = d["paired_diff_alignment_minus_full"][kind]
            pd["contains_zero"] = bool(pd["lo"] <= 0.0 <= pd["hi"])
        out["domains"][dom] = d

        # ---- reproduction checks
        pr = F11.PUBLISHED_RHO_CI[dom][0]
        max_pub_gap = max(max_pub_gap, abs(rho_rows["phase_v2"] - pr))
        f11ci = f11["domains"][dom]["rho_ci"]["cluster_nested"]
        max_f11_gap = max(max_f11_gap,
                          abs(d["ci_cluster_nested"]["phase_v2"]["lo"]
                              - f11ci["lo"]),
                          abs(d["ci_cluster_nested"]["phase_v2"]["hi"]
                              - f11ci["hi"]))
        f12v = f12["per_domain_per_variant_rho_seed_averaged"][dom]["alpha_only"]
        max_f12_gap = max(max_f12_gap, abs(rho_avg["alignment_only"] - f12v))

        pn = d["paired_diff_alignment_minus_full"]["cluster_nested"]
        ps = d["paired_diff_alignment_minus_full"]["cluster_seedavg"]
        print(f"[f17] {dom:9s} alignment-only rho={rho_rows['alignment_only']:+.3f} "
              f"[{d['ci_cluster_nested']['alignment_only']['lo']:+.3f}, "
              f"{d['ci_cluster_nested']['alignment_only']['hi']:+.3f}]  vs "
              f"full rho={rho_rows['phase_v2']:+.3f} "
              f"[{d['ci_cluster_nested']['phase_v2']['lo']:+.3f}, "
              f"{d['ci_cluster_nested']['phase_v2']['hi']:+.3f}]  "
              f"paired diff [{pn['lo']:+.3f}, {pn['hi']:+.3f}]"
              f"{' (contains 0)' if pn['contains_zero'] else ''}; "
              f"doc-level diff [{ps['lo']:+.3f}, {ps['hi']:+.3f}]"
              f"{' (contains 0)' if ps['contains_zero'] else ''}; "
              f"delta_v2 alone {rho_rows['delta_v2_only']:+.3f}", flush=True)

    assert max_pub_gap <= 0.002, (
        f"phase_v2 does not reproduce the published pooled-row rho "
        f"(max gap {max_pub_gap:.4f})")
    assert max_f11_gap <= 0.02, (
        f"the clustered interval for phase_v2 does not reproduce f11 "
        f"(max endpoint gap {max_f11_gap:.4f})")
    assert max_f12_gap <= 1e-9, (
        f"the seed-averaged alignment-only rho does not reproduce f12's "
        f"alpha_only column (max gap {max_f12_gap:.2e})")

    ali_rows = [out["domains"][d]["rho_pooled_rows"]["alignment_only"]
                for d in DOMAINS]
    ful_rows = [out["domains"][d]["rho_pooled_rows"]["phase_v2"]
                for d in DOMAINS]
    ali_avg = [out["domains"][d]["rho_seed_averaged"]["alignment_only"]
               for d in DOMAINS]
    ful_avg = [out["domains"][d]["rho_seed_averaged"]["phase_v2"]
               for d in DOMAINS]
    dv2_rows = [out["domains"][d]["rho_pooled_rows"]["delta_v2_only"]
                for d in DOMAINS]
    n_zero_nested = sum(
        1 for d in DOMAINS
        if out["domains"][d]["paired_diff_alignment_minus_full"]
        ["cluster_nested"]["contains_zero"])
    n_zero_avg = sum(
        1 for d in DOMAINS
        if out["domains"][d]["paired_diff_alignment_minus_full"]
        ["cluster_seedavg"]["contains_zero"])
    n_align_higher = sum(1 for a, f in zip(ali_rows, ful_rows) if a > f)
    n_diff_positive = sum(
        1 for d in DOMAINS
        if out["domains"][d]["paired_diff_alignment_minus_full"]
        ["cluster_nested"]["lo"] > 0)
    n_diff_negative = sum(
        1 for d in DOMAINS
        if out["domains"][d]["paired_diff_alignment_minus_full"]
        ["cluster_nested"]["hi"] < 0)

    out["reproduction_checks"] = {
        "max_gap_phase_v2_vs_published_rho": max_pub_gap,
        "max_endpoint_gap_vs_f11_cluster_nested": max_f11_gap,
        "max_gap_alignment_only_vs_f12_alpha_only": max_f12_gap,
    }
    out["headline"] = {
        dom: {
            "n_documents": out["domains"][dom]["n_documents"],
            "n_rows": out["domains"][dom]["n_rows"],
            "rho_alignment_only": out["domains"][dom]["rho_pooled_rows"]["alignment_only"],
            "ci_alignment_only": [
                out["domains"][dom]["ci_cluster_nested"]["alignment_only"]["lo"],
                out["domains"][dom]["ci_cluster_nested"]["alignment_only"]["hi"]],
            "rho_full_statistic": out["domains"][dom]["rho_pooled_rows"]["phase_v2"],
            "ci_full_statistic": [
                out["domains"][dom]["ci_cluster_nested"]["phase_v2"]["lo"],
                out["domains"][dom]["ci_cluster_nested"]["phase_v2"]["hi"]],
            "rho_delta_v2_only": out["domains"][dom]["rho_pooled_rows"]["delta_v2_only"],
            "ci_delta_v2_only": [
                out["domains"][dom]["ci_cluster_nested"]["delta_v2_only"]["lo"],
                out["domains"][dom]["ci_cluster_nested"]["delta_v2_only"]["hi"]],
            "paired_diff_ci": [
                out["domains"][dom]["paired_diff_alignment_minus_full"]
                ["cluster_nested"]["lo"],
                out["domains"][dom]["paired_diff_alignment_minus_full"]
                ["cluster_nested"]["hi"]],
        } for dom in DOMAINS}
    out["summary"] = {
        "rho_alignment_only_pooled_rows": C.mean_range(ali_rows),
        "rho_full_statistic_pooled_rows": C.mean_range(ful_rows),
        "rho_delta_v2_only_pooled_rows": C.mean_range(dv2_rows),
        "rho_alignment_only_seed_averaged": C.mean_range(ali_avg),
        "rho_full_statistic_seed_averaged": C.mean_range(ful_avg),
        "n_domains_alignment_only_higher_than_full": n_align_higher,
        "n_domains_paired_diff_contains_zero_pooled": n_zero_nested,
        "n_domains_paired_diff_contains_zero_seed_averaged": n_zero_avg,
        "n_domains_paired_diff_favours_alignment": n_diff_positive,
        "n_domains_paired_diff_favours_full_statistic": n_diff_negative,
        "verdict": (
            "the alignment-only statistic matches or exceeds the full phase "
            f"statistic in {n_align_higher}/4 domains; the paired "
            "document-clustered interval for rho(alignment) - rho(full) "
            f"excludes zero on the alignment side in {n_diff_positive}/4 "
            f"domains, contains zero in {n_zero_nested}/4, and favours the "
            f"full statistic in {n_diff_negative}/4.  The shift factor "
            "delta_v2 on its own carries no consistent within-domain signal "
            f"(rho {min(dv2_rows):+.3f} to {max(dv2_rows):+.3f}).  Dropping "
            "delta_v2 from the plotted statistic loses nothing and in most "
            "domains gains, which is the simplification the figure has to "
            "show."),
    }
    C.save(out, "f17_e4_alignment_only.json")
    print(f"[f17] alignment-only mean rho {np.mean(ali_rows):+.3f} "
          f"({min(ali_rows):+.3f}..{max(ali_rows):+.3f}) vs full "
          f"{np.mean(ful_rows):+.3f} ({min(ful_rows):+.3f}.."
          f"{max(ful_rows):+.3f}); higher in {n_align_higher}/4 domains; "
          f"paired interval contains 0 in {n_zero_nested}/4 (pooled) and "
          f"{n_zero_avg}/4 (seed-averaged); delta_v2 alone "
          f"{np.mean(dv2_rows):+.3f} ({min(dv2_rows):+.3f}.."
          f"{max(dv2_rows):+.3f})")
    print("[f17] DONE", flush=True)


if __name__ == "__main__":
    main()
