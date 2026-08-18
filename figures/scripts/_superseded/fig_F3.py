"""F3: ALTA adaptive stopping vs the oracle (e1 part d).

(a) median stopping time t_hat vs oracle t* across the 16 (alpha, delta)
    cells, log-log, with the y=x diagonal.
(b) per-cell p90 realized-risk ratio (realized / oracle risk) vs t*, with
    the Theorem 5 multiplicative bound 3 log T_max as a reference line
    (the additive eta*sigma^2 term only loosens it).

Data: experiments/results/e1/e1_d_seed42.json (seed 42)
      experiments/results/e5/e1_d_seed43.json (seed 43, robustness overlay)
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

SRC42 = st.RESULTS / "e1" / "e1_d_seed42.json"
SRC43 = st.RESULTS / "e5" / "e1_d_seed43.json"


def main():
    d42 = json.loads(SRC42.read_text())
    d43 = json.loads(SRC43.read_text())
    bound = 3.0 * d42["log_Tmax"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(st.SINGLE, 2.7))

    seeds = [(d42, "o", st.BLUE, "seed 42", "full"),
             (d43, "^", st.ORANGE, "seed 43", "none")]

    # --- (a) median t_hat vs t* ---
    lims = [5, 600]
    ax1.plot(lims, lims, color=st.MUTED, lw=0.8, ls=":", zorder=1)
    for d, mk, c, lab, fill in seeds:
        ts = [r["t_star"] for r in d["rows"]]
        th = [r["median_t_hat"] for r in d["rows"]]
        ax1.scatter(ts, th, marker=mk, s=26, zorder=3, label=lab,
                    facecolors=(c if fill == "full" else "none"),
                    edgecolors=c, linewidths=1.2)
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlim(*lims)
    ax1.set_ylim(*lims)
    ax1.set_xlabel(r"truncated oracle $t^\ast_T$")
    ax1.set_ylabel(r"median selected step $\hat t$")
    ax1.annotate(r"$\hat t = t^\ast_T$", xy=(200, 260), fontsize=8,
                 color=st.MUTED, rotation=38)
    ax1.set_title("(a) selected step", pad=4)
    ax1.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.2)

    # --- (b) realized-risk ratio vs t* ---
    for d, mk, c, lab, fill in seeds:
        ts = [r["t_star"] for r in d["rows"]]
        p90 = [r["p90_risk_ratio"] for r in d["rows"]]
        med = [r["median_risk_ratio"] for r in d["rows"]]
        ax2.scatter(ts, p90, marker=mk, s=26, zorder=3,
                    facecolors=(c if fill == "full" else "none"),
                    edgecolors=c, linewidths=1.2)
        ax2.scatter(ts, med, marker=mk, s=12, zorder=2, alpha=0.45,
                    facecolors=(c if fill == "full" else "none"),
                    edgecolors=c, linewidths=0.8)
    ax2.axhline(bound, color=st.RED, lw=1.2, ls="--", zorder=2)
    ax2.annotate(r"diagnostic bound $3\log T$", xy=(0.97, bound * 0.82),
                 xycoords=("axes fraction", "data"), ha="right", va="top",
                 fontsize=8, color=st.RED)
    ax2.axhline(1.0, color=st.MUTED, lw=0.8, ls=":", zorder=1)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"truncated oracle $t^\ast_T$")
    ax2.set_ylabel(r"risk / oracle risk")
    ax2.set_title("(b) realized risk (p90, median)", pad=4)
    ax2.set_ylim(0.2, 40)
    from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter
    for ax in (ax1, ax2):
        ax.xaxis.set_major_locator(FixedLocator([20, 50, 100, 200, 400]))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
    ax1.yaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200, 400]))
    ax1.yaxis.set_major_formatter(ScalarFormatter())
    ax1.yaxis.set_minor_formatter(NullFormatter())
    ax2.yaxis.set_major_locator(FixedLocator([0.3, 1, 3, 10, 30]))
    ax2.yaxis.set_major_formatter(ScalarFormatter())
    ax2.yaxis.set_minor_formatter(NullFormatter())

    fig.tight_layout(w_pad=1.6)
    st.save(fig, "F3_alta")
    n_safe = sum(r["safe_vs_frozen"] for r in d42["rows"])
    print(f"seed42: p90 max {max(r['p90_risk_ratio'] for r in d42['rows']):.2f}"
          f" vs bound {bound:.1f}; safety {n_safe}/{len(d42['rows'])}")


if __name__ == "__main__":
    main()
