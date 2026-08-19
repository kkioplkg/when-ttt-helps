"""F11 -- document-clustered confidence intervals for the E4 (GPT-2) headline
correlations and perplexity improvements.

WHY THIS SCRIPT EXISTS
----------------------
`figures/scripts/bootstrap_ci.py:e4_cis` pools the E4 records of the three
adaptation seeds into one list and then resamples that list i.i.d.:

    rows = recs[dom]                 # 500 documents x 3 seeds = 1500 rows
    idx  = RNG.integers(0, n, n)     # i.i.d. resample of 1500 rows

The 1500 rows are not 1500 independent units.  The same 500 documents appear
three times each -- the adaptation seed only re-randomises the SSL gradient
noise, while the document (and therefore both the phase statistic
alpha|alpha|delta_v2/sigma^2 and most of the gain) is held fixed.  Resampling
rows rather than documents therefore treats each document as if it carried
three times its true information, and the published intervals
([0.55,0.62] code, [0.89,0.92] legal, [0.85,0.88] PubMed, [0.81,0.85]
WikiText) are correspondingly too narrow.  The point estimates are unaffected.

WHAT THIS SCRIPT COMPUTES INSTEAD
Three interval constructions, side by side, on the SAME original records:

  naive_iid_rows     the published construction, reproduced exactly, so the
                     old and new numbers are comparable and the reproduction
                     check below is meaningful;
  cluster_nested     resample the 500 unique DOCUMENTS with replacement and
                     carry all three seed rows of each drawn document with it
                     (seeds stay nested inside the document);
  cluster_seedavg    resample the 500 unique documents and use the
                     seed-averaged statistic and gain for each -- 500 rows,
                     one per independent unit.

`cluster_nested` is the primary corrected interval: it keeps the paper's
estimand (the pooled-row Spearman) and only fixes the resampling unit.
`cluster_seedavg` is reported alongside because it changes the estimand to a
per-document one, which is what the domain-level generalisation claim is
actually about.

Also reported per domain:
  n_docs, n_seeds, n_rows                     (the counts that make the
                                               resampling unit unambiguous)
  design_effect = (clustered width / naive width)
  rho_by_seed                                 (the three single-seed values;
                                               a direct check that the seed is
                                               a nuisance dimension)
  within_document_seed_agreement              mean over documents of the
                                               across-seed spread of the gain,
                                               relative to the between-document
                                               spread -- the quantity that makes
                                               the pseudoreplication concrete.

DATA (original records only; nothing is re-run)
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json   (the delta_v2 proxy join the
                                                   paper already uses)

PROTOCOL
  * statistic: Spearman rho between the per-document phase statistic
    ph = alpha * |alpha| * delta_v2 / sigma2_rel  and the per-document gain
    at the ALTA stop  (frozen_cont_ce - alta_cont_ce).  Identical to
    bootstrap_ci.py:e4_records, so only the resampling unit changes.
  * perplexity improvement: exp(mean frozen_cont_ce) - exp(mean alta_cont_ce),
    identical to the published `impr_stat`.
  * B = 2000 resamples, percentile 2.5 / 97.5.
  * bootstrap RNG seeds 20260806..20260810 (fresh range); the interval is
    reported as the mean endpoint over the five bootstrap seeds together with
    the across-seed endpoint range, so no interval depends on one RNG draw.

REPRODUCTION CHECK (asserted)
The `naive_iid_rows` interval must reproduce the published one to within
0.02 in each endpoint for all four domains, confirming that this script reads
the same records through the same statistic and that the widening seen in
`cluster_nested` is caused only by the change of resampling unit.
"""
import argparse
import glob
import json
import math
import os

import numpy as np

import common as C

_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "results"))
E4_DIR = os.path.join(RESULTS_ROOT, "e4")
E5_DIR = os.path.join(RESULTS_ROOT, "e5")

BOOT_SEEDS = [20260806, 20260807, 20260808, 20260809, 20260810]
B = 2000
DOMAINS = ["code", "legal", "pubmed", "wikitext"]

# published intervals, sections/experiments.tex (E4 paragraph) --
# the object of the reproduction check, not an input to any computation
PUBLISHED_RHO_CI = {
    "code": (0.582, 0.55, 0.62),
    "legal": (0.905, 0.89, 0.92),
    "pubmed": (0.868, 0.85, 0.88),
    "wikitext": (0.834, 0.81, 0.85),
}


# ----------------------------------------------------------------- loading

