"""F8b -- the same commissioning/evaluation cross-fit as f8, applied to the
DETERMINISTIC E2 objectives (tent, pseudo-label).

WHY THIS SCRIPT EXISTS
----------------------
f8_e2_crossfit.py cross-fits only the two stochastic SSL methods, because
those are the ones the C2 gate is about.  Figure 4's third panel, however,
annotates the deterministic objectives with FULL-SAMPLE Spearman values
(-0.69 to -0.96), which mixes two protocols in one figure: it
foregrounds same-sample estimates while the text designates cross-fitted
values as the paper's evidence.  This script produces the cross-fitted
counterparts so every number on the regenerated Figure 4 comes from the same
protocol.

It adds no new machinery: it imports f8_e2_crossfit and calls its `analyse`
on `tent` and `pl` with the loss-proxy statistic (`phase_loss`), which is the
statistic Figure 4(c) plots.  Nothing is re-run on a GPU; the input is the
ORIGINAL results/e2/*_main_*.json episode records.

PROTOCOL (inherited from f8, unchanged)
  * within each (dataset, method, corruption, severity) cell a fresh-seed
    permutation splits the episodes 50/50 into a COMMISSIONING share (which
    defines the phase statistic) and a disjoint EVALUATION share (which
    defines the realized gain);
  * seeds 20260801..20260805, mean and range reported;
  * corruption-clustered bootstrap, 1000 resamples of the 15 corruptions.

OUTPUT
  f8b_e2_crossfit_det_{method}_seed{seed}.json   per-seed rows
  f8b_e2_crossfit_det_summary.json               aggregate

The f8 output files are NOT touched: this script writes under its own prefix
so the existing artefacts the manuscript already cites stay bit-identical.

STATISTIC (corrected)
The deterministic arms carry sigma^2_rel == 0 in every episode record, so the
statistic used here is the DECLARED zero-noise limit of the manuscript's
definition,

    Phi_0 = alpha_sgn |alpha_sgn| delta_proxy,

documented at length in f8_e2_crossfit.py.  The pre-correction implementation
wrote `alpha**2` where the manuscript has `alpha*|alpha|`, discarding the sign
of the alignment factor; the values that dropped out of it (-0.69 .. -0.96)
are not estimates of the manuscript's statistic.  `--statistic
phase_loss_unsigned` recomputes them for the audit trail.

REPRODUCTION CHECKS (asserted)
1. AUDIT: with the unsigned numerator alpha^2 delta_proxy and no split, the
   same-sample correlations must still be <= -0.5, reproducing the archived
   pre-correction regime.
2. The corrected signed statistic is then reported with NO assertion on its
   sign -- nothing about the answer is presupposed.
"""
import argparse

import numpy as np

import common as C
import f8_e2_crossfit as F8

DETERMINISTIC = ("tent", "pl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commission", type=float, default=0.5)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--statistic", default="phase_loss",
                    choices=["phase_feat", "phase_loss", "phase_align",
                             "phase_loss_unsigned"])
    ap.add_argument("--out-prefix", default="f8b_e2_crossfit_det")
    args = ap.parse_args()

    cells = F8.load_cells()
    print(f"[f8b] loaded {len(cells)} cells", flush=True)
    print(f"[f8b] noise regime per arm: {F8.assert_noise_homogeneous(cells)}",
          flush=True)

    # ---- audit check: the pre-correction UNSIGNED numerator must still
    #      reproduce the archived strongly-negative regime
    audit = {}
    for meth in DETERMINISTIC:
        r = F8.analyse(cells, meth, 20260801, 1.0, "phase_loss_unsigned", 0)
        audit[meth] = {k: v for k, v in r.items() if k.startswith("rho_")}
        got = r["rho_mean_final"]
        assert got is not None and got <= -0.5, (
            f"{meth}: unsigned same-sample rho_mean_final = {got}, which does "
            f"not reproduce the archived pre-correction regime (-0.69..-0.96)")
    print("[f8b] audit: the unsigned numerator reproduces the archived "
          "negative regime: OK", flush=True)

    # ---- same-sample reference for the statistic actually reported
    repro = {}
    for meth in DETERMINISTIC:
        r = F8.analyse(cells, meth, 20260801, 1.0, args.statistic, 0)
        repro[meth] = {k: v for k, v in r.items()
                       if k.startswith("rho_") or k.startswith("n_cells")}

    per_method = {}
    for meth in DETERMINISTIC:
        runs = [F8.analyse(cells, meth, s, args.commission, args.statistic,
                           args.n_boot) for s in args.seeds]
        for r, s in zip(runs, args.seeds):
            C.save(r, f"{args.out_prefix}_{meth}_seed{s}.json")
        out = {"method": meth, "seeds": args.seeds,
               "commission_share": args.commission,
               "statistic": args.statistic,
               "n_cells": runs[0]["n_cells_mean"],
               "same_sample_reference": repro[meth],
               "audit_unsigned_same_sample": audit[meth]}
        for how in ("mean", "median"):
            for tag in ("final", "best_crossfit", "best_in_sample"):
                k = f"rho_{how}_{tag}"
                out[k] = C.mean_range([r[k] for r in runs])
                cis = [r.get(f"ci_{how}_{tag}") for r in runs]
                cis = [c for c in cis if c]
                if cis:
                    out[f"ci_{how}_{tag}_clustered"] = {
                        "lo_mean": float(np.mean([c["lo"] for c in cis])),
                        "hi_mean": float(np.mean([c["hi"] for c in cis])),
                        "lo_min": float(np.min([c["lo"] for c in cis])),
                        "hi_max": float(np.max([c["hi"] for c in cis])),
                        "n_clusters": cis[0]["n_clusters"],
                        "n_boot": cis[0]["n_boot"]}
        per_method[meth] = out
        print(f"[f8b] {meth}: same-sample {repro[meth]['rho_mean_final']:+.3f} "
              f"-> cross-fit {out['rho_mean_final']['mean']:+.3f} "
              f"(range {out['rho_mean_final']['min']:+.3f}.."
              f"{out['rho_mean_final']['max']:+.3f})", flush=True)

    C.save({"script": "f8b_e2_crossfit_det.py",
            "replaces": ("full-sample Spearman annotations on Figure 4's "
                         "deterministic panel"),
            "protocol": ("identical to f8_e2_crossfit.py, applied to tent and "
                         "pl with the loss-proxy statistic"),
            "commission_share": args.commission, "seeds": args.seeds,
            "statistic": args.statistic,
            "per_method": per_method}, f"{args.out_prefix}_summary.json")
    print("[f8b] DONE", flush=True)


if __name__ == "__main__":
    main()
