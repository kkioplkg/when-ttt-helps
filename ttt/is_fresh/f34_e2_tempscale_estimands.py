"""F34 -- the two estimands of the E2 temperature-scaling loss statement.

WHY THIS SCRIPT EXISTS
----------------------
The manuscript's temperature-scaling sentence says that recalibration "does
not hurt early adapted loss" and quotes a mean change over steps 1-2.  There
are TWO different quantities that sentence can mean, and they differ by more
than a rounding:

  (A) the change in the ABSOLUTE mean adapted loss,
          mean_eps loss_scaled(t) - mean_eps loss_raw(t);
  (B) the change in the EXCESS loss of each arm over ITS OWN frozen
      baseline,
          [mean_eps loss_scaled(t) - mean_eps frozen_scaled]
        - [mean_eps loss_raw(t)    - mean_eps frozen_raw].

They differ because temperature scaling moves the frozen baseline too: the
mean frozen loss itself falls by about 0.191 under scaling, so (A) = (B) +
(that shift).  (B) is what the C4 criterion recorded and what the older
EXPERIMENT_RESULTS.md line reports as "adapted-loss change with temp scaling
(C4 criterion, mean over steps 1-2)"; the label "adapted loss" belongs to
(A).  A reconciliation pass that binds only one printed value cannot see a
correct number carrying the other estimand's name, which is exactly the
defect class this record exists to close: both quantities are computed here,
under their own names, and both are bound in `r9_reconcile.py`.

DATA
  Re-analysis of the ORIGINAL E2 calibration records, unchanged:
      experiments/results/e2/cifar10_tent_calib_s0.json
      experiments/results/e2/cifar100_tent_calib_s0.json
  pooled over the 15 corruptions of each, using BOTH the temp_scaled=False
  and temp_scaled=True cells (the raw/scaled arms are the comparison).  No
  simulation, no random numbers, no seeds: this script draws none.

REPRODUCTION CHECK
  The per-arm mean excess losses must reproduce the four numbers of the
  published adaptation step curve (4.7946 / 6.7819 raw and 4.4095 / 6.3984
  scaled at t = 1, 2) and the mean fitted temperature 1.19; a mismatch exits
  non-zero.
"""
import json
import os

import numpy as np

import common as C

STEPS = ["1", "2", "5", "20"]
EARLY = ["1", "2"]
SRCS = [
    os.path.join(C.RESULTS_DIR, "..", "e2", "cifar10_tent_calib_s0.json"),
    os.path.join(C.RESULTS_DIR, "..", "e2", "cifar100_tent_calib_s0.json"),
]


def load():
    """Pooled per-arm step losses, frozen losses, and fitted temperatures."""
    arms = {False: {"frozen": [], "steps": {s: [] for s in STEPS}},
            True: {"frozen": [], "steps": {s: [] for s in STEPS}}}
    temps = []
    for src in SRCS:
        with open(os.path.abspath(src), encoding="utf-8") as f:
            d = json.load(f)
        temps.append(float(d["results"]["temperature"]))
        for cell in d["results"]["cells"]:
            a = arms[bool(cell["temp_scaled"])]
            for e in cell["episodes"]:
                a["frozen"].append(float(e["frozen_loss"]))
                for s in STEPS:
                    a["steps"][s].append(float(e["steps"][s]["loss"]))
    return arms, temps


def main():
    arms, temps = load()
    n_raw = len(arms[False]["frozen"])
    n_scaled = len(arms[True]["frozen"])

    frozen = {"raw": float(np.mean(arms[False]["frozen"])),
              "scaled": float(np.mean(arms[True]["frozen"]))}
    frozen["change"] = frozen["scaled"] - frozen["raw"]

    absolute, excess = {}, {}
    for s in STEPS:
        raw = float(np.mean(arms[False]["steps"][s]))
        sca = float(np.mean(arms[True]["steps"][s]))
        absolute[s] = {"raw": raw, "scaled": sca, "change": sca - raw}
        excess[s] = {"raw": raw - frozen["raw"],
                     "scaled": sca - frozen["scaled"],
                     "change": (sca - frozen["scaled"])
                               - (raw - frozen["raw"])}

    mean_abs = float(np.mean([absolute[s]["change"] for s in EARLY]))
    mean_exc = float(np.mean([excess[s]["change"] for s in EARLY]))

    out = {
        "what": "the two estimands of the E2 temperature-scaling early-loss "
                "statement, computed from the original calibration records",
        "sources": [C.rel(os.path.abspath(p)) for p in SRCS],
        "n_episodes_per_arm": {"raw": n_raw, "scaled": n_scaled},
        "mean_fitted_temperature": float(np.mean(temps)),
        "frozen_baseline_mean_loss": frozen,
        "per_step": {
            "absolute_adapted_loss": absolute,
            "excess_over_own_frozen_baseline": excess,
        },
        "early_steps": EARLY,
        # (A) -- the change in ABSOLUTE adapted loss
        "mean_change_absolute_adapted_loss_steps_1_2": mean_abs,
        # (B) -- the change in adapted-minus-OWN-frozen excess loss
        "mean_change_excess_over_own_frozen_steps_1_2": mean_exc,
        "identity_check_A_minus_B_equals_frozen_shift":
            mean_abs - mean_exc - frozen["change"],
        "note": "(A) and (B) differ by the shift in the frozen baseline that "
                "temperature scaling itself induces; neither may be printed "
                "under the other's name.",
    }

    # ---- reproduction checks against the published step curve
    for s, raw_pub, sca_pub in [("1", 4.7946, 4.4095), ("2", 6.7819, 6.3984)]:
        assert abs(excess[s]["raw"] - raw_pub) < 5e-4, (s, excess[s]["raw"])
        assert abs(excess[s]["scaled"] - sca_pub) < 5e-4, (s,
                                                           excess[s]["scaled"])
    assert abs(out["mean_fitted_temperature"] - 1.19) < 5e-3, \
        out["mean_fitted_temperature"]
    assert n_raw == n_scaled == 7680, (n_raw, n_scaled)
    assert abs(out["identity_check_A_minus_B_equals_frozen_shift"]) < 1e-9, \
        out["identity_check_A_minus_B_equals_frozen_shift"]
    out["reproduction_check"] = (
        "per-arm excess losses at t = 1, 2 reproduce the published "
        "adaptation step curve (4.7946 / 6.7819 raw, 4.4095 / 6.3984 "
        "scaled), the mean fitted temperature reproduces 1.19, and "
        "(A) - (B) equals the frozen-baseline shift exactly")

    C.save(out, "f34_e2_tempscale_estimands.json")

    print(f"[f34] 1/2 frozen baseline mean loss moves "
          f"{frozen['raw']:.6f} -> {frozen['scaled']:.6f} "
          f"({frozen['change']:+.6f}) under temperature scaling, so the two "
          f"estimands cannot coincide.")
    print(f"[f34] 2/2 mean change over steps 1-2: ABSOLUTE adapted loss "
          f"{mean_abs:+.6f}; EXCESS over own frozen baseline {mean_exc:+.6f}. "
          f"Both are negative; only the second is the C4-criterion number.")
    print("[f34] DONE", flush=True)


if __name__ == "__main__":
    main()
