#!/usr/bin/env python
"""Figure 4 -- E2 cell-level phase statistic vs realized gain, annotated with
CROSS-FIT rank correlations.

WHAT THE PANELS ANNOTATE.  The annotated values are the CROSS-FIT Spearman
correlations, not the full-sample ones.  A paper cannot designate cross-fitted
values as its defensible evidence while foregrounding the larger same-sample
estimates in its figures, and the cross-fitted values are the smaller of the
two.

SIGNED STATISTIC.  Panel (c) reads the f22b/f23 outputs, whose statistic is
the manuscript's
    Phi   = alpha_sgn|alpha_sgn| delta_proxy / sigma^2_rel,
    Phi_0 = alpha_sgn|alpha_sgn| delta_proxy      (the declared sigma^2 -> 0
            limit, which is what the deterministic N=1 arms use because their
            sigma^2_rel is identically zero).
The f8b/f16 outputs must not be substituted here: they carry an UNSIGNED
alignment factor `alpha**2` in place of the signed `alpha*|alpha|`.  Panels
(a,b) take the same value either way -- the feature-proxy branch carries the
sign in both -- but are read from f22 so that every panel has one provenance.

Every number on this figure comes from one protocol: within each
(dataset, method, corruption, severity) cell the episodes are split by a fresh
seed into a COMMISSIONING share, which defines the phase statistic, and a
disjoint EVALUATION share, which defines the realized gain.  Cross-fit
correlations are therefore free of the shared-episode coupling that inflated
the same-sample ones, and the "best step" variant is chosen on commissioning
and scored on evaluation rather than maximised in sample.

Panels
  (a) ttt_rot, (b) ttt_mask -- stochastic SSL objectives, feature-proxy
      statistic alpha|alpha| delta_feat / sigma^2.  Markers are the per-cell
      values averaged over the five split seeds; the annotated rho is the
      cross-fit Spearman as mean over those seeds with its across-seed range,
      together with the SPLIT-AVERAGED CLUSTERED ENDPOINTS.  Those endpoints
      are the arithmetic means, across the five split seeds, of the lower and
      of the upper endpoint of the five separately computed
      corruption-clustered 95% bootstrap intervals (fields `lo_mean` /
      `hi_mean` of `ci_mean_final_clustered`).  They are NOT the endpoints of
      a single interval with 95% coverage for the split-averaged estimator:
      averaging interval endpoints does not in general preserve the nominal
      coverage of the constituent intervals, so the pair must never be
      labelled a "clustered 95% CI".  The manuscript uses the term
      "split-averaged clustered endpoints" throughout (Appendix C) and this
      figure's internal labels use it too.  The superseded
      same-sample value is printed in grey underneath so the reader can see
      exactly how much the split costs.
  (c) tent / pl -- deterministic self-amplifying objectives with the
      loss-proxy statistic in its zero-noise form, likewise cross-fitted
      (f22b), PLUS the architecture
      control from f15/f23: the same entropy objective run on
      ResNet-26+GroupNorm, the stochastic methods' own architecture.  With
      that series on the panel the comparison no longer changes architecture
      and objective at once.

Data
    experiments/results/is_fresh/f22_e2_crossfit_feat_{method}_seed*.json
    experiments/results/is_fresh/f22_e2_crossfit_feat_summary.json
    experiments/results/is_fresh/f22b_e2_crossfit_det_{method}_seed*.json
    experiments/results/is_fresh/f22b_e2_crossfit_det_summary.json
    experiments/results/is_fresh/f23_e2_gn_summary.json

Usage: python fig_f4_e2.py [--out PATH ...] [--png]
Defaults write paper/is/paper/figures/F4_e2_phase.pdf.
"""
from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]


def _rel(p):
    """Repo-relative POSIX form of `p`.

    Console output from these generators is captured into archived run logs,
    so it must never carry the build machine's absolute prefix.
    """
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(p).name


