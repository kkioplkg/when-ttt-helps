#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Emit the job lanes for the seed-matched delta_feat experiment.

Nothing about the experiment is decided here: the grid this reproduces is READ
from the published records' own metadata (`experiments/results/e2/*_main_*.json`)
when `--from-records` is given, so the job list cannot drift from the grid it
claims to reproduce.  With no records present (i.e. on the compute host) it
falls back to the frozen transcription below, which `--from-records` is used to
verify against the records on the machine that has them.

Lanes
  train   6 source trainings + 6 recon heads      (Stage A)
  grid    the 10 published stochastic adaptation runs (Stage B)
  dfeat   6 seed-resolved delta_feat measurements  (Stage C)
"""
import argparse
import glob
import json
import os
import sys

# ---- frozen transcription of the published stochastic grid --------------
# (dataset, method, seed, severities, alta).  Verified against the record
# metadata by --from-records; the two must agree or this exits non-zero.
#
# ALTA IS PART OF THE TRANSCRIPTION, NOT A CHOICE.  Design v1 proposed running
# the whole grid with --alta off on the argument that ALTA's output feeds no
# delta_feat analysis.  The design review rejected that: "not consumed by the
# analysis" is not sufficient, because a code path can consume RNG or alter
# state, and there is no benefit to manufacturing the argument.  Each run
# therefore carries the flag its published counterpart carried.
#
# It costs nothing here.  Only the three seed-0 runs had ALTA on, and the
# approved Stage B is EXPOSED-ONLY -- seeds 1 and 2 -- every one of which had
# ALTA off.  So the exposed lane reproduces the published settings exactly,
# with zero deviation, rather than merely defensibly.
GRID = [
    ("cifar10", "ttt_rot", 0, "1,2,3,4,5", True),
    ("cifar10", "ttt_rot", 1, "1,2,3,4,5", False),
    ("cifar10", "ttt_rot", 2, "1,2,3,4,5", False),
    ("cifar100", "ttt_rot", 0, "3,5", True),
    ("cifar100", "ttt_rot", 1, "3,5", False),
    ("cifar100", "ttt_rot", 2, "3,5", False),
    ("cifar10", "ttt_mask", 0, "1,2,3,4,5", True),
    ("cifar10", "ttt_mask", 1, "1,2,3,4,5", False),
    ("cifar10", "ttt_mask", 2, "1,2,3,4,5", False),
    ("cifar100", "ttt_mask", 0, "3,5", False),
]

# The APPROVED Stage B: the episodes that were actually mismeasured, i.e. every
# run whose source seed is not 0.  Seed-0 episodes were never cross-measured,
# so re-running them buys no mechanism information -- they only contribute the
# structural point mass at zero that dilutes the full-grid protocol effect.
# `ttt_mask` has no CIFAR-100 seed 1/2 run to expose, so its exposed analysis is
# CIFAR-10 only (75 cells) while `ttt_rot`'s spans all 105.  That asymmetry is
# a property of the published grid, not of this experiment, and is stated in
# the results rather than papered over.
EXPOSED_SEEDS = (1, 2)
EPISODES = 128
STEPS = 20
LR = 1e-3
ARCH = "resnet26ttt"
SOURCE_SEEDS = [0, 1, 2]
DATASETS = ["cifar10", "cifar100"]


def read_grid_from_records(e2_dir):
    got = []
    for p in sorted(glob.glob(os.path.join(e2_dir, "*_main_*.json"))):
        base = os.path.basename(p)
        if "_lr" in base or "bntrain" in base:
            continue
        with open(p, encoding="utf-8") as f:
            argv = json.load(f)["meta"]["argv"]
        if argv["method"] not in ("ttt_rot", "ttt_mask"):
            continue
        if argv.get("bn_mode", "eval") != "eval":
            continue
        got.append((argv["dataset"], argv["method"], int(argv["seed"]),
                    argv["severities"], bool(argv.get("alta", False))))
        assert argv["episodes"] == EPISODES, (base, argv["episodes"])
        assert argv["steps"] == STEPS, (base, argv["steps"])
        assert abs(argv["lr"] - LR) < 1e-12, (base, argv["lr"])
    return sorted(got)


def main():
    ap = argparse.ArgumentParser()
    # No default: the run that produced the shipped records passed the
    # compute host's own checkout, and a published script must not carry
    # a path that resolves nowhere for its reader.
    ap.add_argument("--ttt-root", required=True,
                    help="repository root (in the release, the root of "
                         "the extracted archive)")
    ap.add_argument("--out-dir", required=True, help="where the jobfiles go")
    ap.add_argument("--from-records", default=None,
                    help="path to experiments/results/e2; verifies GRID")
    ap.add_argument("--python", default=None)
    args = ap.parse_args()

    if args.from_records:
        got = read_grid_from_records(args.from_records)
        want = sorted(GRID)
        if got != want:
            print("FATAL: the frozen GRID does not match the published records.")
            print("  records:", got)
            print("  frozen :", want)
            sys.exit(1)
        print("OK: frozen GRID matches the published record metadata "
              "(%d runs, episodes=%d steps=%d lr=%g)"
              % (len(got), EPISODES, STEPS, LR))

    R = args.ttt_root
    PY = args.python or f"{R}/miniconda3/bin/python"
    CODE = f"{R}/experiments/ttt"
    DATA = f"{R}/experiments/data"
    CKPT = f"{R}/experiments/ckpt/seedmatch"
    STAGE = f"{R}/experiments/results/is_fresh_incoming_gpu3"
    os.makedirs(args.out_dir, exist_ok=True)

    def w(name, lines):
        p = os.path.join(args.out_dir, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(lines))
        print("wrote %s (%d jobs)" % (p, len(lines)))

    # ---- Stage A: source trainings, then recon heads --------------------
    train = []
    for ds in DATASETS:
        for s in SOURCE_SEEDS:
            jid = f"train_{ds}_s{s}"
            train.append(
                f"{jid}\tcd {CODE} && {PY} -m e2_cifar.train_source "
                f"--dataset {ds} --arch {ARCH} --seed {s} "
                f"--data-root {DATA} --ckpt-dir {CKPT} "
                f"--out-dir {STAGE}/m0\n")
    w("jobs_train.txt", train)
    w("jobs_train_c10.txt", [l for l in train if "cifar10_" in l])
    w("jobs_train_c100.txt", [l for l in train if "cifar100_" in l])

    # ---- Stage B, as approved: EXPOSED-ONLY ------------------------------
    exposed = [g for g in GRID if g[2] in EXPOSED_SEEDS]

    def grid_line(ds, meth, s, sev, alta):
        jid = f"grid_{ds}_{meth}_s{s}"
        return (f"{jid}\tcd {CODE} && {PY} -m e2_cifar.adapt_cifar "
                f"--dataset {ds} --method {meth} --seed {s} --mode main "
                f"--episodes {EPISODES} --steps {STEPS} --lr {LR:g} "
                f"--severities {sev} --bn-mode eval "
                + ("--alta " if alta else "")
                + f"--data-root {DATA} --ckpt-dir {CKPT} "
                  f"--out-dir {STAGE}/e2\n")

    w("jobs_grid_exposed.txt", [grid_line(*g) for g in exposed])
    w("jobs_grid_full.txt", [grid_line(*g) for g in GRID])

    # ---- recon heads: ONLY for networks that actually run ttt_mask -------
    # The design review's point: six source encoders do not imply six recon
    # heads.  Under exposed-only Stage B the only ttt_mask runs are CIFAR-10
    # seeds 1 and 2, so exactly two heads are built.
    need_recon = sorted({(ds, s) for ds, meth, s, _sev, _a in exposed
                         if meth == "ttt_mask"})
    w("jobs_recon.txt", [
        f"recon_{ds}_s{s}\tcd {CODE} && {PY} -m e2_cifar.train_recon_head "
        f"--ckpt {CKPT}/{ds}_{ARCH}_s{s}.pt --dataset {ds} "
        f"--data-root {DATA}\n"
        for ds, s in need_recon])

    # every exposed run must have the checkpoint (and head) it needs
    for ds, meth, s, _sev, _a in exposed:
        assert s in SOURCE_SEEDS and ds in DATASETS, (ds, meth, s)
        if meth == "ttt_mask":
            assert (ds, s) in need_recon, f"missing recon head for {ds} s{s}"
    print("exposed Stage B: %d runs (%s); recon heads: %s"
          % (len(exposed),
             ", ".join(f"{d}/{m}/s{s}" for d, m, s, _v, _a in exposed),
             ", ".join(f"{d}_s{s}" for d, s in need_recon) or "none"))
    assert all(not a for *_x, a in exposed), (
        "an exposed run carries ALTA=True; the approved lane is supposed to "
        "reproduce the published settings exactly")

    # ---- Stage C' is deliberately NOT emitted as a lane ------------------
    # The crossed measurement matrix is driven by chain.sh, which calls
    # seedmatch/sm_crossed.py for every (dataset, measurement network) pair
    # over the frozen episode manifest.  The earlier per-seed `dfeat` lane
    # measured only the DIAGONAL -- episode of seed s through net s -- and was
    # removed together with sm_delta_feat.py when the design review replaced
    # it with the fully crossed matrix.  A diagonal-only measurement cannot
    # support the derangement arms or the balanced-panel calibration, so
    # leaving the lane here would be an invitation to run the superseded
    # experiment by accident.


if __name__ == "__main__":
    main()