def load_delta_v2():
    out = {}
    for p in sorted(glob.glob(os.path.join(E5_DIR, "delta_v2_*.json"))):
        o = json.loads(open(p, encoding="utf-8").read())
        dom = o.get("domain") or os.path.basename(p)[8:-5]
        out[dom] = {int(r["doc"]): float(r["delta_v2"]) for r in o["records"]}
    return out


def load_e4(dv2=None):
    """domain -> doc -> seed -> record dict.

    Fields kept: phase_v2, gain (frozen - alta CE), frozen_ce, alta_ce,
    alpha, sigma2_rel, delta_v2, delta_ce (the loss proxy), gnorm_ssl,
    gnorm_task, t_hat, oracle/fixed CEs.
    """
    dv2 = load_delta_v2() if dv2 is None else dv2
    out = {}
    for p in sorted(glob.glob(os.path.join(E4_DIR, "*_ln_s*.json"))):
        o = json.loads(open(p, encoding="utf-8").read())
        dom = o["meta"]["argv"]["domain"]
        seed = int(o["meta"]["argv"]["seed"])
        dmap = dv2.get(dom, {})
        for r in o["records"]:
            if not r.get("alta"):
                continue
            a, s2 = r.get("alpha"), r.get("sigma2_rel")
            doc = int(r["doc"])
            v2 = dmap.get(doc)
            if a is None or v2 is None:
                continue
            ph = a * abs(a) * v2
            if s2 is not None and s2 > 1e-12:
                ph = ph / s2
            out.setdefault(dom, {}).setdefault(doc, {})[seed] = {
                "doc": doc, "seed": seed,
                "alpha": float(a), "sigma2_rel": float(s2),
                "delta_v2": float(v2),
                "delta_ce": (float(r["delta_proxy"])
                             if r.get("delta_proxy") is not None else None),
                "gnorm_ssl": r.get("gnorm_ssl"),
                "gnorm_task": r.get("gnorm_task"),
                "phase_v2": float(ph),
                "frozen_ce": float(r["frozen_cont_ce"]),
                "alta_ce": float(r["alta"]["cont_ce"]),
                "gain": float(r["frozen_cont_ce"] - r["alta"]["cont_ce"]),
                "t_hat": r["alta"].get("t_hat"),
            }
    return out


# --------------------------------------------------------------- statistics

def _rank(x):
    x = np.asarray(x, float)
    order = x.argsort(kind="stable")
    ranks = np.empty(len(x), float)
    ranks[order] = np.arange(len(x), dtype=float)
    # average ties
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    if (cnt > 1).any():
        sums = np.zeros(len(cnt))
        np.add.at(sums, inv, ranks)
        ranks = (sums / cnt)[inv]
    return ranks


