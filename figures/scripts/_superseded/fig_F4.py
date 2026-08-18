"""F4: E2 cell-level phase statistic vs realized gain (CIFAR-10/100-C).

Panels (a) ttt_rot and (b) ttt_mask: x = cell-mean feature-proxy phase
statistic alpha*|alpha|*delta_feat/sigma^2 (E5 join, PRIMARY), symlog;
y = cell-mean final-step loss gain (frozen loss - adapted loss).
Panel (c), smaller: tent/pl with the loss-proxy statistic -- deterministic
objectives that violate persistent alignment (A2) along the trajectory;
their correlation is strongly NEGATIVE (theory-boundary evidence, not a C2
gate). Spearman rho annotated per panel is computed from the plotted cells
and cross-checked against the aggregator's values in summary_final.json.

Data: experiments/results/summary_final.json -> milestones.e2_main
      (cells: per (dataset, method, corruption, severity) aggregates;
       correlations: per-method spearman tables).
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

SRC = st.RESULTS / "summary_final.json"


def cells_of(cells, method):
    return [c for c in cells if c["method"] == method]


def main():
    s = json.loads(SRC.read_text())
    e2 = s["milestones"]["e2_main"]
    cells = e2["cells"]
    corr = {c["group"]: c for c in e2["correlations"]}

    fig = plt.figure(figsize=(st.FULL, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.95],
                          wspace=0.55)

    # ---- stochastic SSL methods: feature-proxy phase stat (primary) ----
    for k, (method, color, lthr) in enumerate(
            [("ttt_rot", st.BLUE, 1e-3), ("ttt_mask", st.AQUA, 1e-4)]):
        ax = fig.add_subplot(gs[0, k])
        cs = cells_of(cells, method)
        x = np.array([c["mean_phase_feat"] for c in cs])
        y = np.array([c["gain_final"] for c in cs])
        rho = st.spearman(x, y)
        ref = corr[method]["spearman_feat_mean_final"]
        assert abs(rho - ref) < 1e-6, (method, rho, ref)
        for ds, mk in [("cifar10", "o"), ("cifar100", "s")]:
            m = np.array([c["dataset"] == ds for c in cs])
            ax.scatter(x[m], y[m], s=16, marker=mk, color=color, alpha=0.75,
                       linewidths=0, label=f"CIFAR-{ds[5:]}-C")
        ax.set_xscale("symlog", linthresh=lthr)
        ax.set_xticks([-10 * lthr, 0, 10 * lthr] +
                      ([100 * lthr] if method == "ttt_rot" else []))
        ax.axhline(0, color=st.MUTED, lw=0.7, ls=":")
        ax.set_title(f"({'ab'[k]}) {method}", pad=4)
        ax.annotate(rf"$\rho_s = {rho:.2f}$" + f"\n({len(cs)} cells)",
                    xy=(0.04, 0.96), xycoords="axes fraction", va="top",
                    fontsize=8.5, color=st.INK)
        ax.set_xlabel(r"phase stat. $\alpha|\alpha|\,\delta_{\rm feat}/\sigma^2$")
        if k == 0:
            ax.set_ylabel("loss gain (final step)")
            ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.02),
                      handletextpad=0.1, borderaxespad=0.2)

    # ---- deterministic objectives: theory boundary (A2 violated) ----
    ax = fig.add_subplot(gs[0, 2])
    for method, color, mk in [("tent", st.RED, "o"), ("pl", st.ORANGE, "s")]:
        cs = cells_of(cells, method)
        x = np.array([c["mean_phase_stat"] for c in cs])
        y = np.array([c["gain_final"] for c in cs])
        rho = st.spearman(x, y)
        ref = corr[method]["spearman_mean_final"]
        assert abs(rho - ref) < 1e-6, (method, rho, ref)
        ax.scatter(x, y, s=14, marker=mk, color=color, alpha=0.7,
                   linewidths=0,
                   label=rf"{method}  ($\rho_s={rho:.2f}$)")
    ax.set_xscale("symlog", linthresh=1e-2)
    ax.set_yscale("symlog", linthresh=0.1)
    ax.set_xticks([-0.1, 0, 0.1, 1])
    ax.set_yticks([0, -0.1, -1, -10, -100])
    ax.axhline(0, color=st.MUTED, lw=0.7, ls=":")
    ax.set_title("(c) theory boundary\n(A2 violated along trajectory)",
                 pad=4, fontsize=8.5)
    ax.set_xlabel(r"loss-proxy stat. $\alpha^2\delta_{\rm loss}$")
    ax.set_ylabel("loss gain (final step)")
    ax.legend(loc="lower left", handletextpad=0.1, borderaxespad=0.2)

    st.save(fig, "F4_e2_phase")
    for m in ["ttt_rot", "ttt_mask", "tent", "pl"]:
        c = corr[m]
        print(f"{m}: feat mean final={c['spearman_feat_mean_final']:.3f} "
              f"best={c['spearman_feat_mean_best']:.3f} | loss mean "
              f"final={c['spearman_mean_final']:.3f} "
              f"best={c['spearman_mean_best']:.3f}")


if __name__ == "__main__":
    main()
