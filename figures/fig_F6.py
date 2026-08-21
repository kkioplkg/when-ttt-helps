"""F6: entropy alignment alpha_ent and calibration (Theorem 4).

Distribution of the per-episode entropy alignment alpha_ent for confident
predictions (frozen max softmax > 0.7), split by whether the frozen
prediction is correct, with and without temperature scaling.
Theorem 4 (binary form): alpha_ent = sign((p-1/2)(p-q)) -- entropy descent
aligns with the task iff the confident prediction is right.

Data: experiments/results/e2/cifar10_tent_calib_s0.json and
      experiments/results/e2/cifar100_tent_calib_s0.json, POOLED
      (results.cells[*].episodes with alpha_ent/confidence/correct;
       15 corruptions x severity 5 x {temp_scaled False, True}),
      matching the pooled counts quoted in the main text
      (n = 2873 confident-right / 1554 confident-wrong, mean T = 1.19).
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SRCS = [st.RESULTS / "e2" / "cifar10_tent_calib_s0.json",
        st.RESULTS / "e2" / "cifar100_tent_calib_s0.json"]
CONF = 0.7

# TWO-CHANNEL SERIES DISCRIMINATION.  The two groups must be separable in
# grayscale and under colour-vision deficiency, so they differ in colour AND
# dash pattern AND stroke weight AND fill opacity -- not colour alone.  #2a78d6
# and #e34948 have almost the same relative luminance (0.44 vs 0.45), so a
# colour-only encoding collapses completely in a grayscale print.
GROUP_STYLE = {
    1: {"color": st.BLUE, "ls": "-", "lw": 1.7, "fill_alpha": 0.32,
        "label": "confident & right"},
    0: {"color": st.RED, "ls": (0, (3.6, 1.5)), "lw": 1.2, "fill_alpha": 0.18,
        "label": "confident & wrong"},
}


def main():
    temps = []
    groups = {}                     # (temp_scaled, correct) -> [alpha_ent]
    for src in SRCS:
        data = json.loads(src.read_text())
        res = data["results"]
        temps.append(res["temperature"])
        for cell in res["cells"]:
            for ep in cell["episodes"]:
                if ep["confidence"] <= CONF:
                    continue
                key = (cell["temp_scaled"], ep["correct"])
                groups.setdefault(key, []).append(ep["alpha_ent"])
    temp = float(np.mean(temps))    # mean fitted temperature across datasets

    # AUTHORED AT PRINT SIZE, NOT AT st.SINGLE.  This float is included at
    # width=0.70\textwidth = 4.55 in (cas-sc, \textwidth = 469.755 pt =
    # 6.50 in).  Saved from st.SINGLE the bbox was 5.18 in, so LaTeX reduced it
    # by 0.88 and _style's 9/8 pt type reached the page at 7.9/7.0 pt.  4.87 in
    # of canvas saves a ~4.55 in bbox, i.e. a reduction of ~1.0, and _style's
    # sizes arrive intact.  st.SINGLE itself must not be touched: F3 and F7
    # share it and are included at different widths again.
    fig, axes = plt.subplots(1, 2, figsize=(4.87, 2.62), sharey=True,
                             sharex=True)
    bins = np.linspace(-1, 1, 41)
    titles = {False: "(a) raw confidence", True: "(b) temperature-scaled"}
    for ax, ts in zip(axes, [False, True]):
        for correct in (1, 0):
            s = GROUP_STYLE[correct]
            color = s["color"]
            v = np.array(groups[(ts, correct)])
            ax.hist(v, bins=bins, density=True, histtype="stepfilled",
                    color=color, alpha=s["fill_alpha"], lw=0)
            ax.hist(v, bins=bins, density=True, histtype="step",
                    color=color, lw=s["lw"], linestyle=s["ls"])
            frac_neg = float((v < 0).mean())
            ax.annotate(
                rf"$P(\alpha_{{\rm ent}}<0) = {frac_neg:.2f}$  (n={len(v)})",
                xy=(0.03, 0.90 - 0.11 * (1 - correct)),
                xycoords="axes fraction", color=color, fontsize=8)
        ax.axvline(0, color=st.MUTED, lw=0.8, ls=":")
        ax.set_title(titles[ts], pad=4)
        ax.set_xlabel(r"entropy alignment $\alpha_{\rm ent}$")
        ax.set_xlim(-1.05, 1.05)
    axes[0].set_ylabel("density")
    axes[1].annotate(f"mean fitted $T={temp:.2f}$", xy=(0.03, 0.66),
                     xycoords="axes fraction", fontsize=8, color=st.INK2)
    # LEGEND PLACEMENT IS A CORRECTNESS ISSUE HERE.  Inside the axes the
    # legend sat in the same visual band as the alpha_ent = +1 density spike,
    # and `hist`'s own legend handles are filled RECTANGLES that read as extra
    # density bars -- the entries looked like a bar glued to a truncated
    # label.  The legend now lives OUTSIDE the axes, above both panels, with
    # explicit Line2D handles that cannot be mistaken for plotted data.
    handles = [Line2D([], [], color=GROUP_STYLE[c]["color"],
                      ls=GROUP_STYLE[c]["ls"], lw=GROUP_STYLE[c]["lw"])
               for c in (1, 0)]
    labels = [GROUP_STYLE[c]["label"] for c in (1, 0)]
    fig.legend(handles, labels, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, 1.0), handlelength=2.6,
               columnspacing=2.0, handletextpad=0.6, borderaxespad=0.0,
               labelcolor=st.INK2)
    fig.tight_layout(w_pad=1.2)
    st.save(fig, "F6_calib")
    for k in sorted(groups):
        v = np.array(groups[k])
        print(f"temp_scaled={k[0]} correct={k[1]}: n={len(v)}, "
              f"frac alpha_ent<0 = {(v < 0).mean():.3f}, "
              f"median={np.median(v):.3f}")


if __name__ == "__main__":
    main()
