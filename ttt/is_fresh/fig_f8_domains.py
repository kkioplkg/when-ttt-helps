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
from matplotlib.ticker import (FixedLocator, NullFormatter,  # noqa: E402
                               SymmetricalLogLocator)

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
    # AUTHORED AT PRINT SIZE.  Included at width=0.90\textwidth = 5.85 in in a
    # cas-sc article whose \textwidth is 469.755 pt = 6.50 in.  Authored 6.9 in
    # wide (saved bbox 6.09 in) the reduction was 0.96, which is close enough
    # that the axis furniture survived, but the two per-panel read-out lines
    # were set at 6.6 / 6.4 pt and therefore printed at 6.3 / 6.2 pt -- right on
    # the floor, and the reason a reader of the built PDF reported them as too
    # small.  `figsize` below now matches the printed width, and the read-outs
    # are set at the same size as the rest of the figure's prose.
    "font.size": 8.5, "axes.titlesize": 8.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.6,
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

    # The per-panel correlation read-outs of (a)-(d) are set ABOVE the axes,
    # between the panel title and the top spine, rather than inside the data
    # box.  Inside they landed on the scatter -- in (d) a document marker fell
    # between the digits of "0.88" and made it read as "0,88" -- and there is
    # no corner of these rising clouds that is reliably empty in all four
    # domains.  HEIGHT IS CAPPED, NOT GROWN, to pay for that band: this float
    # is included at 0.90\textwidth and \topfraction is 0.7, so a taller
    # figure gets DEFERRED by LaTeX and drags every later float behind it
    # (the same failure the Figure 1 generator documents).  The band is
    # therefore taken out of the panels, which stay well above the size at
    # which a 500-document scatter stops reading.
    fig = plt.figure(figsize=(6.62, 5.45))
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
        # TICK LABELS ARE PLACED BY ARITHMETIC, NOT BY A LOCATOR.  These panels
        # are ~1.0 in wide on the page and carry ~5.2 decade-widths, i.e. about
        # 0.19 in per decade, while "10^0" set at 7.5 pt is 0.19 in wide and
        # "-10^-2" is 0.35 in: ANY two labels less than two decades apart touch.
        # The symlog linear window is one decade wide in total, so the locator's
        # own choice -- 0 together with +/-10^-2 at the window edges -- put three
        # labels inside 0.19 in and they overprinted each other (at the
        # published, smaller point size "-10^-2" and "0" already ran together).
        # The fixed set below is the densest one that clears: -10^-1 is two
        # decade-widths left of 0 and 10^0 is two and a half to its right.
        # -10^-1 falls outside the data range in three of the four domains and
        # simply does not draw there.  Minor ticks keep every decade marked.
        ax.xaxis.set_major_locator(FixedLocator([-1e-1, 0.0, 1e0]))
        ax.xaxis.set_minor_locator(
            SymmetricalLogLocator(linthresh=1e-2, base=10))
        ax.xaxis.set_minor_formatter(NullFormatter())
        if dom in ("code", "pubmed"):          # heavy-tailed gains
            ax.set_yscale("symlog", linthresh=0.02)
            ax.set_yticks([-0.01, 0, 0.01, 0.1, 1])
        ax.axhline(0, color=MUTED, lw=0.7, ls=":")
        ax.axvline(0, color=MUTED, lw=0.7, ls=":")
        ci = d30["ci_cluster_nested"]["alignment_only"]
        full = d30["rho_pooled_rows"]["phase_v2"]
        # THE READ-OUT IS STACKED, NOT STRUNG OUT.  On one line at the enlarged
        # size "rho_s = 0.68  [0.62, 0.73]" is 1.19 in against a 1.0 in panel,
        # so consecutive panels' read-outs closed to within a hair of touching.
        # Breaking after the point estimate puts the widest line at 0.65 in,
        # well inside the panel, and costs one more line of the band.
        ax.set_title(f"({'abcd'[k]}) {LABEL[dom]}", pad=31)
        ax.annotate(rf"$\rho_s = {rho:.2f}$"
                    + f"\n[{ci['lo']:.2f}, {ci['hi']:.2f}]",
                    xy=(0.5, 1.085), xycoords="axes fraction", ha="center",
                    va="bottom", fontsize=7.5, color=INK, linespacing=1.15)
        ax.annotate(f"full stat. {full:.2f}",
                    xy=(0.5, 1.005), xycoords="axes fraction", ha="center",
                    va="bottom", fontsize=7.3, color=GREY)
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
        # The two classes this panel separates -- interval strictly on the
        # alignment side vs. interval covering zero -- must not be encoded by
        # ink colour alone, which is invisible in a grayscale print.  Resolved
        # rows get a heavier bar and a FILLED marker; unresolved rows get a
        # lighter bar and a HOLLOW marker.
        resolved = pd["lo"] > 0
        col = INK if resolved else GREY
        axd.plot([pd["lo"], pd["hi"]], [yv, yv], color=col,
                 lw=1.6 if resolved else 1.0, solid_capstyle="round")
        axd.plot([pt], [yv], marker="o", ms=4.4 if resolved else 4.8,
                 color=col, linestyle="none",
                 markerfacecolor=col if resolved else "white",
                 markeredgecolor=col, markeredgewidth=1.1)
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
