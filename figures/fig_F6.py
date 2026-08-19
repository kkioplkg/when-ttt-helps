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

SRCS = [st.RESULTS / "e2" / "cifar10_tent_calib_s0.json",
        st.RESULTS / "e2" / "cifar100_tent_calib_s0.json"]
CONF = 0.7


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

    fig, axes = plt.subplots(1, 2, figsize=(st.SINGLE, 2.6), sharey=True,
                             sharex=True)
    bins = np.linspace(-1, 1, 41)
    titles = {False: "(a) raw confidence", True: "(b) temperature-scaled"}
    for ax, ts in zip(axes, [False, True]):
        for correct, color, label in [(1, st.BLUE, "confident \\& right"),
                                      (0, st.RED, "confident \\& wrong")]:
            v = np.array(groups[(ts, correct)])
            ax.hist(v, bins=bins, density=True, histtype="stepfilled",
                    color=color, alpha=0.35, lw=0)
            ax.hist(v, bins=bins, density=True, histtype="step",
                    color=color, lw=1.4,
                    label=label.replace("\\&", "&"))
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
    axes[1].legend(loc="upper left", bbox_to_anchor=(0.02, 0.78),
                   borderaxespad=0)
    axes[1].annotate(f"mean fitted $T={temp:.2f}$", xy=(0.06, 0.47),
                     xycoords="axes fraction", fontsize=8, color=st.INK2)
    fig.tight_layout(w_pad=1.2)
    st.save(fig, "F6_calib")
    for k in sorted(groups):
        v = np.array(groups[k])
        print(f"temp_scaled={k[0]} correct={k[1]}: n={len(v)}, "
              f"frac alpha_ent<0 = {(v < 0).mean():.3f}, "
              f"median={np.median(v):.3f}")


if __name__ == "__main__":
    main()
