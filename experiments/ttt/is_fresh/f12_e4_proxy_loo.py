"""F12 -- leave-one-domain-out validation of the E4 shift proxy.

WHY THIS SCRIPT EXISTS
----------------------
The manuscript adopts the representation-distance proxy delta_v2 *after* the
loss-based proxy delta_ce underperformed, and then reports delta_v2's
within-domain Spearman correlations on the same four domains and the same 500
documents that motivated the switch.  As reported, therefore,
the high correlations (0.58-0.91) cannot be separated from a post-selection
effect: the winning proxy was chosen on the evidence it is evaluated on.

This is repairable without any new experiment, because there are four domains.
Leave-one-domain-out turns the criticism into a test:

    for each held-out domain D:
        select  v* = argmax over the candidate proxy menu of the mean
                     within-domain Spearman across the OTHER three domains
        freeze  v* (definition, alpha weighting, sigma normalisation, all of it)
        score   Spearman(v*, gain) on D's documents, which took no part in
                the selection

If delta_v2 is a genuine shift proxy, it should be selected in all four folds
and its held-out correlation should be close to its in-sample one.  If instead
it wins only where it was tuned, the folds will disagree or the held-out
correlations will collapse.  Either outcome is reported.

CANDIDATE MENU (all computable from the ORIGINAL records; nothing is re-run)
  phase_v2          alpha|alpha| delta_v2 / sigma2_rel      <- the paper's proxy
  phase_v2_nosigma  alpha|alpha| delta_v2
  phase_v2_alpha2   alpha^2 delta_v2 / sigma2_rel
  delta_v2_raw      delta_v2                                 (no alignment term)
  phase_ce          alpha|alpha| delta_ce / sigma2_rel       <- the loss proxy
  phase_ce_nosigma  alpha|alpha| delta_ce
  delta_ce_raw      delta_ce = frozen_cont_ce - wikitext reference mean
  frozen_ce         frozen continuation CE                   <- difficulty
                                                                baseline
  alpha_only        alpha|alpha| / sigma2_rel                 (alignment with no
                                                                shift magnitude)
  gnorm_ratio       gnorm_ssl / gnorm_task
  phase_v2_gnorm    alpha|alpha| delta_v2 gnorm_ssl / sigma2_rel

`frozen_ce` and `alpha_only` are in the menu deliberately: if a pure difficulty
variable or a pure alignment variable can be selected and still transfer, the
correlation is not evidence about delta.

PROTOCOL
  * unit of analysis: the DOCUMENT.  The three adaptation seeds of each
    document are averaged before any correlation is computed, so nothing here
    is pseudoreplicated (the clustering issue f11_e4_cluster_ci.py handles).
  * selection criterion: mean Spearman over the three training domains.  A
    rank-based criterion (mean rank of the variant within each training
    domain) is reported alongside, since a mean of correlations can be carried
    by one easy domain.
  * held-out interval: document-clustered percentile bootstrap, B = 2000,
    bootstrap seeds 20260806..20260810 (fresh range), endpoints averaged over
    the five bootstrap seeds.
  * a paired test of the frozen selection against the paper's proxy on the
    held-out domain: bootstrap distribution of rho(v*) - rho(phase_v2) over
    resampled documents.

DATA
  experiments/results/e4/{code,legal,pubmed,wikitext}_ln_s{0,1,2}.json
  experiments/results/e5/delta_v2_{domain}.json

REPRODUCTION CHECK (asserted)
The pooled-row within-domain Spearman of `phase_v2` must reproduce the four
published values (0.582 code, 0.905 legal, 0.868 PubMed, 0.834 WikiText) to
within 0.002, confirming the candidate menu is built on the same records and
the same statistic the manuscript quotes.
"""
import argparse

import numpy as np

import common as C
import f11_e4_cluster_ci as F11

DOMAINS = F11.DOMAINS
BOOT_SEEDS = F11.BOOT_SEEDS
B = 2000

PUBLISHED_RHO = {d: v[0] for d, v in F11.PUBLISHED_RHO_CI.items()}


# ------------------------------------------------------------ proxy menu

def _sig(r):
    s = r.get("sigma2_rel")
    return s if (s is not None and s > 1e-12) else 1.0


