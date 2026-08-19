"""Figure 1 -- exact-model excess-risk curves, FRESH five-seed regeneration.

REPLACES figures/scripts/fig_F1.py (now under figures/scripts/_superseded/),
which read the single-seed record `experiments/results/e1/e1_a_seed42.json`.
That record is not an input to any number in the manuscript any more: the
risk-curve match is reported from `f7_curve_match.py`, which
remeasures the same 30-cell grid at the five fresh seeds 20260801-05 with
40,000 replicates per cell.  The figure lagged behind the text -- its caption
claimed five seeds while its curves were seed 42.  This script closes that gap,
so Figure 1 is regenerable from the release archive with **no external record
files at all**.

WHAT IT DRAWS
  The same four representative cells as the published figure,
  (alpha, delta/sigma) in {0.25, 1.0} x {1.0, 4.0}:
    * simulation: the across-seed MEAN of the empirical risk curve
      Ehat(t) = mean_rep u_t^2  (solid);
    * a replicate band: the across-seed min-max envelope of Ehat(t), i.e. the
      spread the caption refers to (it is invisible at this line width for
      most cells, which is the point);
    * theory: the closed form of Theorem 8 (label thm:exact) (dashed);
    * the frozen risk delta^2 (dotted reference);
    * per-cell annotation: the across-seed mean of the worst POINTWISE
      relative error sup_t |Ehat(t) - E(t)| / E(t), i.e. the statistic that
      row (a) of Table T4 and Sec. 5.1 report -- not the max/max
      normalization the superseded figure annotated.

REPRODUCTION CHECK (asserted, and the reason this script re-simulates rather
than reading a curve dump)
  `f7_curve_match.py` draws its 30 cells from ONE `default_rng(seed)` stream in
  a fixed (alpha, ratio) order, so a cell's replicates depend on the whole loop
  that precedes it.  This script replays that loop verbatim -- same constants,
  same order, same stream -- and therefore recomputes, for every one of the 30
  cells and every seed, exactly the four error statistics `f7` stored.  It
  ASSERTS that all 600 of them agree with the archived
  `f7_curve_match_seed<seed>.json` rows to 1e-9 relative.  If the assertion
  passes, the curves being plotted are, replicate for replicate, the ones the
  reported numbers were computed from.

  Cost: ~22 s per seed (5 seeds, ~2 min total), CPU only.

OUTPUT
  paper/is/paper/figures/F1_curves.pdf   (--png also writes .png)
  experiments/results/is_fresh/fig_f1_curves.json   (the annotated values and
  the outcome of the reproduction check, so the figure's numbers are auditable
  without opening the PDF)
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import common as C  # noqa: E402

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]


def _rel(p):
    """Repo-relative POSIX form of `p`.

    Console output from these generators is captured into archived run logs,
    so it must never carry the build machine's absolute prefix.
    """
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(p).name


RESULTS = ROOT / "results" / "is_fresh"
OUT_DEFAULT = [ROOT / "paper" / "is" / "paper" / "figures" / "F1_curves.pdf"]

# the four representative cells of the published figure, as (alpha, delta/sigma)
CELLS = [(0.25, 1.0), (0.25, 4.0), (1.0, 1.0), (1.0, 4.0)]

N_REP = 40_000                      # identical to f7_curve_match.N_REP

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
BASE = "#c3c2b7"
BLUE = "#1f5b8f"

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 300, "pdf.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 8.5, "axes.titlesize": 8.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.6,
})


def replay_seed(seed, n_rep, T, want):
    """Replay f7_curve_match.run_seed's loop; keep curves for `want` cells.

    Returns (rows, curves) where `rows` is the same list of per-cell error
    statistics f7 stores and `curves` maps (alpha, ratio) -> dict of arrays.
    """
    rng = np.random.default_rng(seed)
    ts = np.arange(T + 1)
    rows, curves = [], {}
    for a in C.ALPHAS:
        for r in C.RATIOS:
            delta = r * C.SIGMA
            us = C.simulate_scalar(a, delta, C.SIGMA, C.ETA, T, n_rep, rng)
            emp = (us ** 2).mean(axis=0)
            se = (us ** 2).std(axis=0, ddof=1) / np.sqrt(n_rep)
            theo = C.excess_risk(ts, a, delta, C.SIGMA, C.ETA)
            absdiff = np.abs(emp - theo)
            rows.append({
                "alpha": a, "delta": delta,
                "max_rel_err_published_norm": float(
                    absdiff.max() / max(theo.max(), 1e-12)),
                "max_rel_err_pointwise": float(
                    (absdiff / np.maximum(theo, 1e-12)).max()),
                "max_err_in_se_units": float(
                    (absdiff / np.maximum(se, 1e-30)).max()),
                "median_err_in_se_units": float(np.median(
                    absdiff / np.maximum(se, 1e-30))),
            })
            if (a, r) in want:
                curves[(a, r)] = {"emp": emp, "se": se, "theo": theo}
            del us
    return rows, curves


STAT_KEYS = ("max_rel_err_published_norm", "max_rel_err_pointwise",
             "max_err_in_se_units", "median_err_in_se_units")


def check_against_f7(seed, rows, n_rep, T, tol=1e-9):
    """Assert the replay reproduces the archived f7 per-cell statistics."""
    path = RESULTS / f"f7_curve_match_seed{seed}.json"
    if not path.exists():
        return {"seed": seed, "checked": False,
                "reason": f"{path.name} not present"}
    ref = json.loads(path.read_text(encoding="utf-8"))
    if ref["n_rep"] != n_rep or ref["T"] != T:
        return {"seed": seed, "checked": False,
                "reason": (f"protocol mismatch: archived n_rep={ref['n_rep']}, "
                           f"T={ref['T']}; replay n_rep={n_rep}, T={T}")}
    assert len(ref["rows"]) == len(rows), (
        f"seed {seed}: {len(ref['rows'])} archived cells vs {len(rows)} replayed")
    worst = 0.0
    for i, (a, b) in enumerate(zip(ref["rows"], rows)):
        assert a["alpha"] == b["alpha"] and a["delta"] == b["delta"], (
            f"seed {seed}: cell {i} order differs from f7 "
            f"({a['alpha']},{a['delta']}) vs ({b['alpha']},{b['delta']})")
        for k in STAT_KEYS:
            rel = abs(a[k] - b[k]) / max(abs(a[k]), 1e-30)
            worst = max(worst, rel)
            assert rel < tol, (
                f"seed {seed}: cell ({a['alpha']},{a['delta']}) key {k} "
                f"differs from f7 by {rel:.3e} "
                f"(archived {a[k]!r}, replayed {b[k]!r})")
    return {"seed": seed, "checked": True, "n_cells": len(rows),
            "n_statistics": len(rows) * len(STAT_KEYS),
            "worst_relative_difference": worst}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, nargs="*", default=OUT_DEFAULT)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--no-check", action="store_true",
                    help="skip the f7 reproduction check (for quick previews "
                         "at a reduced --n-rep, which cannot reproduce it)")
    args = ap.parse_args()

    T = C.T
    want = set(CELLS)
    per_seed_curves, checks = [], []
    for s in args.seeds:
        rows, curves = replay_seed(s, args.n_rep, T, want)
        missing = want - set(curves)
        assert not missing, f"cells {sorted(missing)} are not on the f7 grid"
        per_seed_curves.append(curves)
        if not args.no_check:
            checks.append(check_against_f7(s, rows, args.n_rep, T))
        print(f"[fig_f1] seed {s}: replayed {len(rows)} cells"
              + ("" if args.no_check else
                 f", f7 check {checks[-1].get('checked')}"), flush=True)

    ts = np.arange(T + 1)
    # Width/height matter: the figure is included at width=\textwidth in a
    # single-column cas-sc float.  A portrait aspect ratio makes the float
    # taller than \topfraction, LaTeX defers it, and every later float
    # queues behind it and lands after the appendices.  Keep the landscape
    # shape of the other figures (aspect ~0.7).
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.2), sharex=True)
    annot = {}
    for ax, (a, r) in zip(axes.ravel(), CELLS):
        delta = r * C.SIGMA
        emps = np.array([cs[(a, r)]["emp"] for cs in per_seed_curves])
        theo = per_seed_curves[0][(a, r)]["theo"]
        mean_emp = emps.mean(axis=0)
        lo, hi = emps.min(axis=0), emps.max(axis=0)
        # across-seed mean of the per-seed worst pointwise relative error
        pw = float(np.mean([
            np.max(np.abs(e - theo) / np.maximum(theo, 1e-12)) for e in emps]))
        annot[f"alpha={a},delta_over_sigma={r}"] = {
            "mean_worst_pointwise_rel_err": pw,
            "per_seed_worst_pointwise_rel_err": [
                float(np.max(np.abs(e - theo) / np.maximum(theo, 1e-12)))
                for e in emps],
            "frozen_risk_delta_sq": delta ** 2}

        ax.fill_between(ts, lo, hi, color=BLUE, alpha=0.35, lw=0, zorder=2,
                        label="across-seed min–max")
        ax.plot(ts, mean_emp, color=BLUE, lw=1.6, zorder=3,
                label=f"simulation ({len(emps)} seeds)")
        ax.plot(ts, theo, color=INK, lw=1.1, ls="--", zorder=4,
                label="theory (closed form)")
        ax.axhline(delta ** 2, color=MUTED, lw=0.8, ls=":", zorder=1,
                   label=r"frozen risk $\delta^2$")
        ax.set_title(rf"$\alpha={a}$,  $\delta/\sigma={r:g}$", pad=3)
        ax.annotate(rf"$\sup_t$ rel. err {pw * 100:.1f}\%".replace("\\%", "%"),
                    xy=(0.96, 0.08), xycoords="axes fraction",
                    ha="right", va="bottom", fontsize=6.8, color=INK2)
        ax.margins(x=0)
    for ax in axes[1]:
        ax.set_xlabel("adaptation step $t$")
    for ax in axes[:, 0]:
        ax.set_ylabel("excess risk $E(t)$")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    order = [labels.index(l) for l in
             [f"simulation ({len(args.seeds)} seeds)", "across-seed min–max",
              "theory (closed form)", r"frozen risk $\delta^2$"]
             if l in labels]
    fig.legend([handles[i] for i in order], [labels[i] for i in order],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.9, columnspacing=1.4, handletextpad=0.5,
               labelcolor=INK2)
    fig.tight_layout(h_pad=0.9, w_pad=1.0)
    for out in args.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
        print(f"saved {_rel(out)} ({out.stat().st_size} bytes)")
        if args.png:
            fig.savefig(out.with_suffix(".png"), bbox_inches="tight",
                        pad_inches=0.02)
    plt.close(fig)

    record = {
        "script": "fig_f1_curves.py",
        "replaces": "figures/scripts/_superseded/fig_F1.py (single seed 42)",
        "figure": "paper/is/paper/figures/F1_curves.pdf",
        "seeds": list(args.seeds), "n_rep_per_cell": args.n_rep, "T": T,
        "cells": [{"alpha": a, "delta_over_sigma": r} for a, r in CELLS],
        "annotations": annot,
        "f7_reproduction_check": checks,
        "f7_reproduction_check_all_passed": bool(
            checks and all(c.get("checked") for c in checks)),
    }
    C.save(record, "fig_f1_curves.json")
    if not args.no_check:
        assert record["f7_reproduction_check_all_passed"], (
            "the f7 reproduction check did not run on every seed: "
            f"{[c for c in checks if not c.get('checked')]}")
        print("[fig_f1] f7 reproduction check PASSED on "
              f"{len(checks)} seeds x {checks[0]['n_statistics']} statistics")


if __name__ == "__main__":
    main()
