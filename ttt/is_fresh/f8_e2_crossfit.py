"""F8 -- E2 rank correlations with a commissioning / evaluation cross-fit.

WHAT THE PAPER CLAIMS: the phase statistic "ranks per-cell gains with Spearman
rho of 0.686 (mean-final) ... and 0.694 (median-final) for ttt_mask, rising to
0.762/0.840 at the best step, and 0.622 (mean-final) / 0.742 (median-final) for
ttt_rot".

CLASSIFICATION: MEASURED, but SAME-SAMPLE. Two distinct problems, both in the
aggregation (analysis/aggregate.py), not in the data:

  (P1) Within each (dataset, method, corruption, severity) cell the phase
       statistic and the realized gain are computed from the SAME 128 (or 384,
       pooled over seeds) episodes. Any episode-level noise that moves both --
       and both are functions of the same forward/backward passes on the same
       images -- inflates the rank correlation between the cell means.
  (P2) The "best step" variant takes gain_best = max over t of the cell's mean
       gain, i.e. the step is selected on the very sample the gain is then
       reported from. That is a maximum of noisy quantities and is biased
       upward by construction; 0.762/0.840 are the numbers most affected.

Neither is repaired by more data; both are repaired by a split.

WHAT THIS SCRIPT DOES
Re-analyses the ORIGINAL E2 raw episode records (results/e2/*_main_*.json) and
the ORIGINAL E5 feature-shift files (results/e5/delta_feat_*.json) -- no new
model runs, no new adaptation code -- under a cross-fit:

    within each cell, a fresh-seed random permutation splits the episodes into
      COMMISSIONING share (fraction --commission, default 0.5)
      EVALUATION   share (the disjoint remainder)
    phase statistic  <- COMMISSIONING episodes only
    realized gain    <- EVALUATION episodes only
    best step t*     <- argmax of the COMMISSIONING mean gain, scored on
                        EVALUATION

then Spearman across cells within a method, exactly as the paper does.

Uncertainty is reported two ways:
  * across 5 fresh split seeds (20260801..20260805): mean and range;
  * corruption-clustered bootstrap (1000 resamples of the 15 corruptions with
    replacement, all severities of a sampled corruption travelling together),
    which is the right cluster because cells sharing a corruption share the
    same images, the same shift, and the same delta_feat reference.

The paper's own bootstrap resampled the 105 cells independently, which treats
the five severities of one corruption as five independent observations.

STATISTIC
Every proxy phase statistic is the manuscript's

    Phi = alpha_sgn |alpha_sgn| delta_proxy / sigma^2_rel                    (*)

with the SIGNED alignment factor alpha_sgn|alpha_sgn| (Appendix C.1).  Two
instances are computed:

    phase_feat  delta_proxy = delta_feat, joined per (corruption, severity,
                idx) from the E5 files and the source model of each method
                (resnet26ttt for ttt_*, wrn2810 for tent/pl);
    phase_loss  delta_proxy = the loss-based shift proxy carried in the
                episode record.

ZERO GRADIENT-NOISE CONVENTION (declared, not a fallback)
For the deterministic objectives (tent, pseudo-label) at N = 1 the only source
of gradient noise is batch composition, so sigma^2_rel vanishes IDENTICALLY:
all 32,640 tent and 28,800 pseudo-label episode records in results/e2/ carry
sigma2_rel == 0 exactly, and all 11,520 records of the ResNet-26+GN entropy run
do too.  Equation (*) is then a 0-denominator expression and has no value.  It
does, however, have a well-defined RANK limit, and ranks are the only thing the
analysis consumes (Spearman within an arm).  Because sigma^2_rel is constant
across every episode of such an arm,

    rank( Phi ) = rank( alpha_sgn |alpha_sgn| delta_proxy / s )  for any s > 0
                = rank( alpha_sgn |alpha_sgn| delta_proxy ),

so lim_{s -> 0+} of the ranking induced by (*) is the ranking induced by the
numerator alone.  We therefore DEFINE the statistic on a zero-noise arm to be

    Phi_0 = alpha_sgn |alpha_sgn| delta_proxy                              (**)

and say so in the manuscript.  This is a definition, not a silent branch: the
loader asserts that sigma^2_rel is either strictly positive for EVERY episode
of an arm or exactly zero for every episode of it, so (*) and (**) are never
mixed inside one rank correlation.  A mixed arm raises.

A second, coarser statistic is carried alongside as a robustness check:

    phase_align = alpha_sgn |alpha_sgn|                                   (***)

the alignment factor alone, which is well defined at every sigma^2 and is the
statistic E4 (f17) found to be the stronger predictor across GPT-2 domains.

AUDIT KEY (not a result)
`phase_loss_unsigned` = alpha^2 delta_proxy / sigma^2_rel reproduces the
pre-correction implementation, which dropped the sign of the alignment factor
by writing `alpha**2` where the manuscript's definition has
`alpha*|alpha|`.  It exists only so the archived f8b/f16/f20 JSONs remain
mechanically reproducible; nothing in the manuscript is computed from it.

REPRODUCTION CHECK (asserted)
Run with --commission 1.0 (no split, statistic and gain both from all
episodes, best step selected in sample) this script must reproduce the
published same-sample numbers for ttt_mask and ttt_rot to within 0.02
Spearman. The assertion runs automatically before the cross-fit.
"""
import argparse
import json
import os
import re

