"""F25 -- E2 learning-rate ablation, recomputed with the manuscript's SIGNED
phase statistic.

WHY THIS SCRIPT EXISTS
----------------------
The manuscript's learning-rate ablation (Section 5.5, "Learning rate") quoted
cell-level Spearman correlations of 0.60 / 0.57 / 0.59 at lr = 3e-4 / 1e-3 /
3e-3 and called them "rank-stable across rates".  Those three numbers were
produced by the same implementation defect identified elsewhere in E2: the
loss-proxy phase statistic was computed with
an UNSIGNED alignment factor `alpha**2` where the manuscript defines the
SIGNED factor `alpha_sgn|alpha_sgn|`.  Recomputed under the manuscript's own
definition the three values are no longer close to one another, so the
"rank-stable" description does not survive and the ablation has to be
restated.

There was no script for this ablation in `is_fresh/`; it was an ad-hoc
computation recorded only in a source comment.  This file supplies one.

INPUTS (stored per-episode records only; nothing is re-run on a GPU)
    lr = 3e-4   results/e5/cifar10_ttt_rot_main_s0_lr0.0003.json
    lr = 1e-3   results/e2/cifar10_ttt_rot_main_s0.json   (the default rate;
                restricted to the four corruptions the other two rates cover)
    lr = 3e-3   results/e5/cifar10_ttt_rot_main_s0_lr0.003.json
All three are source-model seed 0, ttt_rot, bn-eval, 64 episodes per cell,
20 CIFAR-10 cells per rate (4 corruptions x 5 severities).

STATISTIC
`f8_e2_crossfit.phase_value`, i.e. the manuscript's

    Phi = alpha_sgn |alpha_sgn| delta_proxy / sigma^2_rel .

Every ttt_rot episode has sigma^2_rel > 0, so the ratio form applies
throughout and the declared zero-noise limit is never invoked here.

WHAT IS REPORTED, per rate
  * mean over cells of the best-step gain (loss units) -- unchanged by the
    correction, since gains do not involve the statistic;
  * rho_in_sample_best : Spearman(cell-mean phase, in-sample best-step gain),
    the manuscript's original convention, recomputed with the signed
    statistic;
  * rho_final          : Spearman(cell-mean phase, final-step gain);
  * rho_crossfit_best / rho_crossfit_final : the same quantities under the
    50/50 commissioning-to-evaluation cross-fit at split seeds
    20260801--20260805 that every other E2 number in the paper uses, reported
    as mean and range;
  * rho_align_*        : the alignment-only statistic alpha_sgn|alpha_sgn|,
    carried as the robustness statistic throughout the revised E2.

AUDIT CHECK (asserted)
With the unsigned numerator the in-sample values must reproduce the archived
0.603 / 0.573 / 0.588 to within 0.01, and the mean best-step gains must
reproduce 0.1931 / 0.0883 / 0.2166 to within 0.001.  This is what pins the
recomputation to the published one and localises the change to the sign.

OUTPUT
  f25_e2_lr_ablation.json
"""
import argparse
import json
import os

import numpy as np

import common as C
import f8_e2_crossfit as F8

E2_DIR = F8.E2_DIR
E5_DIR = F8.E5_DIR
CORRUPTIONS = ("gaussian_noise", "fog", "contrast", "motion_blur")
SOURCE_SEED = 0

RATES = (
    (3e-4, os.path.join(E5_DIR, "cifar10_ttt_rot_main_s0_lr0.0003.json")),
    (1e-3, os.path.join(E2_DIR, "cifar10_ttt_rot_main_s0.json")),
    (3e-3, os.path.join(E5_DIR, "cifar10_ttt_rot_main_s0_lr0.003.json")),
)
# archived values the correction must reproduce with the unsigned numerator
ARCHIVED_RHO = (0.603, 0.573, 0.588)
ARCHIVED_GAIN = (0.1931, 0.0883, 0.2166)


def load_rate(path):
    """{(dataset, method, corruption, severity): [episode, ...]} for one rate."""
    dfeat = F8.load_delta_feat().get(("cifar10", "resnet26ttt"), {})
    with open(path, encoding="utf-8") as f:
        o = json.load(f)
    argv = o.get("meta", {}).get("argv", {})
    assert argv.get("method") == "ttt_rot" and argv.get("mode", "main") == "main"
    assert int(argv.get("seed", SOURCE_SEED)) == SOURCE_SEED
    cells = {}
    for cell in o.get("results", []):
        corr, sev = cell["corruption"], int(cell["severity"])
        if corr not in CORRUPTIONS:
            continue
        key = ("cifar10", "ttt_rot", corr, sev)
        for e in cell.get("episodes", []):
            df = (dfeat.get((corr, sev, int(e["idx"])))
                  if e.get("idx") is not None else None)
            rec = F8._episode_stats(e.get("alpha"), e.get("sigma2_rel"),
                                    df, e.get("delta_proxy"))
            rec["frozen_loss"] = e["frozen_loss"]
            rec["steps"] = {int(t): v["loss"]
                            for t, v in e.get("steps", {}).items()}
            cells.setdefault(key, []).append(rec)
    F8.assert_noise_homogeneous(cells)
    return cells


def rho_no_split(cells, stat_key, ykey):
    rows = F8.build_rows(cells, "ttt_rot", np.random.default_rng(0), 1.0,
                         stat_key, "mean")
    return F8.spearman([r["phase"] for r in rows], [r[ykey] for r in rows])


def rho_crossfit(cells, stat_key, ykey, seeds, commission):
    vals = []
    for s in seeds:
        rows = F8.build_rows(cells, "ttt_rot", np.random.default_rng(s + 1),
                             commission, stat_key, "mean")
        vals.append(F8.spearman([r["phase"] for r in rows],
                                [r[ykey] for r in rows]))
    return C.mean_range(vals)


