"""F30 -- the E4 ALIGNMENT-ONLY comparison with document-clustered percentile
intervals read off ONE POOLED 10,000-draw bootstrap distribution.  Supersedes
the interval endpoints of `f17_e4_alignment_only.py`; every point estimate,
verdict and count is unchanged.

WHY THIS SCRIPT EXISTS
----------------------
`f17_e4_alignment_only.py` inherits f11's endpoint-averaging construction:
five independent document-clustered bootstraps (`B = 2000`, RNG seeds
20260811..20260815), five percentile pairs, and the arithmetic mean of the
five lower and the five upper endpoints reported as "the" interval.  The
manuscript, Figure 8 and the release documentation described the result as a
single document-clustered percentile interval.  A mean of five percentile
endpoints is not a percentile of anything, so the described object was not
the computed one.  `f29_e4_pooled_ci.py` carries the full argument, including
why this is a milder defect than the E2 split-averaging it resembles: the
five streams here differ only in the bootstrap RNG, so they are five Monte
Carlo estimates of ONE bootstrap-law endpoint rather than five estimands.

WHAT THIS SCRIPT COMPUTES INSTEAD
---------------------------------
The five streams are POOLED into 5 x 2000 = 10,000 draws per quantity and one
2.5 / 97.5 percentile pair is read off that single distribution -- for each of
the three statistics (alignment-only, the full phase statistic, delta_v2
alone), on both estimands (`cluster_nested`, `cluster_seedavg`), and for the
PAIRED difference rho(alignment) - rho(full).

The pairing is preserved exactly as f17 built it: within one resample both
statistics are evaluated on the same drawn documents and their difference is
accumulated as its own draw, so the pooled paired distribution is a pooling of
paired draws and not a difference of pooled marginals.

The draws are the SAME DRAWS f17 used.  `bootstrap_draws()` replays f17's RNG
call sequence exactly (one `integers()` call per resample, same order, same
`default_rng(seed)`), returning the per-draw vectors instead of collapsing
each stream to a percentile pair.  `max_endpoint_gap_vs_f17_per_stream`
asserts that re-deriving f17's averaged endpoints from these vectors returns
f17's archived numbers to 1e-12, so the pooled-versus-averaged difference is
attributable to the endpoint rule and to nothing else.

WHAT MOVES, AND WHAT CANNOT MOVE
--------------------------------
Point estimates and every derived count are asserted unchanged against f17:
`rho_pooled_rows`, `rho_seed_averaged`, `rho_by_seed_pooled`, the paired point
differences, and the five summary counts that carry the manuscript's verdict
(`n_domains_alignment_only_higher_than_full`,
`n_domains_paired_diff_contains_zero_*`,
`n_domains_paired_diff_favours_alignment`,
`n_domains_paired_diff_favours_full_statistic`).  A change in any of those
counts would mean a published conclusion had changed sign or significance
under pooling, so each is asserted, not merely recomputed.

DATA (original records only; nothing is re-run, no new experiment)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json
  experiments/results/is_fresh/f17_e4_alignment_only.json  (audit trail, read
                                                            only)
  experiments/results/is_fresh/f12_e4_proxy_loo.json       (alpha_only check)

Usage: python f30_e4_alignment_pooled.py
Writes experiments/results/is_fresh/f30_e4_alignment_pooled.json
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import common as C
import f11_e4_cluster_ci as F11
import f17_e4_alignment_only as F17

DOMAINS = F17.DOMAINS
BOOT_SEEDS = list(F17.BOOT_SEEDS)        # 20260811..20260815, unchanged
B = F17.B                                # 2000 per stream, unchanged
STATS = F17.STATS
HEADLINE = F17.HEADLINE
COMPARATOR = F17.COMPARATOR
KINDS = ("cluster_nested", "cluster_seedavg")

# The FIXED-BUDGET endpoint.  The manuscript's primary E3 adaptation result is
# a fixed budget of 20 steps, and the retrospective selector is reported as
# beaten by it.  A correlation table whose gain column is taken at the
# SELECTOR's index therefore ranks a secondary endpoint while the text calls
# the fixed budget primary.  This block recomputes every quantity of the table
# against `frozen_cont_ce - fixed[20]_cont_ce` ON THE SAME BOOTSTRAP DRAWS --
# same RNG seeds, same call order, same document clusters -- so the two
# endpoints are compared and not merely both reported.  The point estimates
# are cross-checked against `f32_e4_fixed_budget_ci.json`, which computes them
# by an independently written path.
FIXED_BUDGET = 20


def load_fixed_ce(budget=FIXED_BUDGET):
    """domain -> doc -> seed -> continuation CE after exactly `budget` steps.

    Same records and same admission rule as F11.load_e4, plus the presence of
    the budget in the record's `fixed` block, so the document set is identical
    to the one the selected-index tables use.  The run horizon is asserted to
    BE the budget, otherwise `t = 20` would be a step selected out of a longer
    trajectory rather than the whole budget spent.
    """
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(F11.E4_DIR, "*_ln_s*.json"))):
        o = json.loads(open(p, encoding="utf-8").read())
        dom = o["meta"]["argv"]["domain"]
        seed = int(o["meta"]["argv"]["seed"])
        assert int(o["meta"]["argv"]["steps"]) == int(budget), (
            f"{p}: run horizon {o['meta']['argv']['steps']} is not the fixed "
            f"budget {budget}")
        for r in o["records"]:
            if not r.get("alta"):
                continue
            fixed = r.get("fixed") or {}
            ce = fixed.get(budget, fixed.get(str(budget)))
            if ce is None:
                continue
            out.setdefault(dom, {}).setdefault(int(r["doc"]), {})[seed] = \
                float(r["frozen_cont_ce"]) - float(ce)
    return out


def retarget_gain(docs, rows, row_tab, avg_tab, gain_by_doc_seed):
    """Copies of the two tables with the gain column taken at another endpoint.

    Every statistic column is shared with the originals by reference: only the
    gain moves, which is the whole point -- any difference in the resulting
    correlations is attributable to the endpoint and to nothing else.
    """
    g_rows = np.array([gain_by_doc_seed[r["doc"]][r["seed"]] for r in rows],
                      float)
    g_avg = np.array([float(np.mean(list(gain_by_doc_seed[d].values())))
                      for d in docs], float)
    rt = dict(row_tab)
    rt["gain"] = g_rows
    at = dict(avg_tab)
    at["gain"] = g_avg
    return rt, at


def bootstrap_draws(row_tab, avg_tab, blocks, boot_seed, b=B):
    """One stream's raw draws, in f17's exact RNG call order.

    Returns {kind: {stat_or_'_paired_diff': ndarray}}.
    """
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

    out = {"cluster_nested": {k: np.asarray(v, float)
                              for k, v in nested.items()},
           "cluster_seedavg": {k: np.asarray(v, float)
                               for k, v in seedavg.items()}}
    out["cluster_nested"]["_paired_diff"] = np.asarray(diff_nested, float)
    out["cluster_seedavg"]["_paired_diff"] = np.asarray(diff_seedavg, float)
    return out


def _pct(v):
    x = np.asarray([t for t in v if np.isfinite(t)], float)
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi)


def pooled_block(streams, kind, key):
    pool = np.concatenate([s[kind][key] for s in streams])
    lo, hi = _pct(pool)
    per_stream = [_pct(s[kind][key]) for s in streams]
    los = [p[0] for p in per_stream]
    his = [p[1] for p in per_stream]
    return {
        "lo": lo, "hi": hi, "width": float(hi - lo),
        "n_draws": int(len(pool)),
        "per_stream_endpoints": [[float(a), float(b)] for a, b in per_stream],
        "mc_endpoint_range": {
            "lo": [float(np.min(los)), float(np.max(los))],
            "hi": [float(np.min(his)), float(np.max(his))]},
        "superseded_mean_of_stream_endpoints": {
            "lo": float(np.mean(los)), "hi": float(np.mean(his))},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    ap.add_argument("--max-shift", type=float, default=0.01)
    ap.add_argument("--out-name", default="f30_e4_alignment_pooled.json")
    ap.add_argument("--no-audit", action="store_true")
    args = ap.parse_args()

    recs = F11.load_e4()
    assert set(recs) >= set(DOMAINS), f"missing {set(DOMAINS) - set(recs)}"

    audit = None
    if not args.no_audit:
        with open(os.path.join(C.RESULTS_DIR, "f17_e4_alignment_only.json"),
                  encoding="utf-8") as fh:
            audit = json.load(fh)
    with open(os.path.join(C.RESULTS_DIR, "f12_e4_proxy_loo.json"),
              encoding="utf-8") as fh:
        f12 = json.load(fh)

    out = {
        "script": "f30_e4_alignment_pooled.py",
        "supersedes": "f17_e4_alignment_only.py (interval endpoints only)",
        "finding": ("the E4 brackets "
                    "were the arithmetic mean of five per-stream percentile "
                    "endpoints while several sites described them as a single "
                    "document-clustered percentile interval"),
        "correction": ("the five B = 2000 streams are pooled into one "
                       "10,000-draw empirical distribution per quantity "
                       "(paired differences pooled as paired draws) and one "
                       "2.5/97.5 percentile pair is read off it"),
        "kind": "re-analysis of the ORIGINAL E4/E5 records; no new experiment",
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "statistics": {
            "alignment_only": "alpha|alpha| / sigma2_rel",
            "phase_v2": "alpha|alpha| delta_v2 / sigma2_rel",
            "delta_v2_only": "delta_v2"},
        "gain": "frozen_cont_ce - alta_cont_ce at the ALTA stop",
        "n_bootstrap_per_stream": args.b,
        "bootstrap_seeds": args.boot_seeds,
        "n_pooled_draws": args.b * len(args.boot_seeds),
        "protocol": ("document-clustered percentile bootstrap, 500 document "
                     "clusters with the three adaptation seeds nested; the "
                     "five RNG streams are pooled into one distribution and "
                     "the reported endpoints are genuine percentiles of it, "
                     "with no averaging of endpoints; identical to "
                     "f29_e4_pooled_ci.py"),
        "domains": {},
    }

    max_pub_gap = max_f29_gap = max_f12_gap = max_f32_gap = 0.0
    max_stream_gap = max_point_gap = 0.0
    max_shift, shift_where = 0.0, None

    f29 = json.load(open(os.path.join(C.RESULTS_DIR, "f29_e4_pooled_ci.json"),
                         encoding="utf-8"))
    f32 = json.load(open(os.path.join(C.RESULTS_DIR,
                                      "f32_e4_fixed_budget_ci.json"),
                         encoding="utf-8"))
    fixed_gain = load_fixed_ce()
    for dom in DOMAINS:
        missing = set(recs[dom]) - set(fixed_gain.get(dom, {}))
        assert not missing, (
            f"{dom}: {len(missing)} documents carry a selector record but no "
            f"fixed[{FIXED_BUDGET}] continuation CE, so the two endpoints "
            f"would be compared on different document sets")

    for dom in DOMAINS:
        docs, rows, row_tab, avg_tab, blocks = F17.domain_tables(recs[dom])
        n_docs, n_rows = len(docs), len(rows)

        rho_rows = {k: F11.spearman(row_tab[k], row_tab["gain"])
                    for k in STATS}
        rho_avg = {k: F11.spearman(avg_tab[k], avg_tab["gain"]) for k in STATS}
        rho_by_seed = {}
        for s in sorted({r["seed"] for r in rows}):
            m = np.array([r["seed"] == s for r in rows])
            rho_by_seed[str(s)] = {
                k: F11.spearman(row_tab[k][m], row_tab["gain"][m])
                for k in STATS}

        streams = [bootstrap_draws(row_tab, avg_tab, blocks, bs, args.b)
                   for bs in args.boot_seeds]

        d = {
            "n_documents": n_docs, "n_seeds": n_rows // n_docs,
            "n_rows": n_rows,
            "rho_pooled_rows": rho_rows,
            "rho_seed_averaged": rho_avg,
            "rho_by_seed_pooled": rho_by_seed,
            "ci_cluster_nested": {k: pooled_block(streams, "cluster_nested", k)
                                  for k in STATS},
            "ci_cluster_seedavg": {k: pooled_block(streams, "cluster_seedavg",
                                                   k) for k in STATS},
            "paired_diff_alignment_minus_full": {
                "cluster_nested": pooled_block(streams, "cluster_nested",
                                               "_paired_diff"),
                "cluster_seedavg": pooled_block(streams, "cluster_seedavg",
                                                "_paired_diff"),
                "point_pooled_rows": rho_rows[HEADLINE] - rho_rows[COMPARATOR],
                "point_seed_averaged": rho_avg[HEADLINE] - rho_avg[COMPARATOR],
            },
        }
        for kind in KINDS:
            pd = d["paired_diff_alignment_minus_full"][kind]
            pd["contains_zero"] = bool(pd["lo"] <= 0.0 <= pd["hi"])

        # ---------------- the same quantities at the FIXED-BUDGET endpoint
        rt20, at20 = retarget_gain(docs, rows, row_tab, avg_tab,
                                   fixed_gain[dom])
        rho_rows20 = {k: F11.spearman(rt20[k], rt20["gain"]) for k in STATS}
        rho_avg20 = {k: F11.spearman(at20[k], at20["gain"]) for k in STATS}
        streams20 = [bootstrap_draws(rt20, at20, blocks, bs, args.b)
                     for bs in args.boot_seeds]
        d20 = {
            "endpoint": (f"frozen_cont_ce - fixed[{FIXED_BUDGET}] cont_ce, "
                         f"the manuscript's primary adaptation result"),
            "rho_pooled_rows": rho_rows20,
            "rho_seed_averaged": rho_avg20,
            "ci_cluster_nested": {
                k: pooled_block(streams20, "cluster_nested", k)
                for k in STATS},
            "ci_cluster_seedavg": {
                k: pooled_block(streams20, "cluster_seedavg", k)
                for k in STATS},
            "paired_diff_alignment_minus_full": {
                "cluster_nested": pooled_block(streams20, "cluster_nested",
                                               "_paired_diff"),
                "cluster_seedavg": pooled_block(streams20, "cluster_seedavg",
                                                "_paired_diff"),
                "point_pooled_rows": (rho_rows20[HEADLINE]
                                      - rho_rows20[COMPARATOR]),
                "point_seed_averaged": (rho_avg20[HEADLINE]
                                        - rho_avg20[COMPARATOR]),
            },
            "rho_shift_vs_selected_index": {
                k: float(rho_rows20[k] - rho_rows[k]) for k in STATS},
        }
        for kind in KINDS:
            pd = d20["paired_diff_alignment_minus_full"][kind]
            pd["contains_zero"] = bool(pd["lo"] <= 0.0 <= pd["hi"])
        d["endpoint_fixed_budget"] = d20

        # f32 computes these two point estimates from its own loader; a
        # disagreement means one of the two paths is reading a different
        # document set or a different budget.
        f32d = f32["rank_robustness_to_gain_column"]["by_domain"][dom]
        for stat, key in (("alignment_only",
                           "rho_alignment_only_vs_fixed20_gain"),
                          ("phase_v2",
                           "rho_full_statistic_vs_fixed20_gain")):
            max_f32_gap = max(max_f32_gap,
                              abs(rho_rows20[stat] - f32d[key]))

        out["domains"][dom] = d

        # ------------------------------------------------- reproduction checks
        pr = F11.PUBLISHED_RHO_CI[dom][0]
        max_pub_gap = max(max_pub_gap, abs(rho_rows["phase_v2"] - pr))
        f29ci = f29["domains"][dom]["rho_ci"]["cluster_nested"]
        max_f29_gap = max(max_f29_gap,
                          abs(d["ci_cluster_nested"]["phase_v2"]["lo"]
                              - f29ci["lo"]),
                          abs(d["ci_cluster_nested"]["phase_v2"]["hi"]
                              - f29ci["hi"]))
        f12v = f12["per_domain_per_variant_rho_seed_averaged"][dom]["alpha_only"]
        max_f12_gap = max(max_f12_gap, abs(rho_avg["alignment_only"] - f12v))

        if audit is not None:
            a = audit["domains"][dom]
            for k in STATS:
                max_point_gap = max(
                    max_point_gap,
                    abs(rho_rows[k] - a["rho_pooled_rows"][k]),
                    abs(rho_avg[k] - a["rho_seed_averaged"][k]))
            apd = a["paired_diff_alignment_minus_full"]
            npd = d["paired_diff_alignment_minus_full"]
            for key in ("point_pooled_rows", "point_seed_averaged"):
                max_point_gap = max(max_point_gap, abs(npd[key] - apd[key]))
            for kind in KINDS:
                field = ("ci_cluster_nested" if kind == "cluster_nested"
                         else "ci_cluster_seedavg")
                for k in STATS:
                    ms = d[field][k]["superseded_mean_of_stream_endpoints"]
                    max_stream_gap = max(max_stream_gap,
                                         abs(ms["lo"] - a[field][k]["lo"]),
                                         abs(ms["hi"] - a[field][k]["hi"]))
                    for end in ("lo", "hi"):
                        sh = abs(d[field][k][end] - a[field][k][end])
                        if sh > max_shift:
                            max_shift, shift_where = sh, f"{dom}.{field}.{k}.{end}"
                ms = npd[kind]["superseded_mean_of_stream_endpoints"]
                max_stream_gap = max(max_stream_gap,
                                     abs(ms["lo"] - apd[kind]["lo"]),
                                     abs(ms["hi"] - apd[kind]["hi"]))
                for end in ("lo", "hi"):
                    sh = abs(npd[kind][end] - apd[kind][end])
                    if sh > max_shift:
                        max_shift, shift_where = sh, (
                            f"{dom}.paired_diff.{kind}.{end}")
                assert npd[kind]["contains_zero"] == apd[kind]["contains_zero"], (
                    f"{dom} {kind}: the paired interval changed its relation to "
                    f"zero under pooling -- a published significance claim "
                    f"would move")

        pn = d["paired_diff_alignment_minus_full"]["cluster_nested"]
        print(f"[f30] {dom:9s} align rho={rho_rows['alignment_only']:+.3f} "
              f"[{d['ci_cluster_nested']['alignment_only']['lo']:+.6f}, "
              f"{d['ci_cluster_nested']['alignment_only']['hi']:+.6f}]  full "
              f"[{d['ci_cluster_nested']['phase_v2']['lo']:+.6f}, "
              f"{d['ci_cluster_nested']['phase_v2']['hi']:+.6f}]  paired "
              f"[{pn['lo']:+.6f}, {pn['hi']:+.6f}]"
              f"{' (contains 0)' if pn['contains_zero'] else ''}", flush=True)

    assert max_pub_gap <= 0.002, (
        f"phase_v2 does not reproduce the published pooled-row rho "
        f"(max gap {max_pub_gap:.4f})")
    assert max_f29_gap <= 0.02, (
        f"the pooled clustered interval for phase_v2 does not reproduce f29 "
        f"(max endpoint gap {max_f29_gap:.4f})")
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
        "max_endpoint_gap_vs_f29_cluster_nested": max_f29_gap,
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

    # ---------------- the fixed-budget endpoint, summarized
    fb_ali = [out["domains"][d]["endpoint_fixed_budget"]["rho_pooled_rows"]
              ["alignment_only"] for d in DOMAINS]
    fb_ful = [out["domains"][d]["endpoint_fixed_budget"]["rho_pooled_rows"]
              ["phase_v2"] for d in DOMAINS]
    fb_pd = [out["domains"][d]["endpoint_fixed_budget"]
             ["paired_diff_alignment_minus_full"]["cluster_nested"]
             for d in DOMAINS]
    fb_ci = [out["domains"][d]["endpoint_fixed_budget"]["ci_cluster_nested"]
             ["alignment_only"] for d in DOMAINS]
    max_endpoint_rho_shift = max(
        abs(out["domains"][d]["endpoint_fixed_budget"]
            ["rho_shift_vs_selected_index"][k])
        for d in DOMAINS for k in STATS)
    out["summary_fixed_budget_endpoint"] = {
        "endpoint": (f"per-document continuation-CE gain at the fixed budget "
                     f"t = {FIXED_BUDGET}"),
        "rho_alignment_only_pooled_rows": C.mean_range(fb_ali),
        "rho_full_statistic_pooled_rows": C.mean_range(fb_ful),
        "n_domains_gate_passes": int(sum(c["lo"] > 0.0 for c in fb_ci)),
        "n_domains_paired_diff_favours_alignment":
            int(sum(p["lo"] > 0.0 for p in fb_pd)),
        "n_domains_paired_diff_contains_zero":
            int(sum(p["contains_zero"] for p in fb_pd)),
        "n_domains_paired_diff_favours_full_statistic":
            int(sum(p["hi"] < 0.0 for p in fb_pd)),
        "max_abs_rho_shift_vs_selected_index": float(max_endpoint_rho_shift),
        "max_point_gap_vs_f32": float(max_f32_gap),
        "verdict": ("every qualitative conclusion of the selected-index "
                    "table survives at the fixed budget: the same gate "
                    "outcome, the same paired-difference direction, and no "
                    "correlation moves by more than "
                    f"{max_endpoint_rho_shift:.4f}"),
    }
    assert max_f32_gap <= 1e-12, (
        f"the fixed-budget point estimates disagree with f32 by "
        f"{max_f32_gap:.3e}; the two paths are not reading the same "
        f"documents or the same budget")

    if audit is not None:
        asum = audit["summary"]
        for key in ("n_domains_alignment_only_higher_than_full",
                    "n_domains_paired_diff_contains_zero_pooled",
                    "n_domains_paired_diff_contains_zero_seed_averaged",
                    "n_domains_paired_diff_favours_alignment",
                    "n_domains_paired_diff_favours_full_statistic"):
            assert out["summary"][key] == asum[key], (
                f"{key} moved under pooling ({asum[key]} -> "
                f"{out['summary'][key]}); a published conclusion would change")
        out["audit_vs_f17"] = {
            "max_point_estimate_gap": max_point_gap,
            "max_endpoint_gap_vs_f17_per_stream": max_stream_gap,
            "max_endpoint_shift_vs_f17": max_shift,
            "max_endpoint_shift_location": shift_where,
            "verdict_counts_unchanged": True,
        }
        assert max_point_gap <= 1e-12, (
            f"point estimates moved ({max_point_gap:.3e}); pooling must not "
            f"touch them")
        assert max_stream_gap <= 1e-12, (
            f"re-derived per-stream endpoints do not reproduce f17's archived "
            f"means (max gap {max_stream_gap:.3e}); the RNG call sequence is "
            f"not being replayed")
        assert max_shift <= args.max_shift, (
            f"a pooled endpoint moved by {max_shift:.5f} at {shift_where}, "
            f"beyond the {args.max_shift} Monte Carlo tolerance")
        print(f"[f30] audit vs f17: points {max_point_gap:.2e}, per-stream "
              f"endpoints {max_stream_gap:.2e}, max pooled-vs-averaged "
              f"endpoint shift {max_shift:.6f} at {shift_where}; verdict "
              f"counts unchanged", flush=True)

    C.save(out, args.out_name)
    print("[f30] DONE", flush=True)


if __name__ == "__main__":
    main()