import numpy as np

import common as C

E2_DIR = os.path.join(os.path.dirname(C.RESULTS_DIR), "e2")
E5_DIR = os.path.join(os.path.dirname(C.RESULTS_DIR), "e5")
EPS_SIGMA = 1e-12
METHOD_ARCH = {"ttt_rot": "resnet26ttt", "ttt_mask": "resnet26ttt",
               "tent": "wrn2810", "pl": "wrn2810"}
STOCHASTIC = ("ttt_mask", "ttt_rot")
# published same-sample values (EXPERIMENT_RESULTS.md l.105-106), used only by
# the reproduction check
PUBLISHED = {("ttt_mask", "mean_final"): 0.686,
             ("ttt_mask", "median_final"): 0.694,
             ("ttt_mask", "mean_best"): 0.762,
             ("ttt_mask", "median_best"): 0.840,
             ("ttt_rot", "mean_final"): 0.622,
             ("ttt_rot", "median_final"): 0.742}


# ------------------------------------------------------------------ statistic

def phase_value(alpha, delta_proxy, sigma2_rel, signed=True):
    """The manuscript's proxy phase statistic for ONE episode.

    Returns (value, zero_noise) where `zero_noise` is True when the declared
    sigma^2 -> 0 limit (**) was used instead of the ratio (*).  `signed=False`
    selects the pre-correction unsigned numerator alpha^2 delta_proxy and
    exists only for the audit-trail reproduction check.
    """
    if alpha is None or delta_proxy is None:
        return None, None
    a, d = float(alpha), float(delta_proxy)
    align = a * abs(a) if signed else a ** 2
    if sigma2_rel is None:
        return None, None
    s2 = float(sigma2_rel)
    if s2 > EPS_SIGMA:
        return align * d / s2, False
    return align * d, True          # (**) declared zero-noise rank limit


def alignment_value(alpha):
    """(***) the alignment factor alone; defined at every sigma^2."""
    if alpha is None:
        return None
    a = float(alpha)
    return a * abs(a)


def _episode_stats(a, s2, delta_feat, delta_loss):
    """All statistic keys for one episode, plus the zero-noise flags."""
    pf, zf = phase_value(a, delta_feat, s2)
    pl, zl = phase_value(a, delta_loss, s2)
    plu, _ = phase_value(a, delta_loss, s2, signed=False)
    return {"phase_feat": pf, "phase_loss": pl,
            "phase_loss_unsigned": plu,
            "phase_align": alignment_value(a),
            "_zero_noise": zl if zl is not None else zf}


