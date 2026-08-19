"""F7: ImageNet-C episodic TTA -- ALTA vs baselines (E3).

Top three panels: accuracy at severity 5 for all 15 corruptions, per
method (Tent / EATA / SAR): frozen (eval-BN), bn0 (t=0 batch-stat BN),
best fixed step (label-selected max over acc_by_step of the fixed run,
an oracle over step counts), and ALTA (label-free).
Bottom panel: the mild-shift story -- defocus_blur and glass_blur at
severity 3, where updating BN statistics already degrades the frozen
model; the frozen accuracy is emphasized as a line over the bars.

Data: experiments/results/e3/<corruption>_<method>_{fixed,alta}_s0.json
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

METHODS = ["tent", "eata", "sar"]
CORRUPTIONS = [
    "gaussian_noise", "shot_noise", "impulse_noise",
    "defocus_blur", "glass_blur", "motion_blur", "zoom_blur",
    "snow", "frost", "fog", "brightness",
    "contrast", "elastic_transform", "pixelate", "jpeg_compression",
]
SHORT = {c: c.replace("_blur", "").replace("_noise", " n.")
             .replace("elastic_transform", "elastic")
             .replace("jpeg_compression", "jpeg") for c in CORRUPTIONS}
BARS = [("bn0", st.AQUA, "$t{=}0$ batch-BN"),
        ("best_fixed", st.BLUE, "best nonzero fixed step"),
        ("alta", st.ORANGE, "ALTA (label-free)")]


def cell(path, sev):
    d = json.loads(path.read_text())
    for c in d["results"]:
        if c["severity"] == sev:
            return c, d
    raise KeyError(f"severity {sev} not in {path}")


def collect(sev):
    out = {}
    stale = []
    for m in METHODS:
        for c in CORRUPTIONS:
            fx, _ = cell(st.RESULTS / "e3" / f"{c}_{m}_fixed_s0.json", sev)
            al, _ = cell(st.RESULTS / "e3" / f"{c}_{m}_alta_s0.json", sev)
            if not al["batches"][0].get("alta_t0_is_frozen", False):
                stale.append((c, m, sev))
            out[(c, m)] = {
                "frozen": fx["frozen_acc"],
                "bn0": fx["bn0_acc"],
                "best_fixed": max(fx["acc_by_step"]),
                "alta": al["adapted_acc"],
            }
    if stale:
        print(f"WARNING stale (pre-safety-fix) alta files: {stale}")
    return out


def main():
    sev5 = collect(5)
    sev3 = collect(3)

    fig = plt.figure(figsize=(st.FULL, 7.0))
    gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1.15], hspace=0.62)

    x = np.arange(len(CORRUPTIONS))
    w = 0.26
    for k, m in enumerate(METHODS):
        ax = fig.add_subplot(gs[k])
        for j, (key, color, label) in enumerate(BARS):
            v = [sev5[(c, m)][key] * 100 for c in CORRUPTIONS]
            ax.bar(x + (j - 1) * w, v, width=w * 0.92, color=color,
                   label=label if k == 0 else None, zorder=3)
        fro = [sev5[(c, m)]["frozen"] * 100 for c in CORRUPTIONS]
        for xi, f in zip(x, fro):
            ax.plot([xi - 1.5 * w, xi + 1.5 * w], [f, f], color=st.INK,
                    lw=1.4, zorder=4,
                    label=("frozen (eval-BN)" if k == 0 and xi == 0
                           else None))
        ax.set_xticks(x)
        ax.set_xticklabels([SHORT[c] for c in CORRUPTIONS], rotation=30,
                           ha="right", fontsize=7.5)
        ax.set_ylabel("top-1 acc. (%)")
        ax.set_xlim(-0.6, len(CORRUPTIONS) - 0.4)
        ax.annotate(f"({'abc'[k]}) {m.upper() if m != 'tent' else 'Tent'}"
                    ", severity 5", xy=(0.005, 1.03),
                    xycoords="axes fraction", fontsize=9, fontweight="bold")
        if k == 0:
            ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.42), ncol=4,
                      columnspacing=1.2, handlelength=1.4)

    # ---------------- mild-shift panel ----------------
    ax = fig.add_subplot(gs[3])
    mild = [("defocus_blur", 3), ("glass_blur", 3)]
    groups = [(c, s, m) for (c, s) in mild for m in METHODS]
    xg = np.arange(len(groups), dtype=float)
    xg[len(METHODS):] += 0.5                       # gap between corruptions
    for j, (key, color, _) in enumerate(BARS):
        v = [sev3[(c, m)][key] * 100 for (c, s, m) in groups]
        ax.bar(xg + (j - 1) * w, v, width=w * 0.92, color=color, zorder=3)
    for xi, (c, s, m) in zip(xg, groups):
        f = sev3[(c, m)]["frozen"] * 100
        ax.plot([xi - 1.7 * w, xi + 1.7 * w], [f, f], color=st.INK, lw=2.2,
                zorder=4)
    ax.annotate("frozen", xy=(xg[0] - 1.6 * w,
                              sev3[("defocus_blur", "tent")]["frozen"] * 100),
                xytext=(-6, -11), textcoords="offset points", fontsize=8,
                color=st.INK, fontweight="bold")
    ax.set_xticks(xg)
    ax.set_xticklabels([m.upper() if m != "tent" else "Tent"
                        for (_, _, m) in groups], fontsize=8)
    y0 = min(sev3[(c, m)][k] for (c, s, m) in groups
             for k in ("frozen", "bn0", "best_fixed", "alta")) * 100
    y1 = max(sev3[(c, m)][k] for (c, s, m) in groups
             for k in ("frozen", "bn0", "best_fixed", "alta")) * 100
    ax.set_ylim(max(0, y0 - 6), y1 + 5)
    for c, xc in [("defocus_blur", xg[:3].mean()),
                  ("glass_blur", xg[3:].mean())]:
        ax.annotate(c.replace("_", " "), xy=(xc, y1 + 3.6),
                    ha="center", fontsize=8.5, color=st.INK2, va="top")
    ax.set_ylabel("top-1 acc. (%)")
    ax.annotate("(d) mild shift, severity 3: BN-statistic updates degrade "
                "the frozen baseline", xy=(0.005, 1.03),
                xycoords="axes fraction", fontsize=9, fontweight="bold")

    st.save(fig, "F7_imagenet")

    gaps = [(sev5[(c, m)]["alta"] - sev5[(c, m)]["best_fixed"]) * 100
            for m in METHODS for c in CORRUPTIONS]
    gaps += [(sev3[(c, m)]["alta"] - sev3[(c, m)]["best_fixed"]) * 100
             for m in METHODS for c in CORRUPTIONS]
    below = [(c, m, s) for s, d in [(5, sev5), (3, sev3)]
             for m in METHODS for c in CORRUPTIONS
             if (d[(c, m)]["alta"] - d[(c, m)]["frozen"]) * 100 < -1.5]
    print(f"mean ALTA - best-fixed gap over {len(gaps)} cells: "
          f"{np.mean(gaps):.2f}pt")
    print(f"cells with ALTA > 1.5pt below frozen: {len(below)}: {below}")


if __name__ == "__main__":
    main()