def mean_best_gain(cells):
    """Mean over cells of max_t mean_episodes(frozen_loss - loss_t)."""
    rows = F8.build_rows(cells, "ttt_rot", np.random.default_rng(0), 1.0,
                         "phase_loss", "mean")
    v = [r["gain_best_in_sample"] for r in rows
         if r["gain_best_in_sample"] is not None]
    return float(np.mean(v)), len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commission", type=float, default=0.5)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--out-name", default="f25_e2_lr_ablation.json")
    args = ap.parse_args()

    per_rate, audit_rho, audit_gain = [], [], []
    for lr, path in RATES:
        cells = load_rate(path)
        gain, n_cells = mean_best_gain(cells)
        rec = {
            "lr": lr,
            # POSIX separators, always.  os.path.relpath returns the HOST
            # separator, so the same script emits `e5/x.json` on Linux and
            # `e5\x.json` on Windows: a record that is numerically identical
            # but not byte-identical across operating systems, for a field
            # that names a repository-relative path rather than a filesystem
            # location.
            "source": os.path.relpath(
                path, os.path.dirname(E2_DIR)).replace(os.sep, "/"),
            "n_cells": n_cells,
            "n_episodes": sum(len(v) for v in cells.values()),
            "mean_best_step_gain": gain,
            "rho_in_sample_best": rho_no_split(cells, "phase_loss",
                                               "gain_best_in_sample"),
            "rho_final": rho_no_split(cells, "phase_loss", "gain_final"),
            "rho_crossfit_best": rho_crossfit(cells, "phase_loss",
                                              "gain_best_crossfit",
                                              args.seeds, args.commission),
            "rho_crossfit_final": rho_crossfit(cells, "phase_loss",
                                               "gain_final",
                                               args.seeds, args.commission),
            "rho_align_in_sample_best": rho_no_split(cells, "phase_align",
                                                     "gain_best_in_sample"),
            "rho_align_crossfit_final": rho_crossfit(cells, "phase_align",
                                                     "gain_final",
                                                     args.seeds,
                                                     args.commission),
            "audit_unsigned_rho_in_sample_best": rho_no_split(
                cells, "phase_loss_unsigned", "gain_best_in_sample"),
        }
        per_rate.append(rec)
        audit_rho.append(rec["audit_unsigned_rho_in_sample_best"])
        audit_gain.append(gain)
        print(f"[f25] lr={lr:<8g} n_cells={n_cells} "
              f"gain={gain:.4f}  archived(unsigned) "
              f"{rec['audit_unsigned_rho_in_sample_best']:+.3f}  "
              f"SIGNED in-sample {rec['rho_in_sample_best']:+.3f}  "
              f"final {rec['rho_final']:+.3f}  "
              f"cross-fit final {rec['rho_crossfit_final']['mean']:+.3f} "
              f"[{rec['rho_crossfit_final']['min']:+.3f}, "
              f"{rec['rho_crossfit_final']['max']:+.3f}]  "
              f"align in-sample {rec['rho_align_in_sample_best']:+.3f}",
              flush=True)

    bad = [(lr, w, g) for (lr, _), w, g in zip(RATES, ARCHIVED_RHO, audit_rho)
           if g is None or abs(g - w) > 0.01]
    assert not bad, f"unsigned audit failed to reproduce archived rho: {bad}"
    bad = [(lr, w, g) for (lr, _), w, g in zip(RATES, ARCHIVED_GAIN, audit_gain)
           if abs(g - w) > 1e-3]
    assert not bad, f"audit failed to reproduce archived mean gains: {bad}"
    print("[f25] audit: archived unsigned rho and mean gains reproduced: OK",
          flush=True)

    signed = [r["rho_in_sample_best"] for r in per_rate]
    cf = [r["rho_crossfit_final"]["mean"] for r in per_rate]
    verdict = {
        "archived_claim": ("rank-stable across rates: rho_s = 0.60, 0.57, 0.59"),
        "archived_values_reproduced_with_unsigned_numerator": audit_rho,
        "signed_in_sample_best": signed,
        "signed_in_sample_best_spread": float(max(signed) - min(signed)),
        "signed_crossfit_final": cf,
        "signed_crossfit_final_spread": float(max(cf) - min(cf)),
        "all_three_rates_positive_in_sample": bool(all(v > 0 for v in signed)),
        "all_three_rates_positive_crossfit": bool(all(v > 0 for v in cf)),
        "rank_stable_claim_survives": bool(max(signed) - min(signed) <= 0.10),
        "what_actually_holds": (
            "the sign of the correlation is positive at all three learning "
            "rates; its magnitude is not stable across them, so the ablation "
            "supports sign stability and not rank stability"),
    }
    C.save({"script": "f25_e2_lr_ablation.py",
            "replaces": ("the ad-hoc learning-rate ablation numbers quoted in "
                         "Section 5.5, computed with an unsigned alignment "
                         "factor"),
            "statistic": ("alpha_sgn|alpha_sgn| delta_proxy / sigma^2_rel "
                          "(f8_e2_crossfit.phase_value); ratio form throughout "
                          "-- every ttt_rot episode has sigma^2_rel > 0"),
            "protocol": ("20 CIFAR-10 cells per rate (gaussian_noise, fog, "
                         "contrast, motion_blur x severities 1-5), source seed "
                         "0, 64 episodes per cell; cross-fit at split seeds "
                         f"{args.seeds}"),
            "per_rate": per_rate, "verdict": verdict}, args.out_name)
    print(f"[f25] verdict: {json.dumps(verdict, indent=1)}", flush=True)
    print("[f25] DONE", flush=True)


if __name__ == "__main__":
    main()