def spearman(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return float("nan")
    rx, ry = _rank(x), _rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def ppl_improvement(frozen, alta):
    return (math.exp(float(np.mean(frozen))) - math.exp(float(np.mean(alta))))


# --------------------------------------------------------------- bootstraps

def _flatten(dom_recs, docs=None):
    docs = sorted(dom_recs) if docs is None else docs
    rows = []
    for d in docs:
        rows.extend(dom_recs[d][s] for s in sorted(dom_recs[d]))
    return rows


def _seedavg(dom_recs, docs=None):
    docs = sorted(dom_recs) if docs is None else docs
    out = []
    for d in docs:
        rs = list(dom_recs[d].values())
        out.append({
            "phase_v2": float(np.mean([r["phase_v2"] for r in rs])),
            "gain": float(np.mean([r["gain"] for r in rs])),
            "frozen_ce": float(np.mean([r["frozen_ce"] for r in rs])),
            "alta_ce": float(np.mean([r["alta_ce"] for r in rs])),
        })
    return out


def _ci(vals):
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    lo, hi = np.percentile(v, [2.5, 97.5])
    return float(lo), float(hi), int(len(v))


def bootstrap_domain(dom_recs, boot_seed, b=B):
    """Returns dict of interval-construction -> (rho_ci, impr_ci)."""
    rng = np.random.default_rng(boot_seed)
    docs = sorted(dom_recs)
    rows = _flatten(dom_recs, docs)
    n_rows, n_docs = len(rows), len(docs)
    avg = _seedavg(dom_recs, docs)

    ph_rows = np.array([r["phase_v2"] for r in rows])
    gn_rows = np.array([r["gain"] for r in rows])
    fz_rows = np.array([r["frozen_ce"] for r in rows])
    al_rows = np.array([r["alta_ce"] for r in rows])

    # index of the rows belonging to each document (seeds nested)
    by_doc = {}
    for i, r in enumerate(rows):
        by_doc.setdefault(r["doc"], []).append(i)
    doc_blocks = [np.asarray(by_doc[d], int) for d in docs]

    ph_avg = np.array([r["phase_v2"] for r in avg])
    gn_avg = np.array([r["gain"] for r in avg])
    fz_avg = np.array([r["frozen_ce"] for r in avg])
    al_avg = np.array([r["alta_ce"] for r in avg])

    res = {}

    # (1) published construction: i.i.d. over the 1500 pooled rows
    rho_v, imp_v = [], []
    for _ in range(b):
        idx = rng.integers(0, n_rows, n_rows)
        rho_v.append(spearman(ph_rows[idx], gn_rows[idx]))
        imp_v.append(ppl_improvement(fz_rows[idx], al_rows[idx]))
    res["naive_iid_rows"] = {"rho_ci": _ci(rho_v), "impr_ci": _ci(imp_v),
                             "n_units": n_rows}

    # (2) clustered, seeds nested inside the resampled document
    rho_v, imp_v = [], []
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        idx = np.concatenate([doc_blocks[k] for k in pick])
        rho_v.append(spearman(ph_rows[idx], gn_rows[idx]))
        imp_v.append(ppl_improvement(fz_rows[idx], al_rows[idx]))
    res["cluster_nested"] = {"rho_ci": _ci(rho_v), "impr_ci": _ci(imp_v),
                             "n_units": n_docs}

    # (3) clustered, seeds averaged within document
    rho_v, imp_v = [], []
    for _ in range(b):
        pick = rng.integers(0, n_docs, n_docs)
        rho_v.append(spearman(ph_avg[pick], gn_avg[pick]))
        imp_v.append(ppl_improvement(fz_avg[pick], al_avg[pick]))
    res["cluster_seedavg"] = {"rho_ci": _ci(rho_v), "impr_ci": _ci(imp_v),
                              "n_units": n_docs}
    return res


def variance_decomposition(dom_recs):
    """Between-document vs within-document (across-seed) variance of the gain
    and of the phase statistic -- the size of the pseudoreplication problem."""
    out = {}
    for key in ("gain", "phase_v2"):
        per_doc = [np.asarray([r[key] for r in dom_recs[d].values()], float)
                   for d in sorted(dom_recs)]
        means = np.array([p.mean() for p in per_doc])
        within = np.array([p.var(ddof=1) if len(p) > 1 else 0.0
                           for p in per_doc])
        vb, vw = float(means.var(ddof=1)), float(within.mean())
        out[key] = {
            "between_document_var": vb, "within_document_var": vw,
            "icc": float(vb / (vb + vw)) if (vb + vw) > 0 else float("nan"),
        }
    return out


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    # see the note in f7_curve_match.py: a reduced verify run must not clobber
    # the archived record that fig_f8_domains.py and Sec. 5.4 read.
    ap.add_argument("--out-name", default="f11_e4_cluster_ci.json")
    args = ap.parse_args()

    recs = load_e4()
    assert set(recs) >= set(DOMAINS), f"missing domains: {set(DOMAINS)-set(recs)}"

    out = {
        "script": "f11_e4_cluster_ci.py",
        "finding": ("E4 intervals resampled 1500 pooled "
                    "rows i.i.d., but the 1500 rows are 500 documents x 3 "
                    "adaptation seeds"),
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "statistic": "spearman(alpha|alpha| delta_v2 / sigma2_rel, "
                     "frozen_cont_ce - alta_cont_ce)",
        "n_bootstrap": args.b, "bootstrap_seeds": args.boot_seeds,
        "published_intervals_checked_against": PUBLISHED_RHO_CI,
        "domains": {},
    }

    max_repro_gap = 0.0
    for dom in DOMAINS:
        dr = recs[dom]
        docs = sorted(dr)
        rows = _flatten(dr, docs)
        n_seeds = sorted({r["seed"] for r in rows})
        ph = np.array([r["phase_v2"] for r in rows])
        gn = np.array([r["gain"] for r in rows])
        fz = np.array([r["frozen_ce"] for r in rows])
        al = np.array([r["alta_ce"] for r in rows])
        avg = _seedavg(dr, docs)

        rho_pooled = spearman(ph, gn)
        rho_seedavg = spearman([r["phase_v2"] for r in avg],
                               [r["gain"] for r in avg])
        rho_by_seed = {}
        for s in n_seeds:
            sub = [r for r in rows if r["seed"] == s]
            rho_by_seed[str(s)] = spearman([r["phase_v2"] for r in sub],
                                           [r["gain"] for r in sub])
        impr_pooled = ppl_improvement(fz, al)

        per_boot = [bootstrap_domain(dr, bs, args.b) for bs in args.boot_seeds]

        def agg(kind, which):
            los = [p[kind][which][0] for p in per_boot]
            his = [p[kind][which][1] for p in per_boot]
            return {"lo": float(np.mean(los)), "hi": float(np.mean(his)),
                    "lo_range": [float(np.min(los)), float(np.max(los))],
                    "hi_range": [float(np.min(his)), float(np.max(his))],
                    "width": float(np.mean(his) - np.mean(los)),
                    "n_units": per_boot[0][kind]["n_units"]}

        d = {
            "n_documents": len(docs), "n_seeds": len(n_seeds),
            "n_rows": len(rows),
            "rho_pooled_rows": rho_pooled,
            "rho_seed_averaged": rho_seedavg,
            "rho_by_seed": rho_by_seed,
            "ppl_improvement_pooled": impr_pooled,
            "rho_ci": {k: agg(k, "rho_ci") for k in
                       ("naive_iid_rows", "cluster_nested", "cluster_seedavg")},
            "impr_ci": {k: agg(k, "impr_ci") for k in
                        ("naive_iid_rows", "cluster_nested", "cluster_seedavg")},
            "variance_decomposition": variance_decomposition(dr),
        }
        for k in ("cluster_nested", "cluster_seedavg"):
            d["rho_ci"][k]["design_effect_vs_naive"] = float(
                d["rho_ci"][k]["width"] / d["rho_ci"]["naive_iid_rows"]["width"])
            d["impr_ci"][k]["design_effect_vs_naive"] = float(
                d["impr_ci"][k]["width"]
                / max(d["impr_ci"]["naive_iid_rows"]["width"], 1e-12))
        out["domains"][dom] = d

        # ---- reproduction check against the published interval
        pr, plo, phi = PUBLISHED_RHO_CI[dom]
        nlo = d["rho_ci"]["naive_iid_rows"]["lo"]
        nhi = d["rho_ci"]["naive_iid_rows"]["hi"]
        gap = max(abs(nlo - plo), abs(nhi - phi), abs(rho_pooled - pr))
        max_repro_gap = max(max_repro_gap, gap)
        print(f"[f11] {dom:9s} rho={rho_pooled:+.3f} (published {pr:+.3f})\n"
              f"        naive  1500 rows  [{nlo:+.3f}, {nhi:+.3f}] "
              f"(published [{plo:+.3f}, {phi:+.3f}])\n"
              f"        nested  500 docs  "
              f"[{d['rho_ci']['cluster_nested']['lo']:+.3f}, "
              f"{d['rho_ci']['cluster_nested']['hi']:+.3f}]  "
              f"x{d['rho_ci']['cluster_nested']['design_effect_vs_naive']:.2f} "
              f"wider\n"
              f"        seedavg 500 docs  "
              f"[{d['rho_ci']['cluster_seedavg']['lo']:+.3f}, "
              f"{d['rho_ci']['cluster_seedavg']['hi']:+.3f}]  "
              f"rho_avg={rho_seedavg:+.3f}", flush=True)

    out["max_reproduction_gap_vs_published"] = max_repro_gap
    assert max_repro_gap <= 0.02, (
        f"the naive construction does not reproduce the published intervals "
        f"(max endpoint gap {max_repro_gap:.4f}); the records or the statistic "
        f"differ, so the clustered comparison would not be like-for-like")

    out["headline"] = {
        dom: {
            "rho": out["domains"][dom]["rho_pooled_rows"],
            "ci_published_pseudoreplicated": list(PUBLISHED_RHO_CI[dom][1:]),
            "ci_document_clustered": [
                out["domains"][dom]["rho_ci"]["cluster_nested"]["lo"],
                out["domains"][dom]["rho_ci"]["cluster_nested"]["hi"]],
            "n_documents": out["domains"][dom]["n_documents"],
            "n_rows": out["domains"][dom]["n_rows"],
        } for dom in DOMAINS}
    C.save(out, args.out_name)
    print("[f11] DONE", flush=True)


if __name__ == "__main__":
    main()
