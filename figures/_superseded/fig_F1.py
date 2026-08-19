"""F1: exact-model risk curves E(t), simulation vs closed form.

2x2 grid of representative (alpha, delta) cells from e1 part a.
Data: experiments/results/e1/e1_a_seed42.json
  grid entries carry "emp" and "theory" arrays (risk vs t, length T+1).
Theory = dashed black; empirical = colored solid.
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

SRC = st.RESULTS / "e1" / "e1_a_seed42.json"
CELLS = [(0.25, 1.0), (0.25, 4.0), (1.0, 1.0), (1.0, 4.0)]


def main():
    data = json.loads(SRC.read_text())
    grid = {(g["alpha"], g["delta"]): g for g in data["grid"]}
    for c in CELLS:
        assert c in grid, f"cell {c} missing from {SRC}"

    fig, axes = plt.subplots(2, 2, figsize=(st.SINGLE, 4.1), sharex=True)
    for ax, (a, d) in zip(axes.ravel(), CELLS):
        g = grid[(a, d)]
        t = np.arange(len(g["emp"]))
        ax.plot(t, g["emp"], color=st.BLUE, lw=1.8, label="simulation",
                zorder=3)
        ax.plot(t, g["theory"], color=st.INK, lw=1.2, ls="--",
                label="theory (closed form)", zorder=4)
        ax.axhline(d ** 2, color=st.MUTED, lw=0.8, ls=":", zorder=2)
        ax.set_title(rf"$\alpha={a}$,  $\delta/\sigma={d:g}$", pad=3)
        ax.annotate(f"max rel. err {g['max_rel_err'] * 100:.1f}%",
                    xy=(0.97, 0.06), xycoords="axes fraction",
                    ha="right", va="bottom", fontsize=7.5, color=st.INK2)
        ax.margins(x=0)
    # frozen-risk reference label once (top-left panel: line at delta^2 = 1)
    axes[0, 0].annotate(r"frozen risk $\delta^2$", xy=(0.5, 0.90),
                        xycoords="axes fraction", fontsize=7.5,
                        color=st.MUTED, ha="center")
    axes[0, 0].legend(loc="center right", handlelength=1.8)
    for ax in axes[1]:
        ax.set_xlabel("adaptation step $t$")
    for ax in axes[:, 0]:
        ax.set_ylabel("excess risk $E(t)$")
    fig.tight_layout(h_pad=0.9, w_pad=1.0)
    st.save(fig, "F1_curves")
    print(f"worst_rel_err (all 30 cells): {data['worst_rel_err']:.4f}")


if __name__ == "__main__":
    main()