def assert_noise_homogeneous(cells):
    """(*) and (**) must never be mixed inside one rank correlation.

    Raises unless, for every (dataset, method) arm, sigma^2_rel is either
    strictly positive for every episode or exactly zero for every episode.
    """
    by_arm = {}
    for (ds, meth, _c, _s), eps in cells.items():
        seen = by_arm.setdefault((ds, meth), set())
        for e in eps:
            if e["_zero_noise"] is not None:
                seen.add(bool(e["_zero_noise"]))
    bad = {k: v for k, v in by_arm.items() if len(v) > 1}
    if bad:
        raise ValueError(
            "sigma^2_rel is zero for some episodes and positive for others "
            f"within these arms: {sorted(bad)}.  The ratio statistic (*) and "
            "its zero-noise limit (**) are on different scales and must not "
            "be ranked against each other; fix the records or split the arm.")
    return {f"{ds}/{meth}": ("zero-noise limit (**)" if True in v
                             else "ratio (*)")
            for (ds, meth), v in sorted(by_arm.items())}


# ------------------------------------------------------------------ loading

def load_delta_feat():
    out = {}
    for fn in sorted(os.listdir(E5_DIR)):
        m = re.match(r"delta_feat_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.json$", fn)
        if not m:
            continue
        with open(os.path.join(E5_DIR, fn), encoding="utf-8") as f:
            o = json.load(f)
        key = (o.get("dataset", m.group(1)), o.get("arch", m.group(2)))
        out.setdefault(key, {}).update(
            {(r["corruption"], int(r["severity"]), int(r["idx"])):
             float(r["delta_feat"]) for r in o.get("records", [])})
    return out


def load_cells():
    """{(dataset, method, corruption, severity): [episode, ...]} for the
    bn-eval `main` runs, pooled over model seeds exactly as aggregate.py does."""
    dfeat = load_delta_feat()
    cells = {}
    for fn in sorted(os.listdir(E2_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(E2_DIR, fn), encoding="utf-8") as f:
            o = json.load(f)
        argv = o.get("meta", {}).get("argv", {})
        if argv.get("mode", "main") != "main":
            continue
        ds, meth = argv["dataset"], argv["method"]
        fmap = dfeat.get((ds, METHOD_ARCH.get(meth)), {})
        for cell in o.get("results", []):
            corr, sev = cell["corruption"], int(cell["severity"])
            key = (ds, meth, corr, sev)
            for e in cell.get("episodes", []):
                df = (fmap.get((corr, sev, int(e["idx"])))
                      if e.get("idx") is not None else None)
                rec = _episode_stats(e.get("alpha"), e.get("sigma2_rel"),
                                     df, e.get("delta_proxy"))
                rec["frozen_loss"] = e["frozen_loss"]
                rec["steps"] = {int(t): v["loss"]
                                for t, v in e.get("steps", {}).items()}
                cells.setdefault(key, []).append(rec)
    assert_noise_homogeneous(cells)
    return cells


# ------------------------------------------------------------------ stats

def _rank(a):
    a = np.asarray(a, float)
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    vals, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(vals))
    np.add.at(sums, inv, ranks)
    return sums[inv] / cnt[inv]


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3 or _rank(x).std() == 0 or _rank(y).std() == 0:
        return None
    return float(np.corrcoef(_rank(x), _rank(y))[0, 1])


def agg(vals, how):
    v = [float(x) for x in vals if x is not None and np.isfinite(float(x))]
    if not v:
        return None
    return float(np.mean(v)) if how == "mean" else float(np.median(v))


def cell_stats(eps, idx_stat, idx_gain, stat_key, how):
    """Statistic from idx_stat episodes, gains from idx_gain episodes.

    Returns (phase, gain_final, gain_best_crossfit, gain_best_insample)."""
    S = [eps[i] for i in idx_stat]
    V = [eps[i] for i in idx_gain]
    phase = agg([e[stat_key] for e in S], how)
    steps = sorted({t for e in eps for t in e["steps"]})
    if not steps:
        return phase, None, None, None

    def gain_at(pool, t):
        return agg([e["frozen_loss"] - e["steps"][t]
                    for e in pool if t in e["steps"]], how)

    final_t = steps[-1]
    gain_final = gain_at(V, final_t)
    # cross-fit best step: chosen on the commissioning share, scored on eval
    gS = {t: gain_at(S, t) for t in steps}
    gS = {t: v for t, v in gS.items() if v is not None}
    t_best = max(gS, key=gS.get) if gS else None
    gain_best_cf = gain_at(V, t_best) if t_best is not None else None
    # in-sample best step on the EVALUATION share (the published convention)
    gV = {t: gain_at(V, t) for t in steps}
    gV = {t: v for t, v in gV.items() if v is not None}
    gain_best_is = max(gV.values()) if gV else None
    return phase, gain_final, gain_best_cf, gain_best_is


