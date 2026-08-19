#!/usr/bin/env python
"""Figure 2 -- the measured phase diagram of single-instance TTT, in three
panels that keep the three different questions apart.

WHY THREE PANELS
----------------
The published single-panel Figure 2 coloured its grid with the realized gain of
a SPLIT-SELECTED stopping rule while its caption described it as the oracle
phase of Theorem 1.  Those are different objects, and conflating them made the
panel unable to test the theorem it was presented as testing:

  * a true oracle has t = 0 on its menu, so its gain is non-negative by
    construction; every negative cell in the published panel was therefore
    stopping-selection error, not "TTT hurts";
  * the genuinely signed, theorem-matched quantity -- the one-step gain -- was
    never plotted;
  * the overlaid boundary was the flow-limit form alpha^2 delta^2/sigma^2 =
    eta/2, not the exact discrete condition.

So the three questions are now three panels, each with the quantity that
actually answers it:

  (a) ONE-STEP SIGN STRUCTURE.  G1 = delta^2 - E_B[u_1^2], a diverging map
      centred at zero.  This is where genuine harm lives: about 180 of the 625
      cells measure negative, ~139 of them resolved at three Monte-Carlo
      standard errors.  The white curve is the EXACT discrete one-step boundary
      alpha^2 delta^2 (2 - eta alpha^2) = sigma^2 eta, derived from Theorem 1's
      closed form; the dotted curve is its small-step simplification
      alpha^2 delta^2/sigma^2 = eta/2, plotted so the reader can see how much
      the approximation moves the line.
  (b) MEASURED ORACLE GAIN.  Gora = max_{0<=t<=T} (delta^2 - E_B[u_t^2]), a
      sequential map starting at zero -- non-negative everywhere BY
      CONSTRUCTION, and labelled as such.  What the boundary separates here is
      not help from harm but "the oracle adapts" from "the oracle declines"
      (t = 0 chosen in about 174 cells).  Overlays as in (a), with the exact
      finite-horizon boundary min_t Exc(t) = delta^2 solved numerically.
  (c) SELECTION ERROR.  Gsel - Gora <= 0 identically, where Gsel is the gain of
      the split-selected stopping rule.  This panel, and only this panel, is
      what the published figure was actually showing.

All three are measured on the SAME replicates of the same simulation, so (c) is
literally (its own selected gain) minus (b), cell by cell.

Data: experiments/results/is_fresh/f10_oracle_grid_summary.json
Usage: python fig_f2_phase.py [--data PATH] [--out PATH ...] [--png]
Defaults write paper/is/paper/figures/F2_phase.pdf.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

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

DATA = ROOT / "results" / "is_fresh" / "f10_oracle_grid_summary.json"
OUT_DEFAULT = [ROOT / "paper" / "is" / "paper" / "figures" / "F2_phase.pdf"]

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
BASE = "#c3c2b7"

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


def _edges(values: np.ndarray, log: bool = False) -> np.ndarray:
    v = np.log10(values) if log else np.asarray(values, dtype=float)
    mid = 0.5 * (v[:-1] + v[1:])
    edges = np.concatenate([[v[0] - (mid[0] - v[0])], mid,
                            [v[-1] + (v[-1] - mid[-1])]])
    return 10.0 ** edges if log else edges


def curve(d, name):
    pts = d["theory_boundaries"][name]
    return (np.array([p["alpha"] for p in pts], float),
            np.array([p["delta_over_sigma"] for p in pts], float))


def overlay(ax, d, exact_key, thr, alphas, show_labels):
    """Exact boundary (solid white), flow simplification (dotted), and the
    measured single-threshold fit with its across-seed band."""
    a_fine = np.linspace(alphas.min(), alphas.max(), 400)
    lo = np.sqrt(thr["min"]) / a_fine
    hi = np.sqrt(thr["max"]) / a_fine
    # 1. exact discrete boundary (thick white with a dark halo, drawn first so
    #    the two comparison lines stay legible on top of it)
    ea, er = curve(d, exact_key)
    ax.plot(ea, er, color="white", lw=2.4, zorder=5, solid_capstyle="round",
            path_effects=[pe.withStroke(linewidth=4.0, foreground="#0b0b0b")],
            # The executable one-step criterion is Theorem 9
            # (\ref{thm:integer}) in the manuscript's numbering, which is what
            # the caption and the surrounding text cite; the legend must carry
            # that number and no other.
            label=("exact discrete boundary (Thm. 9)" if show_labels else None))
    # 2. its small-step simplification, the line the published panel overlaid
    fa, fr = curve(d, "boundary_flow")
    ax.plot(fa, fr, color="#ffd23f", lw=1.3, ls=(0, (1.2, 1.3)), zorder=7,
            label=(r"flow limit $\alpha^2\delta^2/\sigma^2=\eta/2$"
                   if show_labels else None))
    # 3. the boundary fitted to the MEASURED signs, with its across-seed band
    ax.fill_between(a_fine, lo, hi, color="#111111", alpha=0.22, lw=0, zorder=6)
    ax.plot(a_fine, np.sqrt(thr["mean"]) / a_fine, ls=(0, (4.5, 2.2)), lw=1.3,
            color="#111111", zorder=8,
            label=("measured boundary (fitted to signs)"
                   if show_labels else None))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--out", type=Path, nargs="*", default=OUT_DEFAULT)
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()

    d = json.loads(args.data.read_text(encoding="utf-8"))
    alphas = np.asarray(d["grid"]["alphas"], float)
    ratios = np.asarray(d["grid"]["ratios_delta_over_sigma"], float)
    frozen = ratios[None, :] ** 2                       # sigma = 1

    g1 = np.asarray(d["gain_onestep"]["mean"], float) / frozen
    gora = np.asarray(d["gain_oracle"]["mean"], float) / frozen
    gsel_err = np.asarray(d["selection_error"]["mean"], float) / frozen

    xe, ye = _edges(alphas), _edges(ratios, log=True)
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.85))

    # ------------------------------------------------------- (a) one-step
    ax = axes[0]
    nb = [-0.05, -0.02, -0.01, -0.005, -0.002, 0.0]
    pb = [0.002, 0.005, 0.01, 0.02, 0.05]
    bounds = nb + pb
    base = plt.get_cmap("RdBu_r")
    cmap = ListedColormap(base(np.linspace(0.03, 0.97, len(bounds) - 1)))
    cmap.set_under(base(0.01))
    cmap.set_over(base(0.99))
    m1 = ax.pcolormesh(xe, ye, g1.T, cmap=cmap,
                       norm=BoundaryNorm(bounds, len(bounds) - 1, clip=False),
                       shading="flat", rasterized=True, linewidth=0)
    AA, RR = np.meshgrid(alphas, ratios, indexing="ij")
    neg = np.asarray(d["gain_onestep"]["max"], float) < 0     # negative at every seed
    ax.scatter(AA[neg], RR[neg], s=2.4, marker="o", facecolors="none",
               edgecolors="#12305c", linewidths=0.4, zorder=3)
    overlay(ax, d, "boundary_onestep_exact",
            d["fitted_threshold_onestep"], alphas, True)
    ax.set_title(r"(a) one-step gain $G_1$ (signed)", pad=4)
    ax.set_ylabel(r"shift-to-noise ratio $\delta/\sigma$")
    cb = fig.colorbar(m1, ax=ax, pad=0.02, spacing="uniform",
                      boundaries=bounds, ticks=[-0.05, -0.01, 0.0, 0.01, 0.05],
                      extend="both")
    cb.set_label(r"rel. to $\delta^2$", fontsize=7.5)

    # --------------------------------------------------------- (b) oracle
    ax = axes[1]
    ob = [0.0, 1e-4, 1e-3, 5e-3, 0.02, 0.08, 0.25, 0.6, 1.0]
    ocm = ListedColormap(plt.get_cmap("YlGnBu")(
        np.linspace(0.08, 0.95, len(ob) - 1)))
    m2 = ax.pcolormesh(xe, ye, gora.T, cmap=ocm,
                       norm=BoundaryNorm(ob, len(ob) - 1, clip=True),
                       shading="flat", rasterized=True, linewidth=0)
    overlay(ax, d, "boundary_oracle_exact",
            d["fitted_threshold_oracle"], alphas, False)
    ax.set_title(r"(b) oracle gain $G_{\rm oracle}\ (\geq 0)$", pad=4)
    cb = fig.colorbar(m2, ax=ax, pad=0.02, spacing="uniform",
                      boundaries=ob, ticks=[0.0, 1e-3, 0.02, 0.25, 1.0])
    cb.set_label(r"rel. to $\delta^2$", fontsize=7.5)
    cb.set_ticklabels(["0", "0.001", "0.02", "0.25", "1.0"])

    # ------------------------------------------------ (c) selection error
    ax = axes[2]
    sb = [-0.05, -0.02, -0.008, -0.003, -1e-3, -3e-4, -1e-4, -1e-5, 0.0]
    scm = ListedColormap(plt.get_cmap("YlOrRd_r")(
        np.linspace(0.05, 0.92, len(sb) - 1)))
    scm.set_under(plt.get_cmap("YlOrRd_r")(0.0))
    m3 = ax.pcolormesh(xe, ye, gsel_err.T, cmap=scm,
                       norm=BoundaryNorm(sb, len(sb) - 1, clip=False),
                       shading="flat", rasterized=True, linewidth=0,
                       )
    ea, er = curve(d, "boundary_oracle_exact")
    ax.plot(ea, er, color="white", lw=1.7, zorder=6, solid_capstyle="round",
            path_effects=[pe.withStroke(linewidth=3.4, foreground="#0b0b0b")])
    ax.set_title("(c) selection error (selected $-$ oracle)", pad=4)
    cb = fig.colorbar(m3, ax=ax, pad=0.02, spacing="uniform",
                      boundaries=sb, ticks=[-0.05, -0.003, -1e-4, 0.0],
                      extend="min")
    cb.set_label(r"rel. to $\delta^2$", fontsize=7.5)
    cb.set_ticklabels(["$-0.05$", "$-0.003$", "$-10^{-4}$", "0"])

    for ax in axes:
        ax.set_yscale("log")
        ax.set_xlim(xe[0], xe[-1])
        ax.set_ylim(ye[0], ye[-1])
        ax.set_xlabel(r"gradient alignment $\alpha$")
        ax.tick_params(labelsize=7.5)
    for ax in axes[1:]:
        ax.set_yticklabels([])

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, 1.0), handlelength=2.2,
               columnspacing=1.6, handletextpad=0.5, labelcolor=INK2)

    fig.tight_layout(w_pad=1.5)
    for out in args.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", pad_inches=0.03)
        print(f"saved {_rel(out)} ({out.stat().st_size} bytes)")
        if args.png:
            fig.savefig(out.with_suffix(".png"), bbox_inches="tight",
                        pad_inches=0.03)
    plt.close(fig)

    def rng(k):
        v = d[k]
        return f"{v['mean']:.4g} (range {v['min']:.4g}-{v['max']:.4g})"

    print("cells:", g1.size)
    print("one-step negative:", rng("n_cells_onestep_negative"),
          "| resolved at 3 SE:", rng("n_cells_onestep_negative_resolved_3se"))
    print("oracle declines (t=0):", rng("n_cells_oracle_declines"),
          "| oracle gain > 0:", rng("n_cells_oracle_positive"))
    print("selected-stopping negative:", rng("n_cells_selected_negative"),
          "| selection error non-zero:", rng("n_cells_selection_error_nonzero"))
    print("selection error rel. frozen: mean", rng("mean_selection_error_rel_frozen"),
          "worst", rng("worst_selection_error_rel_frozen"))
    print("fitted threshold / (eta/2): one-step",
          rng("threshold_ratio_onestep"), "| oracle",
          rng("threshold_ratio_oracle"))
    print("holdout sign accuracy: one-step", rng("holdout_accuracy_onestep"),
          "resolved", rng("holdout_accuracy_onestep_resolved"),
          "| oracle-adapts", rng("holdout_accuracy_oracle"))


if __name__ == "__main__":
    main()
