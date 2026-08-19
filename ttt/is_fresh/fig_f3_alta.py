#!/usr/bin/env python
"""Figure 3 -- ALTA against MEASURED oracles in the exact model, five seeds.

REPLACES the published F3_alta.pdf, which plotted two seeds (42 and 43) against
a CLOSED-FORM oracle: its denominator came from `t_star_theory`, the paper's own
risk formula evaluated at its own argmin, so every ratio in that panel was
measured-over-analytic and the "oracle" was never run.  It also compared a
K = 3 replica-averaged output against a SINGLE-trajectory oracle.

Both are fixed here.  Everything plotted is simulated:

  (a) median selected step  t_hat  vs the MEASURED oracle step, where the
      oracle step is the argmin of the risk curve on a SELECT block of
      replicates and is scored on a disjoint SCORE block.
  (b) realized-risk ratio against that measured SINGLE-trajectory oracle
      (the comparator Theorem 45, label thm:alta, is stated against), with the diagnostic
      3 log T_max bound line retained.
  (c) the same realized risks against the COMPUTE-MATCHED oracle -- the best
      fixed step for the mean of K = 3 trajectories, i.e. min_t {m_t^2+V_t/K}
      measured rather than evaluated.  This is the like-for-like benchmark:
      ALTA spends K trajectories, so the honest oracle is allowed to spend
      K too.

Five fresh seeds (20260801..20260805) are plotted as individual markers, so the
across-seed spread is visible per cell rather than summarised away.

Data
    experiments/results/is_fresh/f4_alta_measured_oracle_seed*.json
    experiments/results/is_fresh/f13_compute_matched_seed*.json

Usage
    python fig_f3_alta.py [--out PATH ...] [--png]
Defaults write paper/is/paper/figures/F3_alta.pdf.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import (FixedLocator, NullFormatter,  # noqa: E402
                               ScalarFormatter)

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


RES = ROOT / "results" / "is_fresh"
OUT_DEFAULT = [ROOT / "paper" / "is" / "paper" / "figures" / "F3_alta.pdf"]

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
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.6,
})


def load(pattern):
    out = {}
    for p in sorted(glob.glob(str(RES / pattern))):
        o = json.loads(Path(p).read_text(encoding="utf-8"))
        out[o["seed"]] = o
    return out


def logticks(ax, axis, vals):
    a = ax.xaxis if axis == "x" else ax.yaxis
    a.set_major_locator(FixedLocator(vals))
    a.set_major_formatter(ScalarFormatter())
    a.set_minor_formatter(NullFormatter())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, nargs="*", default=OUT_DEFAULT)
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()

    f4 = load("f4_alta_measured_oracle_seed*.json")
    f13 = load("f13_compute_matched_seed*.json")
    assert f4, "f4 outputs missing -- run f4_alta_measured_oracle.py"
    seeds = sorted(f4)
    bound = 3.0 * float(next(iter(f4.values()))["log_Tmax"])

    fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.55))
    ax1, ax2, ax3 = axes

    # ------------------------------------------------- (a) selected step
    lims = [5, 600]
    ax1.plot(lims, lims, color=MUTED, lw=0.8, ls=":", zorder=1)
    tt, hh = [], []
    for s in seeds:
        rows = f4[s]["rows"]
        x = [r["t_oracle_measured"] for r in rows]
        y = [r["median_t_hat"] for r in rows]
        tt += x
        hh += y
        ax1.scatter(x, y, s=17, marker="o", facecolors="none",
                    edgecolors=BLUE, linewidths=0.9, alpha=0.75, zorder=3)
    ax1.scatter([], [], s=17, marker="o", facecolors="none", edgecolors=BLUE,
                linewidths=0.9,
                label=f"{len(seeds)} seeds $\\times$ {len(f4[seeds[0]]['rows'])} cells")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlim(*lims)
    ax1.set_ylim(*lims)
    ax1.set_xlabel(r"measured oracle step $t^{\ast}$")
    ax1.set_ylabel(r"median selected step $\hat t$")
    ax1.annotate(r"$\hat t = t^{\ast}$", xy=(150, 210), fontsize=8,
                 color=MUTED, rotation=38)
    ax1.set_title("(a) selected step", pad=4)
    ax1.legend(loc="upper left", handletextpad=0.15, borderaxespad=0.2)
    logticks(ax1, "x", [20, 50, 100, 200, 400])
    logticks(ax1, "y", [10, 20, 50, 100, 200, 400])

    # -------------------------- (b) ratio vs single-trajectory oracle
    p90s = []
    for s in seeds:
        rows = f4[s]["rows"]
        x = [r["t_oracle_measured"] for r in rows]
        ax2.scatter(x, [r["p90_risk_ratio"] for r in rows], s=17, marker="o",
                    facecolors="none", edgecolors=BLUE, linewidths=0.9,
                    alpha=0.8, zorder=3)
        ax2.scatter(x, [r["median_risk_ratio"] for r in rows], s=9, marker="o",
                    color=AQUA, alpha=0.55, linewidths=0, zorder=2)
        p90s += [r["p90_risk_ratio"] for r in rows]
    ax2.axhline(bound, color=RED, lw=1.1, ls="--", zorder=2)
    ax2.annotate(r"diagnostic bound $3\log T$", xy=(0.97, bound * 0.86),
                 xycoords=("axes fraction", "data"), ha="right", va="top",
                 fontsize=7.5, color=RED)
    ax2.axhline(1.0, color=MUTED, lw=0.8, ls=":", zorder=1)
    ax2.scatter([], [], s=17, marker="o", facecolors="none", edgecolors=BLUE,
                linewidths=0.9, label="p90")
    ax2.scatter([], [], s=9, marker="o", color=AQUA, linewidths=0,
                label="median")
    ax2.legend(loc="upper left", handletextpad=0.15, borderaxespad=0.2, ncol=2,
               columnspacing=0.8)
    ax2.set_title("(b) vs measured $K{=}1$ oracle", pad=4)
    ax2.set_xlabel(r"measured oracle step $t^{\ast}$")
    ax2.set_ylabel("realized risk / oracle risk")

    # ------------------------- (c) ratio vs compute-matched K-oracle
    if f13:
        cm90 = []
        for s in sorted(f13):
            rows = f13[s]["rows"]
            x = [r["t_oracle_kK"] for r in rows]
            ax3.scatter(x, [r["p90_ratio_vs_computematched"] for r in rows],
                        s=17, marker="s", facecolors="none",
                        edgecolors=ORANGE, linewidths=0.9, alpha=0.8, zorder=3)
            ax3.scatter(x, [r["median_ratio_vs_computematched"] for r in rows],
                        s=9, marker="s", color=INK2, alpha=0.5, linewidths=0,
                        zorder=2)
            cm90 += [r["p90_ratio_vs_computematched"] for r in rows]
        ax3.axhline(bound, color=RED, lw=1.1, ls="--", zorder=2)
        ax3.axhline(1.0, color=MUTED, lw=0.8, ls=":", zorder=1)
        ax3.annotate("parity", xy=(0.985, 1.02),
                     xycoords=("axes fraction", "data"), ha="right",
                     va="bottom", fontsize=7.5, color=MUTED)
        ax3.scatter([], [], s=17, marker="s", facecolors="none",
                    edgecolors=ORANGE, linewidths=0.9, label="p90")
        ax3.scatter([], [], s=9, marker="s", color=INK2, linewidths=0,
                    label="median")
        ax3.legend(loc="upper left", handletextpad=0.15, borderaxespad=0.2,
                   ncol=2, columnspacing=0.8)
        print(f"compute-matched: max p90 {max(cm90):.2f}, "
              f"median-of-medians "
              f"{np.median([r['median_ratio_vs_computematched'] for s in f13 for r in f13[s]['rows']]):.2f}")
    else:
        ax3.text(0.5, 0.5, "f13 outputs missing", ha="center", va="center",
                 transform=ax3.transAxes, color=RED)
    ax3.set_title(r"(c) vs compute-matched $K{=}3$ oracle", pad=4)
    ax3.set_xlabel(r"compute-matched oracle step $t^{\ast}_K$")
    ax3.set_ylabel(r"realized risk / $\min_t\{m_t^2+V_t/K\}$")

    for ax in (ax2, ax3):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylim(0.2, 40)
        logticks(ax, "x", [20, 50, 100, 200, 400])
        logticks(ax, "y", [0.3, 1, 3, 10, 30])

    fig.tight_layout(w_pad=1.3)
    for out in args.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
        print(f"saved {_rel(out)} ({out.stat().st_size} bytes)")
        if args.png:
            fig.savefig(out.with_suffix(".png"), bbox_inches="tight",
                        pad_inches=0.02)
    plt.close(fig)

    print(f"seeds {seeds}; max p90 vs measured K=1 oracle {max(p90s):.2f} "
          f"vs diagnostic bound {bound:.1f}")
    n_hold = sum(1 for s in seeds for r in f4[s]["rows"]
                 if r["p90_bound_holds"])
    print(f"p90 bound holds in {n_hold}/{len(seeds)*len(f4[seeds[0]]['rows'])} "
          f"(seed, cell) pairs")


if __name__ == "__main__":
    main()