def build_rows(cells, method, rng, commission, stat_key, how):
    rows = []
    for key in sorted(cells):
        ds, meth, corr, sev = key
        if meth != method:
            continue
        eps = cells[key]
        n = len(eps)
        perm = rng.permutation(n)
        if commission >= 1.0:
            idx_stat = idx_gain = list(range(n))
        else:
            k = int(round(n * commission))
            k = min(max(k, 1), n - 1)
            idx_stat, idx_gain = perm[:k].tolist(), perm[k:].tolist()
        ph, gf, gbc, gbi = cell_stats(eps, idx_stat, idx_gain, stat_key, how)
        rows.append({"dataset": ds, "corruption": corr, "severity": sev,
                     "n_episodes": n, "n_commission": len(idx_stat),
                     "n_evaluation": len(idx_gain),
                     "phase": ph, "gain_final": gf,
                     "gain_best_crossfit": gbc,
                     "gain_best_in_sample": gbi})
    return rows


def clustered_bootstrap(rows, ykey, n_boot, rng):
    """Resample CORRUPTIONS with replacement; all severities travel together."""
    by_corr = {}
    for r in rows:
        by_corr.setdefault(r["corruption"], []).append(r)
    corrs = sorted(by_corr)
    if len(corrs) < 3:
        return None
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(corrs), len(corrs))
        sub = [r for i in pick for r in by_corr[corrs[i]]]
        rho = spearman([r["phase"] for r in sub], [r[ykey] for r in sub])
        if rho is not None:
            vals.append(rho)
    if len(vals) < 50:
        return None
    v = np.asarray(vals)
    return {"lo": float(np.percentile(v, 2.5)),
            "hi": float(np.percentile(v, 97.5)),
            "n_boot": len(vals), "cluster": "corruption",
            "n_clusters": len(corrs)}


