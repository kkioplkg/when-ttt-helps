#!/usr/bin/env python
"""Figure 8 -- GPT-2 domain shift, redrawn around the ALIGNMENT-ONLY statistic.

REPLACES the published F8_domains.pdf, whose four panels plotted the full
phase statistic alpha|alpha| delta_v2 / sigma^2 and annotated its
correlations (0.58-0.90) as the headline result, even though the repository's
own leave-one-domain-out analysis (f12, whose interval endpoints are now
f31's) concludes that the shift factor delta_v2 adds no CONSISTENT
incremental benefit -- its partial correlation given alignment is resolved
positive in PubMed and resolved negative in code, and unresolved in the other
two -- and that the alignment factor alone is what transfers.

What the redrawn figure shows
  (a)-(d)  one panel per domain: the ALIGNMENT-ONLY statistic
           alpha|alpha| / sigma^2 against the realized per-document CE gain
           at the label-free selected stop.  NOTE ON LABELS: no axis label,
           title or annotation in this figure names the selection rule or
           any system -- the y-axis reads only "CE gain at the selected
           stop" -- and the rule itself is specified in full in supplement
           section S6.3, so nothing about it is withheld.  Keep the label
           neutral if this generator is edited.  Each panel carries both
           correlations -- the
           alignment-only value as the headline and the full statistic's
           value directly underneath in grey -- so the comparison is on the
           figure, not only in the text.  The sign structure is visible:
           documents with negative alignment sit at negative x and do not
           gain.
  (e)      per-domain Spearman with document-clustered 95% intervals for all
           three statistics side by side -- alignment-only, the full
           statistic, and delta_v2 on its own -- which is the comparison the
           figure has to make.
  (f)      the PAIRED difference rho(alignment) - rho(full), computed inside
           each bootstrap resample so the two statistics see the same
           documents.  This is the panel that carries the simplification
           claim: dropping delta_v2 never costs anything, and in three of
           four domains the interval lies strictly on the alignment side.

All numbers come from f30_e4_alignment_pooled.py, which re-analyses the
ORIGINAL E4/E5 records with f29's document-clustered protocol (500 document
clusters, three adaptation seeds nested, five B = 2000 streams with
bootstrap seeds 20260811-20260815, POOLED into one 10,000-draw distribution
per quantity).  Every interval drawn below is therefore a single 2.5/97.5
percentile pair of ONE bootstrap distribution, which is what the panel
annotations, the (e) axis label and the Figure 8 caption say it is.  The
superseded f17_e4_alignment_only.py reported the arithmetic mean of the
five per-stream percentile endpoints instead; a mean of percentile
endpoints is not a percentile of anything, and this figure annotated it as
a 95% interval.  The scatter is
recomputed here from the same records and its Spearman values are asserted
against f30 before anything is drawn.

Data
    experiments/results/e4/{domain}_ln_s{0,1,2}.json
    experiments/results/e5/delta_v2_{domain}.json
    experiments/results/is_fresh/f30_e4_alignment_pooled.json

Usage: python fig_f8_domains.py [--out PATH ...] [--png]
Defaults write paper/is/paper/figures/F8_domains.pdf.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import SymmetricalLogLocator  # noqa: E402

import common as C  # noqa: E402
import f11_e4_cluster_ci as F11  # noqa: E402

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

OUT_DEFAULT = [ROOT / "paper" / "is" / "paper" / "figures" / "F8_domains.pdf"]

DOMAINS = ["code", "legal", "pubmed", "wikitext"]
LABEL = {"code": "code", "legal": "legal", "pubmed": "PubMed",
         "wikitext": "WikiText"}

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
BASE = "#c3c2b7"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
ORANGE = "#eb6834"
RED = "#e34948"
GREY = "#8c8b85"

COLORS = {"wikitext": BLUE, "pubmed": AQUA, "legal": VIOLET, "code": ORANGE}
STAT_STYLE = {
    "alignment_only": (INK, "o",
                       r"alignment only $\alpha_{\rm sgn}|\alpha_{\rm sgn}|/\sigma^2_{\rm rel}$"),
    "phase_v2": (GREY, "s",
                 r"full statistic $\alpha_{\rm sgn}|\alpha_{\rm sgn}|\,\delta_{v2}/\sigma^2_{\rm rel}$"),
    "delta_v2_only": (RED, "^", r"shift factor only $\delta_{v2}$"),
}

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 300, "pdf.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 8.5, "axes.titlesize": 8.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.2,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False,
})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, nargs="*", default=OUT_DEFAULT)
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()

    f30 = json.loads((Path(C.RESULTS_DIR) / "f30_e4_alignment_pooled.json")
                     .read_text(encoding="utf-8"))
    # The record must be the POOLED one.  A figure that annotates averaged
    # endpoints as a percentile interval misnames its own construction, so
    # the property every interval below asserts is checked before anything is
    # drawn.
    assert f30["n_pooled_draws"] == 10000, f30.get("n_pooled_draws")
    assert "no averaging of endpoints" in f30["protocol"], f30["protocol"]
    recs = F11.load_e4()

    fig = plt.figure(figsize=(6.9, 5.45))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 1.0],
                          hspace=0.62, wspace=0.42)

    # ------------------------------------------------ (a)-(d) scatter panels
    for k, dom in enumerate(DOMAINS):
        ax = fig.add_subplot(gs[0, k])
        rows = F11._flatten(recs[dom])
        x = np.array([r["alpha"] * abs(r["alpha"]) / r["sigma2_rel"]
                      for r in rows], float)
        y = np.array([r["gain"] for r in rows], float)
        rho = F11.spearman(x, y)
        d30 = f30["domains"][dom]
        assert abs(rho - d30["rho_pooled_rows"]["alignment_only"]) < 5e-4, (
            dom, rho, d30["rho_pooled_rows"]["alignment_only"])

        ax.scatter(x, y, s=4.5, color=COLORS[dom], alpha=0.32, linewidths=0,
                   rasterized=True)
        ax.set_xscale("symlog", linthresh=1e-2)
        # two-decade ticks: the panels are 1.5 in wide and 10^k labels collide
        ax.xaxis.set_major_locator(
            SymmetricalLogLocator(linthresh=1e-2, base=100))
        if dom in ("code", "pubmed"):          # heavy-tailed gains
            ax.set_yscale("symlog", linthresh=0.02)
            ax.set_yticks([-0.01, 0, 0.01, 0.1, 1])
        ax.axhline(0, color=MUTED, lw=0.7, ls=":")
        ax.axvline(0, color=MUTED, lw=0.7, ls=":")
        ci = d30["ci_cluster_nested"]["alignment_only"]
        full = d30["rho_pooled_rows"]["phase_v2"]
        ax.set_title(f"({'abcd'[k]}) {LABEL[dom]}", pad=3)
        ax.annotate(rf"$\rho_s = {rho:.2f}$" + "\n"
                    + f"[{ci['lo']:.2f}, {ci['hi']:.2f}]",
                    xy=(0.04, 0.97), xycoords="axes fraction", va="top",
                    fontsize=7.4, color=INK)
        ax.annotate(f"full stat. {full:.2f}",
                    xy=(0.04, 0.79), xycoords="axes fraction", va="top",
                    fontsize=6.8, color=GREY)
        if k == 0:
            ax.set_ylabel("CE gain at the selected index")
        ax.set_xlabel(r"$\alpha_{\rm sgn}|\alpha_{\rm sgn}|/\sigma^2_{\rm rel}$", labelpad=1)
        print(f"{dom}: alignment-only rho={rho:.3f} "
              f"[{ci['lo']:.3f}, {ci['hi']:.3f}]  full={full:.3f}  "
              f"n={len(x)} rows / {d30['n_documents']} documents")

    # ------------------------------------------------ (e) forest of the three
    axf = fig.add_subplot(gs[1, :3])
    ys = np.arange(len(DOMAINS))[::-1]
    off = {"alignment_only": 0.24, "phase_v2": 0.0, "delta_v2_only": -0.24}
    for stat, (col, mk, lab) in STAT_STYLE.items():
        first = True
        for yv, dom in zip(ys, DOMAINS):
            d30 = f30["domains"][dom]
            r = d30["rho_pooled_rows"][stat]
            ci = d30["ci_cluster_nested"][stat]
            yy = yv + off[stat]
            axf.plot([ci["lo"], ci["hi"]], [yy, yy], color=col, lw=1.3,
                     solid_capstyle="round", alpha=0.9)
            axf.plot([r], [yy], marker=mk, ms=4.2, color=col,
                     label=lab if first else None, linestyle="none")
            first = False
    axf.axvline(0, color=MUTED, lw=0.7, ls=":")
    axf.set_yticks(ys)
    axf.set_yticklabels([LABEL[d] for d in DOMAINS])
    axf.set_ylim(-0.6, len(DOMAINS) - 0.4)
    axf.set_xlim(-0.55, 1.0)
    # LABEL LENGTH IS A LAYOUT CONSTRAINT.  This axes spans three of four
    # gridspec columns, so a centred x-label wider than that span runs off
    # the figure on the left and collides with panel (f)'s x-label on the
    # right; neither shows up in the LaTeX log, because both are inside the
    # figure PDF.  The interval's construction -- 500 document clusters, a
    # 95% percentile pair read off one pooled 10,000-draw bootstrap -- is
    # stated in full in the caption, so naming the axis is enough here.
    axf.set_xlabel(r"Spearman $\rho_s$ with realized gain")
    axf.set_title("(e) per-domain association by diagnostic component",
                  pad=4)
    axf.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3,
               handletextpad=0.35, columnspacing=1.4, borderaxespad=0.0)

    # ------------------------------------------------ (f) paired difference
    axd = fig.add_subplot(gs[1, 3])
    for yv, dom in zip(ys, DOMAINS):
        pd = f30["domains"][dom]["paired_diff_alignment_minus_full"][
            "cluster_nested"]
        pt = f30["domains"][dom]["paired_diff_alignment_minus_full"][
            "point_pooled_rows"]
        col = INK if pd["lo"] > 0 else GREY
        axd.plot([pd["lo"], pd["hi"]], [yv, yv], color=col, lw=1.3,
                 solid_capstyle="round")
        axd.plot([pt], [yv], marker="o", ms=4.2, color=col, linestyle="none")
    axd.axvline(0, color=RED, lw=0.8, ls="--")
    axd.set_yticks(ys)
    axd.set_yticklabels([])
    axd.set_ylim(-0.6, len(DOMAINS) - 0.4)
    axd.set_xlabel(r"$\rho_s$(align) $-$ $\rho_s$(full)")
    axd.set_title("(f) paired difference", pad=4)

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
