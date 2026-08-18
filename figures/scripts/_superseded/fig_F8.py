"""F8: GPT-2 language-shift experiment (E4) -- within-domain phase
statistic vs realized gain, one panel per domain.

x = alpha * |alpha| * delta_v2 / sigma^2 (PRIMARY statistic: delta_v2 is
    the doc's hidden-state cosine distance to the wikitext reference at
    theta0, from E5; joined to e4 records by doc id), symlog scale.
y = per-doc continuation-CE gain at the ALTA stop
    (frozen_cont_ce - alta.cont_ce), pooled over 3 seeds.
Spearman rho annotated per domain, computed from the plotted points and
cross-checked against summary_final.json (milestones.e4.within_domain).

Data: experiments/results/e4/<domain>_ln_s{0,1,2}.json
      experiments/results/e5/delta_v2_<domain>.json
"""
import json

import numpy as np

import _style as st
import matplotlib.pyplot as plt

DOMAINS = ["wikitext", "pubmed", "legal", "code"]
COLORS = {"wikitext": st.BLUE, "pubmed": st.AQUA,
          "legal": st.VIOLET, "code": st.ORANGE}
SEEDS = [0, 1, 2]


def main():
    s = json.loads((st.RESULTS / "summary_final.json").read_text())
    ref = {d["domain"]: d["rho_gain_alta_delta_v2"]
           for d in s["milestones"]["e4"]["within_domain"][0]["per_domain"]}

    fig, axes = plt.subplots(2, 2, figsize=(st.SINGLE, 4.4))
    for ax, dom in zip(axes.ravel(), DOMAINS):
        dv = json.loads(
            (st.RESULTS / "e5" / f"delta_v2_{dom}.json").read_text())
        d2 = {r["doc"]: r["delta_v2"] for r in dv["records"]}
        xs, ys = [], []
        for seed in SEEDS:
            e4 = json.loads(
                (st.RESULTS / "e4" / f"{dom}_ln_s{seed}.json").read_text())
            for r in e4["records"]:
                if r["alta"] is None or r["doc"] not in d2:
                    continue
                if r["sigma2_rel"] <= 0:
                    continue
                xs.append(r["alpha"] * abs(r["alpha"]) * d2[r["doc"]]
                          / r["sigma2_rel"])
                ys.append(r["frozen_cont_ce"] - r["alta"]["cont_ce"])
        xs, ys = np.array(xs), np.array(ys)
        rho = st.spearman(xs, ys)
        assert abs(rho - ref[dom]) < 5e-3, (dom, rho, ref[dom])
        ax.scatter(xs, ys, s=5, color=COLORS[dom], alpha=0.35, linewidths=0,
                   rasterized=True)
        ax.set_xscale("symlog", linthresh=1e-3)
        if dom in ("pubmed", "code"):             # heavy-tailed gains
            ax.set_yscale("symlog", linthresh=0.02)
            ax.set_yticks([-0.01, 0, 0.01, 0.1, 1])
        ax.axhline(0, color=st.MUTED, lw=0.7, ls=":")
        ax.set_title(dom, pad=3)
        ax.annotate(rf"$\rho_s = {rho:.2f}$" + f"\n(n={len(xs)})",
                    xy=(0.04, 0.95), xycoords="axes fraction", va="top",
                    fontsize=8.5)
        print(f"{dom}: rho={rho:.3f} (summary {ref[dom]:.3f}), n={len(xs)}")
    for ax in axes[1]:
        ax.set_xlabel(r"phase stat. $\alpha|\alpha|\,\delta_{v2}/\sigma^2$")
    for ax in axes[:, 0]:
        ax.set_ylabel("CE gain at ALTA stop")
    fig.tight_layout(h_pad=1.1, w_pad=1.0)
    st.save(fig, "F8_domains")


if __name__ == "__main__":
    main()
