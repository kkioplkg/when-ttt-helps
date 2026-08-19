"""F32 -- E4 document-clustered intervals for the FIXED-BUDGET arms, on
exactly f29's draws, so the fixed budget and the retrospective selector are
comparable endpoint-for-endpoint.

WHY THIS SCRIPT EXISTS
----------------------
The E4 headline was stated at the retrospective ALTA index t_hat, and the
document-clustered intervals shipped for it (f11 -> f29) exist only for that
arm.  The selector is admissible-at-t only after every later step u > t has
been observed, so it is a full-horizon retrospective selection, not an online
stopping rule; and the same records show that a FIXED budget of t = 20 steps
attains a larger mean improvement in every domain.  Before the simpler claim
can carry the headline it has to be established to the SAME evidential
standard as the claim it replaces: a document-clustered percentile interval
excluding zero in every domain, on the same resampling unit, the same
estimand form, and the same pooled 10,000-draw endpoint rule.

That is what this script computes.  Nothing is re-run and no new experiment is
introduced; the fixed-step continuation cross-entropies are already stored in
the E4 records (`records[i]["fixed"][t]`) and were used to print the
"within 7-15% relative of the best fixed step" comparison.

WHAT IS COMPUTED
----------------
Per domain, for each candidate arm

    alta            frozen_cont_ce - alta_cont_ce         (the current headline)
    fixed_1/2/5/10/20   frozen_cont_ce - fixed[t]         (the fixed budgets)
    oracle          frozen_cont_ce - oracle_cont_ce       (the per-document
                                                           oracle over the
                                                           recorded grid)

  * the pooled perplexity improvement exp(mean frozen) - exp(mean adapted),
    the paper's `impr_stat`, identical in form to f11/f29;
  * document-clustered percentile intervals under f11's three constructions,
    with f29's pooled 10,000-draw endpoint rule;
  * the PAIRED difference impr(fixed 20) - impr(alta), computed inside each
    resample so both arms see the same drawn documents -- the load-bearing
    comparison, exactly as the alignment-vs-full paired difference in
    Table T7 is the load-bearing comparison there.

RNG DISCIPLINE / REPRODUCTION CHECK (asserted)
----------------------------------------------
The draw sequence is f11's, byte for byte: `default_rng(seed)`, the three
constructions in the same order, the same number of `integers()` calls with
the same shapes.  Extra statistics are evaluated on each drawn index set, but
no additional numbers are drawn.  Therefore the `alta` arm here must
reproduce f29's archived interval endpoints to Monte Carlo zero, and that is
asserted (`max_alta_endpoint_gap_vs_f29`).  If it did not, the two series
would not be on the same draws and the paired comparison would be void.

DATA (original records only)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json
  experiments/results/is_fresh/f29_e4_pooled_ci.json  (read only, audit)

Usage: python f32_e4_fixed_budget_ci.py
Writes experiments/results/is_fresh/f32_e4_fixed_budget_ci.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

import common as C
import f11_e4_cluster_ci as F11

DOMAINS = F11.DOMAINS
BOOT_SEEDS = list(F11.BOOT_SEEDS)          # 20260806..20260810, f11's stream
B = F11.B                                  # 2000 per stream
KINDS = ("naive_iid_rows", "cluster_nested", "cluster_seedavg")
FIXED_STEPS = ("1", "2", "5", "10", "20")
ARMS = ("alta", "oracle") + tuple(f"fixed_{t}" for t in FIXED_STEPS)


# ----------------------------------------------------------------- loading

def load_e4_arms():
    """domain -> doc -> seed -> {frozen_ce, <arm>_ce for every arm, t_hat}.

    Same record set and same admission rule as F11.load_e4 (a record is used
    iff it carries an `alta` block), so the document sets are identical and
    the arms are compared on one common population.
    """
    dv2 = F11.load_delta_v2()
    out = {}
    for p in sorted(glob.glob(os.path.join(F11.E4_DIR, "*_ln_s*.json"))):
        o = json.loads(open(p, encoding="utf-8").read())
        dom = o["meta"]["argv"]["domain"]
        seed = int(o["meta"]["argv"]["seed"])
        # The largest recorded budget must BE the run horizon, otherwise
        # "t = 20" would be a step selected from a longer trajectory.
        assert int(o["meta"]["argv"]["steps"]) == int(FIXED_STEPS[-1]), (
            f"{p}: run horizon {o['meta']['argv']['steps']} is not the largest "
            f"recorded fixed step {FIXED_STEPS[-1]}")
        dmap = dv2.get(dom, {})
        for r in o["records"]:
            if not r.get("alta"):
                continue
            a, s2 = r.get("alpha"), r.get("sigma2_rel")
            doc = int(r["doc"])
            v2 = dmap.get(doc)
            if a is None or v2 is None:
                continue
            fixed = r.get("fixed") or {}
            if any(fixed.get(t) is None for t in FIXED_STEPS):
                continue
            ph = a * abs(a) * v2
            if s2 is not None and s2 > 1e-12:
                ph = ph / s2
            rec = {
                "doc": doc, "seed": seed, "phase_v2": float(ph),
                "alpha": float(a),
                "sigma2_rel": float(s2) if s2 is not None else 1.0,
                "delta_v2": float(v2),
                "frozen_ce": float(r["frozen_cont_ce"]),
                "alta_ce": float(r["alta"]["cont_ce"]),
                "oracle_ce": float(r["oracle"]["cont_ce"]),
                "t_hat": r["alta"].get("t_hat"),
                "t_star": r["oracle"].get("t_star"),
            }
            for t in FIXED_STEPS:
                rec[f"fixed_{t}_ce"] = float(fixed[t])
            out.setdefault(dom, {}).setdefault(doc, {})[seed] = rec
    return out


def _seedavg_arms(dom_recs, docs):
    keys = ["frozen_ce"] + [f"{a}_ce" for a in ARMS]
    out = []
    for d in docs:
        rs = list(dom_recs[d].values())
        out.append({k: float(np.mean([r[k] for r in rs])) for k in keys})
    return out


# --------------------------------------------------------------- bootstrap

def bootstrap_draws(dom_recs, boot_seed, b=B):
    """One stream's raw draws in f11's exact RNG call order.

    Per draw we evaluate the improvement of EVERY arm on the one index set the
    draw produced.  The RNG is advanced only by the `integers()` calls f11
    makes, in f11's order, so the draws are f11's draws.
    """
    rng = np.random.default_rng(boot_seed)
    docs = sorted(dom_recs)
    rows = F11._flatten(dom_recs, docs)
    n_rows, n_docs = len(rows), len(docs)
    avg = _seedavg_arms(dom_recs, docs)

    fz_rows = np.array([r["frozen_ce"] for r in rows])
    arm_rows = {a: np.array([r[f"{a}_ce"] for r in rows]) for a in ARMS}

    by_doc = {}
    for i, r in enumerate(rows):
        by_doc.setdefault(r["doc"], []).append(i)
    doc_blocks = [np.asarray(by_doc[d], int) for d in docs]

    fz_avg = np.array([r["frozen_ce"] for r in avg])
    arm_avg = {a: np.array([r[f"{a}_ce"] for r in avg]) for a in ARMS}

    out = {}
    imp = F11.ppl_improvement

    # (1) f11's published construction: i.i.d. over the pooled rows
    acc = {a: [] for a in ARMS}
    for _ in range(b):
        idx = rng.integers(0, n_rows, n_rows)
        for a in ARMS:
            acc[a].append(imp(fz_rows[idx], arm_rows[a][idx]))
    out["naive_iid_rows"] = {a: np.asarray(v, float) for a, v in acc.items()}
    out["naive_iid_rows"]["n_units"] = n_rows

    # (2) clustered, seeds nested inside the resampled document
    acc = {a: [] for a in ARMS}
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        idx = np.concatenate([doc_blocks[k] for k in pick])
        for a in ARMS:
            acc[a].append(imp(fz_rows[idx], arm_rows[a][idx]))
    out["cluster_nested"] = {a: np.asarray(v, float) for a, v in acc.items()}
    out["cluster_nested"]["n_units"] = n_docs

    # (3) clustered, seeds averaged within document
    acc = {a: [] for a in ARMS}
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        for a in ARMS:
            acc[a].append(imp(fz_avg[pick], arm_avg[a][pick]))
    out["cluster_seedavg"] = {a: np.asarray(v, float) for a, v in acc.items()}
    out["cluster_seedavg"]["n_units"] = n_docs
    return out


def _pct(v):
    x = np.asarray([t for t in v if np.isfinite(t)], float)
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi), int(len(x))


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    ap.add_argument("--out-name", default="f32_e4_fixed_budget_ci.json")
    ap.add_argument("--no-audit", action="store_true")
    args = ap.parse_args()

    recs = load_e4_arms()
    assert set(recs) >= set(DOMAINS), f"missing domains: {set(DOMAINS)-set(recs)}"

    audit = None
    if not args.no_audit:
        with open(os.path.join(C.RESULTS_DIR, "f29_e4_pooled_ci.json"),
                  encoding="utf-8") as fh:
            audit = json.load(fh)

    out = {
        "script": "f32_e4_fixed_budget_ci.py",
        "question": ("does a FIXED adaptation budget improve on the frozen "
                     "model in every domain, to the same document-clustered "
                     "evidential standard as the retrospective ALTA index?"),
        "kind": "re-analysis of the ORIGINAL E4/E5 records; no new experiment",
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "statistic": "exp(mean frozen_cont_ce) - exp(mean adapted_cont_ce)",
        "arms": list(ARMS),
        "protocol": ("f11's document-clustered percentile bootstrap (500 "
                     "document clusters, three adaptation seeds nested) with "
                     "f29's pooled endpoint rule: the five B = 2000 RNG "
                     "streams are concatenated into one 10,000-draw empirical "
                     "distribution per quantity and one 2.5/97.5 percentile "
                     "pair is read off it.  Every arm is evaluated on the SAME "
                     "drawn index set, so paired differences are exact."),
        "n_bootstrap_per_stream": args.b,
        "bootstrap_seeds": args.boot_seeds,
        "n_pooled_draws": args.b * len(args.boot_seeds),
        "domains": {},
    }

    max_alta_gap = 0.0
    max_alta_point_gap = 0.0
    for dom in DOMAINS:
        dr = recs[dom]
        docs = sorted(dr)
        rows = F11._flatten(dr, docs)
        fz = np.array([r["frozen_ce"] for r in rows])

        point = {a: F11.ppl_improvement(
            fz, np.array([r[f"{a}_ce"] for r in rows])) for a in ARMS}
        t_hats = np.array([r["t_hat"] for r in rows], float)
        t_stars = np.array([r["t_star"] for r in rows], float)

        streams = [bootstrap_draws(dr, bs, args.b) for bs in args.boot_seeds]

        d = {
            "n_documents": len(docs),
            "n_seeds": len(sorted({r["seed"] for r in rows})),
            "n_rows": len(rows),
            "frozen_ppl": float(np.exp(np.mean(fz))),
            "mean_t_hat": float(t_hats.mean()),
            "mean_t_star_on_recorded_grid": float(t_stars.mean()),
            "frac_t_star_eq_20": float((t_stars == 20).mean()),
            "impr_point": point,
            "impr_ci": {},
            "paired_fixed20_minus_alta": {},
        }

        for kind in KINDS:
            block = {}
            for a in ARMS:
                pool = np.concatenate([s[kind][a] for s in streams])
                lo, hi, n_used = _pct(pool)
                block[a] = {"lo": lo, "hi": hi, "width": float(hi - lo),
                            "excludes_zero_positive": bool(lo > 0.0),
                            "n_draws": int(len(pool)), "n_draws_finite": n_used,
                            "n_units": int(streams[0][kind]["n_units"])}
            d["impr_ci"][kind] = block

            pool_d = np.concatenate(
                [s[kind]["fixed_20"] - s[kind]["alta"] for s in streams])
            lo, hi, _ = _pct(pool_d)
            d["paired_fixed20_minus_alta"][kind] = {
                "point": float(point["fixed_20"] - point["alta"]),
                "lo": lo, "hi": hi,
                "excludes_zero_favouring_fixed20": bool(lo > 0.0),
                "n_draws": int(len(pool_d))}

        # relative shortfall of the retrospective selector against fixed 20
        d["alta_relative_shortfall_vs_fixed20"] = float(
            1.0 - point["alta"] / point["fixed_20"]) if point["fixed_20"] else None
        d["best_fixed_step"] = max(
            FIXED_STEPS, key=lambda t: point[f"fixed_{t}"])
        # Is the largest budget best because it won a selection over the
        # recorded grid, or because the gain simply increases with the budget?
        # If the latter, t = 20 is the horizon rather than a selected step and
        # no selection is being performed at all.
        seq = [point[f"fixed_{t}"] for t in FIXED_STEPS]
        d["impr_by_fixed_step"] = dict(zip(FIXED_STEPS, seq))
        d["impr_monotone_increasing_in_budget"] = bool(
            all(b > a for a, b in zip(seq, seq[1:])))
        d["fixed20_is_run_horizon"] = True   # meta.argv.steps == 20; asserted
        d["fixed20_relative_shortfall_vs_per_document_oracle"] = float(
            1.0 - point["fixed_20"] / point["oracle"]) if point["oracle"] else None

        out["domains"][dom] = d

        if audit is not None:
            a29 = audit["domains"][dom]
            max_alta_point_gap = max(
                max_alta_point_gap,
                abs(point["alta"] - a29["ppl_improvement_pooled"]))
            for kind in KINDS:
                for end in ("lo", "hi"):
                    max_alta_gap = max(
                        max_alta_gap,
                        abs(d["impr_ci"][kind]["alta"][end]
                            - a29["impr_ci"][kind][end]))

        cn = d["impr_ci"]["cluster_nested"]
        pr = d["paired_fixed20_minus_alta"]["cluster_nested"]
        print(f"[f32] {dom:9s} frozen ppl {d['frozen_ppl']:8.3f}  "
              f"alta {point['alta']:+.4f} [{cn['alta']['lo']:+.4f},"
              f"{cn['alta']['hi']:+.4f}]  "
              f"fixed20 {point['fixed_20']:+.4f} "
              f"[{cn['fixed_20']['lo']:+.4f},{cn['fixed_20']['hi']:+.4f}]  "
              f"paired {pr['point']:+.4f} [{pr['lo']:+.4f},{pr['hi']:+.4f}]"
              f"  mean t_hat {d['mean_t_hat']:.2f}", flush=True)

    # ------------------------------------------- rank robustness of Table T7
    # The article's per-domain Spearman correlations are computed against the
    # per-document gain AT THE SELECTOR'S INDEX.  Now that the fixed budget
    # carries the headline, the obvious question is whether the ranking result
    # depends on that choice.  Recompute both statistics against the fixed-20
    # gain and report the shift and the verdict count.  Nothing here replaces
    # a printed value; it bounds the sensitivity of one.
    rank = {}
    for dom in DOMAINS:
        al, fu, g_alta, g_f20 = [], [], [], []
        for doc, seeds in recs[dom].items():
            for r in seeds.values():
                s2 = r["sigma2_rel"] if r["sigma2_rel"] > 1e-12 else 1.0
                a, v2 = r["alpha"], r["delta_v2"]
                al.append(a * abs(a) / s2)
                fu.append(a * abs(a) * v2 / s2)
                g_alta.append(r["frozen_ce"] - r["alta_ce"])
                g_f20.append(r["frozen_ce"] - r["fixed_20_ce"])
        rank[dom] = {
            "rho_alignment_only_vs_alta_gain": F11.spearman(al, g_alta),
            "rho_alignment_only_vs_fixed20_gain": F11.spearman(al, g_f20),
            "rho_full_statistic_vs_alta_gain": F11.spearman(fu, g_alta),
            "rho_full_statistic_vs_fixed20_gain": F11.spearman(fu, g_f20),
        }
        rank[dom]["alignment_exceeds_full_at_fixed20"] = bool(
            rank[dom]["rho_alignment_only_vs_fixed20_gain"]
            > rank[dom]["rho_full_statistic_vs_fixed20_gain"])
    shifts = [abs(rank[d][f"rho_{s}_vs_fixed20_gain"]
                  - rank[d][f"rho_{s}_vs_alta_gain"])
              for d in DOMAINS
              for s in ("alignment_only", "full_statistic")]
    out["rank_robustness_to_gain_column"] = {
        "question": ("do the per-domain Spearman correlations of the article's "
                     "alignment table depend on the gain being taken at the "
                     "retrospective selector index rather than at the fixed "
                     "budget?"),
        "by_domain": rank,
        "max_abs_rho_shift": float(max(shifts)),
        "alignment_exceeds_full_at_fixed20_in_n_of_4": int(sum(
            rank[d]["alignment_exceeds_full_at_fixed20"] for d in DOMAINS)),
        "note": ("pooled-row Spearman, the article's own estimand; this bounds "
                 "the sensitivity of a printed value and replaces none"),
    }

    # ------------------------------------------------------------- verdicts
    cn = "cluster_nested"
    sa = "cluster_seedavg"
    out["verdict"] = {
        "fixed20_positive_point_estimate_in_n_of_4": int(sum(
            out["domains"][x]["impr_point"]["fixed_20"] > 0 for x in DOMAINS)),
        "fixed20_clustered_interval_excludes_zero_in_n_of_4": int(sum(
            out["domains"][x]["impr_ci"][cn]["fixed_20"]
            ["excludes_zero_positive"] for x in DOMAINS)),
        "fixed20_seedavg_interval_excludes_zero_in_n_of_4": int(sum(
            out["domains"][x]["impr_ci"][sa]["fixed_20"]
            ["excludes_zero_positive"] for x in DOMAINS)),
        "alta_clustered_interval_excludes_zero_in_n_of_4": int(sum(
            out["domains"][x]["impr_ci"][cn]["alta"]
            ["excludes_zero_positive"] for x in DOMAINS)),
        "fixed20_beats_alta_pointwise_in_n_of_4": int(sum(
            out["domains"][x]["impr_point"]["fixed_20"]
            > out["domains"][x]["impr_point"]["alta"] for x in DOMAINS)),
        "paired_favours_fixed20_excluding_zero_in_n_of_4": int(sum(
            out["domains"][x]["paired_fixed20_minus_alta"][cn]
            ["excludes_zero_favouring_fixed20"] for x in DOMAINS)),
        "best_fixed_step_by_domain": {
            x: out["domains"][x]["best_fixed_step"] for x in DOMAINS},
        "impr_monotone_in_budget_in_n_of_4": int(sum(
            out["domains"][x]["impr_monotone_increasing_in_budget"]
            for x in DOMAINS)),
        "fixed20_relative_shortfall_vs_oracle_by_domain": {
            x: out["domains"][x]["fixed20_relative_shortfall_vs_per_document_oracle"]
            for x in DOMAINS},
        "mean_t_hat_by_domain": {
            x: out["domains"][x]["mean_t_hat"] for x in DOMAINS},
        "alta_relative_shortfall_vs_fixed20_by_domain": {
            x: out["domains"][x]["alta_relative_shortfall_vs_fixed20"]
            for x in DOMAINS},
    }

    if audit is not None:
        out["audit_vs_f29"] = {
            "max_alta_point_gap": max_alta_point_gap,
            "max_alta_endpoint_gap_vs_f29": max_alta_gap,
            "note": ("the alta arm is recomputed here on this script's own "
                     "draws; a gap of Monte Carlo zero proves the draws are "
                     "f29's draws, hence the paired difference is exact"),
        }
        assert max_alta_point_gap <= 1e-12, (
            f"alta point estimate moved ({max_alta_point_gap:.3e}); the record "
            f"set differs from f11/f29's")
        assert max_alta_gap <= 1e-12, (
            f"the alta arm does not reproduce f29's endpoints (max gap "
            f"{max_alta_gap:.3e}); the RNG call sequence is not f11's, so the "
            f"paired fixed-20-minus-alta difference is not computed on one "
            f"common set of draws")
        print(f"[f32] audit vs f29: alta point gap {max_alta_point_gap:.2e}, "
              f"alta endpoint gap {max_alta_gap:.2e}", flush=True)

    v = out["verdict"]
    rr = out["rank_robustness_to_gain_column"]
    print(f"[f32] rank robustness: recomputing the alignment table's Spearman "
          f"correlations against the fixed-20 gain instead of the selector's "
          f"moves no value by more than {rr['max_abs_rho_shift']:.4f}, and the "
          f"alignment-only statistic still exceeds the full statistic in "
          f"{rr['alignment_exceeds_full_at_fixed20_in_n_of_4']}/4 domains.",
          flush=True)
    print(f"[f32] VERDICT  fixed t=20 interval excludes zero (positive) in "
          f"{v['fixed20_clustered_interval_excludes_zero_in_n_of_4']}/4 "
          f"domains (nested), "
          f"{v['fixed20_seedavg_interval_excludes_zero_in_n_of_4']}/4 "
          f"(seed-averaged); alta in "
          f"{v['alta_clustered_interval_excludes_zero_in_n_of_4']}/4; "
          f"paired favours fixed 20 in "
          f"{v['paired_favours_fixed20_excluding_zero_in_n_of_4']}/4",
          flush=True)

    C.save(out, args.out_name)
    print("[f32] DONE", flush=True)


if __name__ == "__main__":
    main()