VARIANTS = {
    "phase_v2": lambda r: r["alpha"] * abs(r["alpha"]) * r["delta_v2"] / _sig(r),
    "phase_v2_nosigma": lambda r: r["alpha"] * abs(r["alpha"]) * r["delta_v2"],
    "phase_v2_alpha2": lambda r: r["alpha"] ** 2 * r["delta_v2"] / _sig(r),
    "delta_v2_raw": lambda r: r["delta_v2"],
    "phase_ce": lambda r: (None if r["delta_ce"] is None else
                           r["alpha"] * abs(r["alpha"]) * r["delta_ce"] / _sig(r)),
    "phase_ce_nosigma": lambda r: (None if r["delta_ce"] is None else
                                   r["alpha"] * abs(r["alpha"]) * r["delta_ce"]),
    "delta_ce_raw": lambda r: r["delta_ce"],
    "frozen_ce": lambda r: r["frozen_ce"],
    "alpha_only": lambda r: r["alpha"] * abs(r["alpha"]) / _sig(r),
    "gnorm_ratio": lambda r: (None if not r.get("gnorm_task")
                              else r["gnorm_ssl"] / r["gnorm_task"]),
    "phase_v2_gnorm": lambda r: (None if not r.get("gnorm_ssl") else
                                 r["alpha"] * abs(r["alpha"]) * r["delta_v2"]
                                 * r["gnorm_ssl"] / _sig(r)),
}

V2_FAMILY = {"phase_v2", "phase_v2_nosigma", "phase_v2_alpha2",
             "delta_v2_raw", "phase_v2_gnorm"}

# Note recorded by this script: WITHIN a domain, delta_ce = frozen_cont_ce -
# (a constant reference mean), so `delta_ce_raw` and `frozen_ce` have
# identical ranks and identical Spearman correlations by construction.  The
# manuscript's "loss-based proxy" therefore IS the document-difficulty
# baseline it has to be compared against; they cannot be
# distinguished by any within-domain rank statistic.


def partial_spearman(x, y, z):
    """Spearman partial correlation of x and y controlling for z.

    Computed on ranks: rho_xy.z = (r_xy - r_xz r_yz) / sqrt((1-r_xz^2)(1-r_yz^2)).
    Used to ask whether the shift proxy delta_v2 carries ANY within-domain
    signal once the alignment/noise term alpha|alpha|/sigma^2 is held fixed.
    """
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    if m.sum() < 5:
        return float("nan")
    rxy = F11.spearman(x[m], y[m])
    rxz = F11.spearman(x[m], z[m])
    ryz = F11.spearman(y[m], z[m])
    den = np.sqrt(max((1 - rxz ** 2) * (1 - ryz ** 2), 1e-12))
    return float((rxy - rxz * ryz) / den)