def analyse(cells, method, seed, commission, stat_key, n_boot):
    rng = np.random.default_rng(seed)
    out = {"method": method, "seed": seed, "commission_share": commission,
           "statistic": stat_key}
    for how in ("mean", "median"):
        rows = build_rows(cells, method, np.random.default_rng(seed + 1),
                          commission, stat_key, how)
        out[f"n_cells_{how}"] = len(rows)
        for ykey, tag in (("gain_final", "final"),
                          ("gain_best_crossfit", "best_crossfit"),
                          ("gain_best_in_sample", "best_in_sample")):
            rho = spearman([r["phase"] for r in rows], [r[ykey] for r in rows])
            out[f"rho_{how}_{tag}"] = rho
            if n_boot:
                out[f"ci_{how}_{tag}"] = clustered_bootstrap(
                    rows, ykey, n_boot, rng)
        out[f"rows_{how}"] = rows if how == "mean" else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commission", type=float, default=0.5)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--statistic", default="phase_feat",
                    choices=["phase_feat", "phase_loss", "phase_align",
                             "phase_loss_unsigned"])
    ap.add_argument("--out-prefix", default="f8_e2_crossfit",
                    help="output file stem; set to a fresh f-number to keep "
                         "an earlier run's JSONs intact")
    args = ap.parse_args()

    cells = load_cells()
    print(f"[f8] loaded {len(cells)} (dataset, method, corruption, severity) "
          f"cells; {sum(len(v) for v in cells.values())} episodes", flush=True)
    print(f"[f8] noise regime per arm: {assert_noise_homogeneous(cells)}",
          flush=True)

    # ---- reproduction check: no split -> published same-sample numbers
    repro = {}
    for meth in STOCHASTIC:
        r = analyse(cells, meth, 20260801, 1.0, args.statistic, 0)
        repro[meth] = {k: v for k, v in r.items()
                       if k.startswith("rho_") or k.startswith("n_cells")}
    bad = []
    for (meth, tag), want in PUBLISHED.items():
        key = {"mean_final": "rho_mean_final",
               "median_final": "rho_median_final",
               "mean_best": "rho_mean_best_in_sample",
               "median_best": "rho_median_best_in_sample"}[tag]
        got = repro[meth].get(key)
        if got is None or abs(got - want) > 0.02:
            bad.append((meth, tag, want, got))
    # the PUBLISHED table is the feature-proxy statistic; the assertion is
    # only meaningful for that statistic.
    assert args.statistic != "phase_feat" or not bad, (
        "same-sample reproduction of the published Spearman values failed: "
        + "; ".join(f"{m}/{t}: published {w}, recomputed {g}"
                    for m, t, w, g in bad))
    print(f"[f8] same-sample reproduction of published rho "
          f"({args.statistic}): {'OK' if not bad else 'N/A (other statistic)'}",
          flush=True)
    C.save({"note": ("no-split recomputation of the published same-sample "
                     "Spearman values from the original E2/E5 records"),
            "published": {f"{m}/{t}": v for (m, t), v in PUBLISHED.items()},
            "recomputed": repro}, f"{args.out_prefix}_reproduction_check.json")

    # ---- cross-fit
    per_method = {}
    for meth in STOCHASTIC:
        runs = [analyse(cells, meth, s, args.commission, args.statistic,
                        args.n_boot) for s in args.seeds]
        for r, s in zip(runs, args.seeds):
            C.save(r, f"{args.out_prefix}_{meth}_seed{s}.json")
        agg_out = {"method": meth, "seeds": args.seeds,
                   "commission_share": args.commission,
                   "statistic": args.statistic,
                   "n_cells": runs[0]["n_cells_mean"]}
        for how in ("mean", "median"):
            for tag in ("final", "best_crossfit", "best_in_sample"):
                k = f"rho_{how}_{tag}"
                agg_out[k] = C.mean_range([r[k] for r in runs])
                cis = [r.get(f"ci_{how}_{tag}") for r in runs]
                cis = [c for c in cis if c]
                if cis:
                    agg_out[f"ci_{how}_{tag}_clustered"] = {
                        "lo_mean": float(np.mean([c["lo"] for c in cis])),
                        "hi_mean": float(np.mean([c["hi"] for c in cis])),
                        "lo_min": float(np.min([c["lo"] for c in cis])),
                        "hi_max": float(np.max([c["hi"] for c in cis])),
                        "n_clusters": cis[0]["n_clusters"],
                        "n_boot": cis[0]["n_boot"]}
        per_method[meth] = agg_out
        print(f"[f8] {meth}: cross-fit rho_mean_final="
              f"{agg_out['rho_mean_final']['mean']:.3f} "
              f"(range {agg_out['rho_mean_final']['min']:.3f}-"
              f"{agg_out['rho_mean_final']['max']:.3f}), "
              f"best_crossfit={agg_out['rho_mean_best_crossfit']['mean']:.3f}",
              flush=True)

    n_pass = sum(
        1 for m in STOCHASTIC
        if any(per_method[m][k]["mean"] is not None
               and per_method[m][k]["mean"] >= 0.5
               for k in ("rho_mean_final", "rho_median_final",
                         "rho_mean_best_crossfit",
                         "rho_median_best_crossfit")))
    C.save({"script": "f8_e2_crossfit.py",
            "replaces": ("aggregate.py E2 Spearman correlations "
                         "(same-sample statistic and gain; in-sample best "
                         "step)"),
            "protocol": ("per-cell episodes split by a fresh seed into a "
                         "commissioning share (phase statistic) and a "
                         "disjoint evaluation share (realized gain); best "
                         "step chosen on commissioning, scored on "
                         "evaluation; CIs from a corruption-clustered "
                         "bootstrap"),
            "commission_share": args.commission, "seeds": args.seeds,
            "statistic": args.statistic,
            "per_method": per_method,
            "c2_gate_stochastic_methods_passing_rho_ge_0.5": n_pass},
           f"{args.out_prefix}_summary.json")
    print("[f8] DONE", flush=True)


if __name__ == "__main__":
    main()
