"""F5: Tent batch-size mechanics on CIFAR-10-C (severity 5).

(a) mean accuracy gain over frozen vs batch size N at adaptation steps
    1/2/5/10, bn-TRAIN protocol (published Tent protocol), seed 0.
(b) per-batch SSL gradient noise sigma^2_batch_abs = sigma2_batch_rel *
    gnorm_ssl^2 (SCHEMAS.md reconstruction) vs N on log-log axes with a
    1/N reference, bn-EVAL protocol (independent per-sample gradients),
    medians over batches x 15 corruptions, seeds 0/1/2. N=1 is excluded:
    Tent's objective is deterministic there (sigma^2 == 0 exactly).

Data: experiments/results/e2/cifar10_tent_batch_sweep_s0_bntrain.json
      experiments/results/e2/cifar10_tent_batch_sweep_s{0,1,2}.json
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

BNTRAIN = st.RESULTS / "e2" / "cifar10_tent_batch_sweep_s0_bntrain.json"
BNEVAL = [st.RESULTS / "e2" / f"cifar10_tent_batch_sweep_s{s}.json"
          for s in (0, 1, 2)]
STEPS = ["1", "2", "5", "10"]
# TWO-CHANNEL SERIES DISCRIMINATION.  Colour alone does not survive a
# grayscale print: AQUA (#1baf7a) and ORANGE (#eb6834) sit within 0.02 of each
# other in relative luminance, so a reader with a monochrome copy -- or with a
# red-green deficiency -- cannot tell t=2 from t=10.  Each step count therefore
# carries its own dash pattern AND its own marker in addition to its colour.
STEP_STYLE = {
    "1": {"color": st.BLUE, "ls": "-", "marker": "o", "ms": 3.8, "lw": 1.7},
    "2": {"color": st.AQUA, "ls": (0, (4.2, 1.6)), "marker": "s", "ms": 3.3,
          "lw": 1.5},
    "5": {"color": st.VIOLET, "ls": (0, (1.2, 1.4)), "marker": "^", "ms": 4.2,
          "lw": 1.5},
    "10": {"color": st.ORANGE, "ls": (0, (5.5, 1.6, 1.2, 1.6)), "marker": "D",
           "ms": 3.0, "lw": 1.5},
}


def main():
    # ---------------- (a) gain vs N by step count, bn-train ----------------
    tr = json.loads(BNTRAIN.read_text())
    Ns = sorted({r["N"] for r in tr["results"]})
    gain = {t: [] for t in STEPS}
    for N in Ns:
        accs = {t: [] for t in STEPS}
        frozen = []
        for r in tr["results"]:
            if r["N"] != N:
                continue
            for b in r["batches"]:
                assert "steps" in b, "v2 per-step schema expected"
                frozen.append(b["frozen_acc"])
                for t in STEPS:
                    accs[t].append(b["steps"][t]["acc"])
        f = np.mean(frozen)
        for t in STEPS:
            gain[t].append((np.mean(accs[t]) - f) * 100)

    # ---------------- (b) sigma^2_batch_abs vs N, bn-eval ----------------
    med_by_seed = {}
    pooled = {}
    for path in BNEVAL:
        ev = json.loads(path.read_text())
        seed = ev["meta"]["argv"]["seed"]
        for r in ev["results"]:
            N = r["N"]
            if N == 1:
                continue                      # deterministic: sigma^2 == 0
            vals = [b["sigma2_batch_rel"] * b["gnorm_ssl"] ** 2
                    for b in r["batches"]]
            med_by_seed.setdefault(seed, {}).setdefault(N, []).extend(vals)
            pooled.setdefault(N, []).extend(vals)
    Nb = sorted(pooled)
    med = [float(np.median(pooled[N])) for N in Nb]
    rho = st.spearman(Nb, med)

    # AUTHORED AT PRINT SIZE, NOT AT st.SINGLE.  This float is included in the
    # supplement at width=0.92\textwidth = 5.98 in (cas-sc, \textwidth =
    # 469.755 pt = 6.50 in).  Saved from st.SINGLE the bbox was 5.32 in, so
    # LaTeX ENLARGED it by 1.13 and _style's 9/8 pt type landed on the page at
    # 10.1/9.0 pt -- legible, but visibly heavier than the body face and than
    # every other figure in the document.  6.17 in of canvas saves a ~5.98 in
    # bbox, so the reduction is ~1.0 and the figure carries the same 9/8 pt as
    # its neighbours.  st.SINGLE itself must not be touched: F3 and F7 share it
    # and are included at different widths again.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.17, 3.02))

    for t in STEPS:
        s = STEP_STYLE[t]
        ax1.plot(Ns, gain[t], color=s["color"], ls=s["ls"], marker=s["marker"],
                 markersize=s["ms"], lw=s["lw"], label=f"$t={t}$")
    ax1.set_xscale("log", base=2)
    # handlelength has to be long enough to show a full dash period, otherwise
    # the legend key cannot distinguish the four line styles it is there to key
    ax1.legend(loc="lower right", handlelength=2.8, labelspacing=0.35,
               borderaxespad=0.3, handletextpad=0.6)
    ax1.axhline(0, color=st.MUTED, lw=0.8, ls=":")
    ax1.set_xlabel("batch size $N$")
    ax1.set_ylabel("accuracy gain over frozen (pp)")
    ax1.set_title("(a) Tent gain vs $N$ (bn-train)", pad=4)

    for seed, d in sorted(med_by_seed.items()):
        ax2.plot(sorted(d), [np.median(d[N]) for N in sorted(d)],
                 marker="o", markersize=3, lw=0.9, alpha=0.45,
                 color=st.BLUE)
    anchor = Nb.index(8)                          # match the tail regime
    ref = med[anchor] * (Nb[anchor] / np.array(Nb, float))
    ax2.plot(Nb, ref, ls="--", color=st.INK, lw=1.1)
    ax2.annotate(r"$\propto 1/N$", xy=(4.4, ref[list(Nb).index(4)] * 1.45),
                 fontsize=8.5, color=st.INK)
    ax2.set_xscale("log", base=2)
    ax2.set_yscale("log")
    from matplotlib.ticker import NullFormatter
    ax2.yaxis.set_minor_formatter(NullFormatter())
    ax2.set_xlabel("batch size $N$")
    ax2.set_ylabel(r"median $\hat\sigma^2_{\rm batch}$")
    ax2.set_title("(b) SSL gradient noise (bn-eval)", pad=4)
    ax2.annotate(rf"$\rho_s(N,\mathrm{{median}}) = {rho:.3f}$" + "\nseeds 0/1/2",
                 xy=(0.04, 0.07), xycoords="axes fraction", fontsize=8,
                 color=st.INK2)

    fig.tight_layout(w_pad=1.8)
    st.save(fig, "F5_batch")
    print(f"pooled medians: {dict(zip(Nb, np.round(med, 1)))}, rho={rho:.3f}")
    print(f"gain@N=1: " + ", ".join(f"t={t}: {gain[t][0]:.2f}pp"
                                    for t in STEPS))


if __name__ == "__main__":
    main()
