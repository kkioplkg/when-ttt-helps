"""Original bootstrap/seed-range helper for the headline correlations.

STATUS.  Only branch (b), `e3_seed_ranges`, is current: it is the record of
record for the E3 across-seed spread quoted in the Information Sciences
manuscript.  Branches (a) -- `e2_cis` and `e4_cis` -- are SUPERSEDED and no
number they print appears in that manuscript.  They are retained because
`experiments/ttt/is_fresh/f11_e4_cluster_ci.py` reproduces the E4 construction
below verbatim as its `naive_iid_rows` baseline, and that comparison is what
makes the corrected interval's widening attributable to the resampling unit
alone.  Do not quote (a).

(a) SUPERSEDED bootstrap CIs (1000 resamples, percentile 2.5/97.5):
    - E2: per-method Spearman of the feature-proxy phase statistic
      (mean/median of alpha*|alpha|*delta_feat/sigma^2 per cell) against
      realized gain (final and best step), resampling the
      (dataset, corruption, severity) CELLS i.i.d.  Superseded by
      is_fresh/f8_e2_crossfit.py (-> f22/f22b/f22c), which cross-fits the
      statistic and resamples CORRUPTION clusters, not cells.
    - E4: per-domain Spearman of the delta_v2 phase statistic against
      per-document gain at the ALTA stop, plus the mean perplexity
      improvement.  THE RESAMPLING UNIT HERE IS THE SEED-DOCUMENT ROW, NOT
      THE DOCUMENT.  `e4_records()` returns 500 documents x 3 adaptation
      seeds = 1500 rows per domain, discards the document identifier, and
      `boot_ci` resamples those 1500 rows independently.  The three seed
      rows of one document are NOT independent -- the adaptation seed only
      re-randomises the SSL gradient noise while the document, and hence the
      phase statistic and most of the gain, is held fixed -- so these
      intervals are too narrow by a design effect of roughly 1.55-1.76.
      Superseded by is_fresh/f11_e4_cluster_ci.py, which resamples the 500
      DOCUMENTS with the three seed rows nested inside each; the E4 intervals
      the manuscript prints come from f11 and are unaffected by this script.

(b) CURRENT.  Seed ranges where multi-seed data exists:
    - E3: ALTA adapted accuracy across seeds 0/1/2 on the four 3-seed
      corruptions (motion_blur, contrast, fog, gaussian_noise).  This is the
      branch sections/experiments.tex cites.
    - E4: perplexity improvement at the ALTA stop per adaptation seed
      (descriptive only; no interval).

Printed only; nothing is written.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "ttt" / "analysis"))
from aggregate import analyze_e2_main, gather_files, spearman  # noqa: E402

B = 1000
RNG = np.random.default_rng(0)


def boot_ci(rows, stat, b=B):
    """Percentile bootstrap CI of stat(list_of_rows)."""
    n = len(rows)
    vals = []
    for _ in range(b):
        idx = RNG.integers(0, n, n)
        v = stat([rows[i] for i in idx])
        if v is not None and np.isfinite(v):
            vals.append(v)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi), len(vals)


# ------------------------------------------------------------------- E2

def e2_cis():
    found, _ = gather_files(str(RESULTS), False)
    main_r = [(fn, obj) for fn, obj in found["e2"]
              if (obj["meta"]["argv"].get("mode") or
                  ("batch_sweep" if "_batch_sweep_" in fn else
                   "calib" if "_calib_" in fn else "main")) == "main"]
    e2 = analyze_e2_main(main_r, found.get("e5", []))
    print("== [SUPERSEDED -- see f8_e2_crossfit.py / f22*] E2 feature-proxy "
          "Spearman, same-sample, i.i.d. bootstrap over CELLS ==")
    for meth in ("ttt_mask", "ttt_rot"):
        rows = [r for r in e2["cells"] if r["method"] == meth
                and r["mean_phase_feat"] is not None]
        for xkey, ykey, label in (
                ("mean_phase_feat", "gain_final", "mean-final"),
                ("median_phase_feat", "gain_final_median", "median-final"),
                ("mean_phase_feat", "gain_best", "mean-best"),
                ("median_phase_feat", "gain_best_median", "median-best")):
            def stat(rs, xk=xkey, yk=ykey):
                rho, _ = spearman([r[xk] for r in rs], [r[yk] for r in rs])
                return rho
            point = stat(rows)
            lo, hi, nb = boot_ci(rows, stat)
            print(f"  {meth:9s} {label:12s} rho={point:+.3f} "
                  f"95% CI [{lo:+.3f}, {hi:+.3f}]  (n_cells={len(rows)}, "
                  f"B={nb})")


# ------------------------------------------------------------------- E4

def e4_records():
    """domain -> list of (phase_v2, gain_alta, frozen_ce, alta_ce, seed).

    One row per (document, adaptation seed): 500 x 3 = 1500 rows per domain.
    The document identifier is deliberately NOT carried, which is why the
    bootstrap below cannot cluster on it.  f11_e4_cluster_ci.py keeps it.
    """
    dv2 = {}
    for f in (RESULTS / "e5").glob("delta_v2_*.json"):
        obj = json.loads(f.read_text())
        dv2[obj.get("domain", f.stem.split("_")[-1])] = {
            int(r["doc"]): float(r["delta_v2"]) for r in obj["records"]}
    out = {}
    for f in sorted((RESULTS / "e4").glob("*_ln_s*.json")):
        obj = json.loads(f.read_text())
        dom = obj["meta"]["argv"]["domain"]
        seed = int(obj["meta"]["argv"]["seed"])
        dmap = dv2.get(dom, {})
        for r in obj["records"]:
            if not r.get("alta"):
                continue
            a, s2 = r.get("alpha"), r.get("sigma2_rel")
            v2 = dmap.get(int(r["doc"]))
            if a is None or v2 is None:
                continue
            ph = a * abs(a) * v2
            if s2 is not None and s2 > 1e-12:
                ph /= s2
            out.setdefault(dom, []).append(
                (ph, r["frozen_cont_ce"] - r["alta"]["cont_ce"],
                 r["frozen_cont_ce"], r["alta"]["cont_ce"], seed))
    return out


def e4_cis():
    recs = e4_records()
    print("== [SUPERSEDED -- see f11_e4_cluster_ci.py] E4 delta_v2 "
          "within-domain Spearman (gain at ALTA stop),")
    print("   i.i.d. bootstrap over SEED-DOCUMENT ROWS, not over document "
          "clusters; intervals are too narrow ==")
    for dom in sorted(recs):
        rows = recs[dom]

        def rho_stat(rs):
            r, _ = spearman([x[0] for x in rs], [x[1] for x in rs])
            return r

        def impr_stat(rs):
            return (math.exp(float(np.mean([x[2] for x in rs])))
                    - math.exp(float(np.mean([x[3] for x in rs]))))

        point = rho_stat(rows)
        lo, hi, _ = boot_ci(rows, rho_stat)
        ilo, ihi, _ = boot_ci(rows, impr_stat)
        ipoint = impr_stat(rows)
        by_seed = {}
        for x in rows:
            by_seed.setdefault(x[4], []).append(x)
        seed_impr = {s: impr_stat(v) for s, v in sorted(by_seed.items())}
        n_seeds = len(by_seed)
        print(f"  {dom:9s} rho={point:+.3f} row-bootstrap interval "
              f"[{lo:+.3f}, {hi:+.3f}] "
              f"(n_rows={len(rows)} = {len(rows) // n_seeds} documents "
              f"x {n_seeds} seeds; NOT a document-clustered interval)")
        print(f"            ppl improvement@ALTA = {ipoint:.3f} "
              f"95% CI [{ilo:.3f}, {ihi:.3f}]; per-seed "
              + ", ".join(f"s{s}={v:.3f}" for s, v in seed_impr.items()))


# ------------------------------------------------------------------- E3

def e3_seed_ranges():
    print("== E3 3-seed cells: ALTA adapted accuracy across seeds ==")
    spreads = []
    for corr in ("contrast", "fog", "gaussian_noise", "motion_blur"):
        for meth in ("tent", "eata", "sar"):
            accs = {}
            for seed in (0, 1, 2):
                f = RESULTS / "e3" / f"{corr}_{meth}_alta_s{seed}.json"
                obj = json.loads(f.read_text())
                for c in obj["results"]:
                    accs.setdefault(int(c["severity"]), []).append(
                        c["adapted_acc"])
            for sev, a in sorted(accs.items()):
                spread = (max(a) - min(a)) * 100
                spreads.append(spread)
                print(f"  {corr:15s} {meth:5s} s{sev}: "
                      + " ".join(f"{100*x:.2f}" for x in a)
                      + f"  spread={spread:.2f} pt")
    print(f"  spread over 24 cells: max={max(spreads):.2f} pt, "
          f"median={float(np.median(spreads)):.2f} pt")


if __name__ == "__main__":
    e2_cis()
    e4_cis()
    e3_seed_ranges()