RES = ROOT / "experiments" / "results" / "is_fresh"
OUT_DEFAULT = [ROOT / "paper" / "is" / "paper" / "figures" / "F4_e2_phase.pdf"]

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
BASE = "#c3c2b7"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
RED = "#e34948"
ORANGE = "#eb6834"

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
    "legend.frameon": False,
})


def seed_mean_rows(pattern):
    """Average each (dataset, corruption, severity) cell over the split seeds."""
    acc = defaultdict(lambda: {"phase": [], "gain": []})
    n_seeds = 0
    for p in sorted(glob.glob(str(RES / pattern))):
        o = json.loads(Path(p).read_text(encoding="utf-8"))
        n_seeds += 1
        for r in o["rows_mean"]:
            if r["phase"] is None or r["gain_final"] is None:
                continue
            k = (r["dataset"], r["corruption"], r["severity"])
            acc[k]["phase"].append(r["phase"])
            acc[k]["gain"].append(r["gain_final"])
    rows = [{"dataset": k[0], "corruption": k[1], "severity": k[2],
             "phase": float(np.mean(v["phase"])),
             "gain": float(np.mean(v["gain"]))}
            for k, v in sorted(acc.items())]
    return rows, n_seeds


def fmt_rho(agg, key, ci_key):
    """Panel annotation.

    The bracketed pair on the third/fourth line is the SPLIT-AVERAGED
    CLUSTERED ENDPOINT pair -- the mean over the five split seeds of the
    lower and of the upper endpoint of the five per-split
    corruption-clustered bootstrap intervals.  It is deliberately NOT
    labelled a confidence interval: averaging endpoints does not preserve
    nominal coverage.  See the module docstring.
    """
    v = agg[key]
    s = rf"$\rho_s = {v['mean']:.2f}$"
    s += f"\n[{v['min']:.2f}, {v['max']:.2f}] over {v['n']} splits"
    ci = agg.get(ci_key)
    if ci:
        s += (f"\nsplit-averaged clustered\nendpoints "
              f"[{ci['lo_mean']:.2f}, {ci['hi_mean']:.2f}]")
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, nargs="*", default=OUT_DEFAULT)
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()

    summ = json.loads((RES / "f22_e2_crossfit_feat_summary.json")
                      .read_text(encoding="utf-8"))["per_method"]
    det_path = RES / "f22b_e2_crossfit_det_summary.json"
    det = (json.loads(det_path.read_text(encoding="utf-8"))["per_method"]
           if det_path.exists() else {})

    fig = plt.figure(figsize=(6.9, 2.85))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.98], wspace=0.52)

    for k, (method, color, lthr) in enumerate(
            [("ttt_rot", BLUE, 1e-3), ("ttt_mask", AQUA, 1e-4)]):
        ax = fig.add_subplot(gs[0, k])
        rows, n_seeds = seed_mean_rows(
            f"f22_e2_crossfit_feat_{method}_seed*.json")
        x = np.array([r["phase"] for r in rows])
        y = np.array([r["gain"] for r in rows])
        for ds, mk in (("cifar10", "o"), ("cifar100", "s")):
            m = np.array([r["dataset"] == ds for r in rows])
            ax.scatter(x[m], y[m], s=15, marker=mk, color=color, alpha=0.75,
                       linewidths=0, label=f"CIFAR-{ds[5:]}-C")
        ax.set_xscale("symlog", linthresh=lthr)
        ax.axhline(0, color=MUTED, lw=0.7, ls=":")
        ax.set_title(f"({'ab'[k]}) {method} (cross-fit)", pad=4)
        same = {"ttt_rot": 0.622, "ttt_mask": 0.686}[method]
        ax.annotate(fmt_rho(summ[method], "rho_mean_final",
                            "ci_mean_final_clustered")
                    + f"\nsame-sample {same:.2f} (superseded)",
                    xy=(0.03, 0.98), xycoords="axes fraction", va="top",
                    fontsize=6.9, color=INK)
        ax.set_xlabel(r"empirical diagnostic $D_{\rm emp}$"
                      "\n(commissioning share)")
        if k == 0:
            ax.set_ylabel("loss gain, final step\n(evaluation share)")
            ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.10),
                      handletextpad=0.1, borderaxespad=0.2)
        print(f"{method}: {len(rows)} cells over {n_seeds} split seeds; "
              f"cross-fit rho {summ[method]['rho_mean_final']['mean']:.3f} "
              f"(range {summ[method]['rho_mean_final']['min']:.3f}-"
              f"{summ[method]['rho_mean_final']['max']:.3f}); same-sample {same}")

    ax = fig.add_subplot(gs[0, 2])
    for method, color, mk in (("tent", RED, "o"), ("pl", ORANGE, "s")):
        if method not in det:
            continue
        rows, _ = seed_mean_rows(
            f"f22b_e2_crossfit_det_{method}_seed*.json")
        x = np.array([r["phase"] for r in rows])
        y = np.array([r["gain"] for r in rows])
        v = det[method]["rho_mean_final"]
        ax.scatter(x, y, s=13, marker=mk, color=color, alpha=0.7, linewidths=0,
                   label=rf"{method} @ WRN+BN ($\rho_s={v['mean']:.2f}$)")
        ss = det[method]["same_sample_reference"]["rho_mean_final"]
        print(f"{method}: cross-fit rho {v['mean']:.3f} "
              f"(range {v['min']:.3f}-{v['max']:.3f}); same-sample {ss:.3f}")
    # architecture control (f15 run, f16 analysis): the SAME entropy objective
    # on the stochastic methods' architecture.  Its presence is the point of
    # the panel -- without it the comparison changes architecture and objective
    # at once.
    gn_path = RES / "f23_e2_gn_summary.json"
    if gn_path.exists():
        gn = json.loads(gn_path.read_text(encoding="utf-8"))
        rows, _ = seed_mean_rows("f23_e2_gn_tent_gn_loss_seed*.json")
        x = np.array([r["phase"] for r in rows])
        y = np.array([r["gain"] for r in rows])
        v = gn["arms"]["tent_gn_loss"]["rho_mean_final"]
        ax.scatter(x, y, s=17, marker="^", facecolors="none",
                   edgecolors="#7a1fa2", linewidths=0.9, alpha=0.95,
                   label=rf"tent @ ResNet-26+GN ($\rho_s={v['mean']:.2f}$)")
        print(f"tent@GN: cross-fit rho {v['mean']:.3f} "
              f"(range {v['min']:.3f}-{v['max']:.3f})")
    ax.set_xscale("symlog", linthresh=1e-2)
    ax.set_yscale("symlog", linthresh=0.1)
    ax.axhline(0, color=MUTED, lw=0.7, ls=":")
    ax.set_title("(c) deterministic objectives\n"
                 "(architecture controlled)", pad=4, fontsize=8.0)
    # NB every cell in this panel is negative in BOTH coordinates: the
    # correlation orders the severity of the loss, it does not separate help
    # from harm.  The axis label names the zero-noise form of the statistic,
    # which is what these sigma^2_rel == 0 arms use.
    ax.set_xlabel(r"loss-proxy stat. "
                  r"$\alpha_{\rm sgn}|\alpha_{\rm sgn}|\,\delta_{\rm loss}$"
                  "\n(commissioning share)")
    ax.set_ylabel("loss gain, final step")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.93),
              handletextpad=0.1, borderaxespad=0.2, fontsize=6.4)

    fig.tight_layout(w_pad=1.1)
    for out in args.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", pad_inches=0.03)
        print(f"saved {_rel(out)} ({out.stat().st_size} bytes)")
        if args.png:
            fig.savefig(out.with_suffix(".png"), bbox_inches="tight",
                        pad_inches=0.03)
    plt.close(fig)


if __name__ == "__main__":
    main()
