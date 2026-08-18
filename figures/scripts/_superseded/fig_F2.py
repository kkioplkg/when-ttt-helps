"""F2 (HERO): measured phase diagram of single-instance TTT.

Heatmap of realized relative gain of optimally-stopped TTT over the frozen
model on the (alpha, delta/sigma) grid, with the theoretical phase boundary
alpha^2 delta^2 / sigma^2 = eta/2 (white solid) and the threshold fitted to
the data (dashed) overlaid.

Data: experiments/results/e1/e1_b_seed42.json
  alphas[25], ratios[25] (= delta/sigma, log-spaced), gain[25][25]
  (gain[i][j]: alpha_i, ratio_j; absolute risk improvement, sigma=1),
  fitted_threshold, holdout_accuracy.
eta is not recorded in part b (see SCHEMAS.md); it is read from part a of
the same seed (e1_a_seed42.json).
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

SRC_B = st.RESULTS / "e1" / "e1_b_seed42.json"
SRC_A = st.RESULTS / "e1" / "e1_a_seed42.json"


def main():
    b = json.loads(SRC_B.read_text())
    eta = json.loads(SRC_A.read_text())["eta"]
    alphas = np.array(b["alphas"])
    ratios = np.array(b["ratios"])
    gain = np.array(b["gain"])                     # [alpha, ratio]
    thr_fit = b["fitted_threshold"]
    thr_theory = eta / 2.0

    # orientation sanity check against recorded phase_stat
    ps = np.array(b["phase_stat"])
    assert np.allclose(ps, (alphas[:, None] * ratios[None, :]) ** 2), \
        "gain grid orientation does not match phase_stat"

    # relative gain: fraction of frozen risk (delta^2, sigma=1) removed
    rel = gain / (ratios[None, :] ** 2)
    rel = np.clip(rel, 0.0, 1.0)

    fig, ax = plt.subplots(figsize=(st.SINGLE, 4.0))
    ax.grid(False)
    # log-spaced ratios: pcolormesh with true cell edges on a log y-axis
    def edges(v, log=False):
        v = np.log10(v) if log else v
        e = np.concatenate([[v[0] - (v[1] - v[0]) / 2],
                            (v[:-1] + v[1:]) / 2,
                            [v[-1] + (v[-1] - v[-2]) / 2]])
        return 10 ** e if log else e

    pm = ax.pcolormesh(edges(alphas), edges(ratios, log=True), rel.T,
                       cmap="viridis", norm=Normalize(0, 1),
                       rasterized=False, shading="flat")
    ax.set_yscale("log")

    # The eta -> 0 flow limit alpha^2 (delta/sigma)^2 = eta/2 is NOT the
    # exact boundary of either phase criterion; the criterion that governs
    # the measured integer-step gains is eq:phaseint, whose threshold in
    # the coordinate alpha^2 delta^2 / sigma^2 is eta / (2 - alpha^2 eta)
    # and runs from eta/2 at alpha=0 to eta/(2-eta) at alpha=1. Plot that
    # as a BAND, not a line, and label the flow limit as a flow limit.
    aa = np.linspace(alphas[0], alphas[-1], 400)
    thr_int = eta / (2.0 - aa ** 2 * eta)          # integer-condition
    rr_flow = np.sqrt(thr_theory) / aa
    rr_int = np.sqrt(thr_int) / aa
    band = ((np.minimum(rr_flow, rr_int) <= ratios[-1])
            & (np.maximum(rr_flow, rr_int) >= ratios[0]))
    ax.fill_between(aa[band],
                    np.clip(np.minimum(rr_flow, rr_int)[band],
                            ratios[0], ratios[-1]),
                    np.clip(np.maximum(rr_flow, rr_int)[band],
                            ratios[0], ratios[-1]),
                    color="white", alpha=0.45, lw=0, zorder=4,
                    label=(r"integer-condition band "
                           r"$[%.5f,\,%.5f]$, width $%.1f\%%$"
                           % (thr_theory, eta / (2.0 - eta),
                              100 * (eta / (2.0 - eta) / thr_theory - 1))))
    m_int = (rr_int >= ratios[0]) & (rr_int <= ratios[-1])
    ax.plot(aa[m_int], rr_int[m_int], ls=(0, (1, 2)), color="white",
            lw=1.2, zorder=5,
            label=(r"integer condition: "
                   r"$\alpha^2\delta^2/\sigma^2=\eta/(2-\alpha^2\eta)$"))
    for thr, ls, color, lw, label in [
            (thr_theory, "-", "white", 1.6,
             r"flow limit: $\alpha^2\delta^2/\sigma^2=\eta/2$"),
            (thr_fit, (0, (4, 3)), st.YELLOW, 1.8,
             "fitted threshold (%.5f)" % thr_fit)]:
        rr = np.sqrt(thr) / aa
        m = (rr >= ratios[0]) & (rr <= ratios[-1])
        ax.plot(aa[m], rr[m], ls=ls, color=color, lw=lw, label=label,
                zorder=5)

    ax.set_xlabel(r"alignment $\alpha$")
    ax.set_ylabel(r"shift-to-noise ratio  $\delta/\sigma$")
    ax.set_xlim(edges(alphas)[0], edges(alphas)[-1])
    leg = ax.legend(loc="upper right", frameon=False, fontsize=7.5,
                    handlelength=2.2)
    for txt in leg.get_texts():
        txt.set_color("white")
    cb = fig.colorbar(pm, ax=ax, pad=0.02)
    cb.set_label("fraction of frozen risk removed\nby optimally-stopped TTT")
    cb.outline.set_visible(False)
    fig.tight_layout()
    st.save(fig, "F2_phase")
    print(f"eta={eta}, theory thr={thr_theory}, fitted={thr_fit:.6f}, "
          f"ratio={thr_fit / thr_theory:.4f}, holdout={b['holdout_accuracy']}")


if __name__ == "__main__":
    main()