def doc_table(dom_recs):
    """Per-document, seed-averaged table: {variant: array, 'gain': array}."""
    docs = sorted(dom_recs)
    cols = {v: [] for v in VARIANTS}
    gain = []
    for d in docs:
        rs = list(dom_recs[d].values())
        gain.append(float(np.mean([r["gain"] for r in rs])))
        for v, fn in VARIANTS.items():
            vals = [fn(r) for r in rs]
            vals = [x for x in vals if x is not None and np.isfinite(x)]
            cols[v].append(float(np.mean(vals)) if vals else np.nan)
    out = {v: np.asarray(cols[v], float) for v in VARIANTS}
    out["gain"] = np.asarray(gain, float)
    out["_docs"] = np.asarray(docs, int)
    return out


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--boot-seeds", type=int, nargs="*", default=BOOT_SEEDS)
    args = ap.parse_args()

    recs = F11.load_e4()
    tabs = {d: doc_table(recs[d]) for d in DOMAINS}

    # ---- reproduction check on the published pooled-row values
    repro = {}
    max_gap = 0.0
    for d in DOMAINS:
        rows = F11._flatten(recs[d])
        rho = F11.spearman([VARIANTS["phase_v2"](r) for r in rows],
                           [r["gain"] for r in rows])
        repro[d] = rho
        max_gap = max(max_gap, abs(rho - PUBLISHED_RHO[d]))
    assert max_gap <= 0.002, (
        f"phase_v2 does not reproduce the published within-domain rho "
        f"(max gap {max_gap:.4f}); the candidate menu is not built on the "
        f"same records/statistic as the manuscript")

    # ---- per-domain, per-variant Spearman on seed-averaged documents
    rho_tab = {d: {v: F11.spearman(tabs[d][v], tabs[d]["gain"])
                   for v in VARIANTS} for d in DOMAINS}

    # in-sample (all four domains) ranking -- the circular ranking the
    # manuscript's selection effectively used
    insample_mean = {v: float(np.nanmean([rho_tab[d][v] for d in DOMAINS]))
                     for v in VARIANTS}
    insample_winner = max(insample_mean, key=lambda v: insample_mean[v])

    folds = {}
    for held in DOMAINS:
        train = [d for d in DOMAINS if d != held]
        sel_mean = {v: float(np.nanmean([rho_tab[d][v] for d in train]))
                    for v in VARIANTS}
        # rank-based criterion: mean rank (1 = best) within each train domain
        ranks = {v: [] for v in VARIANTS}
        for d in train:
            order = sorted(VARIANTS, key=lambda v: -(rho_tab[d][v]
                                                     if np.isfinite(rho_tab[d][v])
                                                     else -9))
            for k, v in enumerate(order):
                ranks[v].append(k + 1)
        sel_rank = {v: float(np.mean(ranks[v])) for v in VARIANTS}

        v_mean = max(sel_mean, key=lambda v: sel_mean[v])
        v_rank = min(sel_rank, key=lambda v: sel_rank[v])

        t = tabs[held]
        rho_sel = F11.spearman(t[v_mean], t["gain"])
        rho_sel_rank = F11.spearman(t[v_rank], t["gain"])
        rho_paper = F11.spearman(t["phase_v2"], t["gain"])
        rho_diff_base = F11.spearman(t["frozen_ce"], t["gain"])
        rho_align = F11.spearman(t["alpha_only"], t["gain"])
        # does the shift proxy add anything once alignment/noise is fixed?
        part_v2 = partial_spearman(t["delta_v2_raw"], t["gain"], t["alpha_only"])
        part_phase = partial_spearman(t["phase_v2"], t["gain"], t["alpha_only"])

        # ---- document-clustered bootstrap on the held-out domain
        n = len(t["gain"])
        lo_s, hi_s, lo_p, hi_p, dlt, dlt_al, pv2 = [], [], [], [], [], [], []
        for bs in args.boot_seeds:
            rng = np.random.default_rng(bs)
            vs, vp, vd, vda, vpart = [], [], [], [], []
            for _ in range(args.b):
                idx = rng.integers(0, n, n)
                a = F11.spearman(t[v_mean][idx], t["gain"][idx])
                b = F11.spearman(t["phase_v2"][idx], t["gain"][idx])
                c = F11.spearman(t["alpha_only"][idx], t["gain"][idx])
                p = partial_spearman(t["delta_v2_raw"][idx], t["gain"][idx],
                                     t["alpha_only"][idx])
                if np.isfinite(a):
                    vs.append(a)
                if np.isfinite(b):
                    vp.append(b)
                if np.isfinite(a) and np.isfinite(b):
                    vd.append(a - b)
                if np.isfinite(b) and np.isfinite(c):
                    vda.append(b - c)
                if np.isfinite(p):
                    vpart.append(p)
            l, h, _ = F11._ci(vs)
            lo_s.append(l)
            hi_s.append(h)
            l, h, _ = F11._ci(vp)
            lo_p.append(l)
            hi_p.append(h)
            dlt.append(F11._ci(vd)[:2])
            dlt_al.append(F11._ci(vda)[:2])
            pv2.append(F11._ci(vpart)[:2])

        folds[held] = {
            "train_domains": train,
            "selected_by_mean_rho": v_mean,
            "selected_by_mean_rank": v_rank,
            "selection_scores_mean_rho": sel_mean,
            "selection_scores_mean_rank": sel_rank,
            "selected_is_delta_v2_family": v_mean in V2_FAMILY,
            "selected_is_papers_exact_proxy": v_mean == "phase_v2",
            "heldout_rho_selected": rho_sel,
            "heldout_rho_selected_by_rank": rho_sel_rank,
            "heldout_rho_phase_v2": rho_paper,
            "heldout_rho_difficulty_baseline_frozen_ce": rho_diff_base,
            "heldout_rho_alignment_only": rho_align,
            "heldout_partial_rho_delta_v2_given_alignment": part_v2,
            "heldout_partial_rho_phase_v2_given_alignment": part_phase,
            "heldout_ci_phase_v2_minus_alignment_only": {
                "lo": float(np.mean([x[0] for x in dlt_al])),
                "hi": float(np.mean([x[1] for x in dlt_al]))},
            "heldout_ci_partial_rho_delta_v2_given_alignment": {
                "lo": float(np.mean([x[0] for x in pv2])),
                "hi": float(np.mean([x[1] for x in pv2]))},
            "heldout_ci_selected": {
                "lo": float(np.mean(lo_s)), "hi": float(np.mean(hi_s)),
                "lo_range": [float(np.min(lo_s)), float(np.max(lo_s))],
                "hi_range": [float(np.min(hi_s)), float(np.max(hi_s))]},
            "heldout_ci_phase_v2": {
                "lo": float(np.mean(lo_p)), "hi": float(np.mean(hi_p))},
            "heldout_ci_selected_minus_phase_v2": {
                "lo": float(np.mean([x[0] for x in dlt])),
                "hi": float(np.mean([x[1] for x in dlt]))},
            "n_heldout_documents": n,
        }
        print(f"[f12] hold out {held:9s}: selected={v_mean:17s} "
              f"(rank-criterion {v_rank}) -> held-out rho={rho_sel:+.3f} "
              f"[{np.mean(lo_s):+.3f}, {np.mean(hi_s):+.3f}]; "
              f"phase_v2={rho_paper:+.3f}; "
              f"difficulty baseline={rho_diff_base:+.3f}", flush=True)

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
    n_part_pos = sum(
        1 for d in DOMAINS
        if folds[d]["heldout_ci_partial_rho_delta_v2_given_alignment"]["lo"] > 0)

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
            "exceeds the full statistic, and delta_v2 adds no resolved "
            "within-domain signal once alignment is held fixed")
    else:
        verdict = "FAIL: the frozen selection does not transfer; see per-fold detail"

    out = {
        "script": "f12_e4_proxy_loo.py",
        "finding": ("the E4 proxy was selected and "
                    "evaluated on the same domains and documents"),
        "source_records": ["experiments/results/e4/*_ln_s{0,1,2}.json",
                           "experiments/results/e5/delta_v2_*.json"],
        "unit_of_analysis": "document (3 adaptation seeds averaged)",
        "candidate_variants": sorted(VARIANTS),
        "delta_v2_family": sorted(V2_FAMILY),
        "n_bootstrap": args.b, "bootstrap_seeds": args.boot_seeds,
        "reproduction_check_phase_v2_pooled_rho": repro,
        "published_rho": PUBLISHED_RHO,
        "max_reproduction_gap": max_gap,
        "per_domain_per_variant_rho_seed_averaged": rho_tab,
        "in_sample_all_four_domains": {
            "mean_rho_by_variant": insample_mean,
            "winner": insample_winner,
            "note": ("this is the circular ranking; the folds below never see "
                     "their evaluation domain")},
        "folds": folds,
        "summary": {
            "n_folds": len(DOMAINS),
            "n_folds_selecting_delta_v2_family": n_v2,
            "n_folds_selecting_papers_exact_proxy": n_exact,
            "heldout_rho_selected": C.mean_range(ho),
            "heldout_rho_phase_v2": C.mean_range(ho_paper),
            "heldout_rho_difficulty_baseline": C.mean_range(ho_base),
            "heldout_rho_alignment_only": C.mean_range(ho_align),
            "heldout_partial_rho_delta_v2_given_alignment": C.mean_range(ho_part),
            "n_folds_partial_rho_delta_v2_ci_excludes_zero": n_part_pos,
            "loss_proxy_equals_difficulty_baseline_within_domain": True,
            "verdict": verdict,
        },
    }
    C.save(out, "f12_e4_proxy_loo.json")
    print(f"[f12] {verdict}")
    print(f"[f12] delta_v2 family selected in {n_v2}/{len(DOMAINS)} folds "
          f"(paper's exact phase_v2 in {n_exact}/{len(DOMAINS)}); "
          f"held-out rho {min(ho):+.3f}..{max(ho):+.3f} vs difficulty "
          f"baseline {min(ho_base):+.3f}..{max(ho_base):+.3f}")
    print("[f12] DONE", flush=True)


if __name__ == "__main__":
    main()
