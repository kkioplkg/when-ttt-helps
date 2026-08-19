"""F15 -- de-confound the E2 stochastic-vs-deterministic comparison by running
the ENTROPY objective on the ResNet-26+GN architecture.

THE CONFOUND
In E2 as published, the two regimes differ in four things at once:

    ttt_rot / ttt_mask   ResNet-26 + GroupNorm, stochastic SSL objective
    tent / pl            WRN-28-10 + BatchNorm, deterministic objective

and the paper reads the sign flip of the phase-statistic/gain correlation
(positive for the first pair, strongly negative for the second) as evidence
that violating the stochastic-gradient assumption A2 is what breaks the
prediction.  But architecture, normalisation layer, source
model and objective all change together, so nothing in the comparison isolates
the objective.  (Separately: failure of an assumption does not predict that the
correlation must go NEGATIVE -- only that the guarantee lapses.)

THE FIX-FORWARD
Run the deterministic entropy objective on the SAME source architecture the
stochastic objectives use -- ResNet-26 + GroupNorm, trained with the unchanged
original `e2_cifar/train_source.py` -- under the unchanged original E2
episodic protocol (`e2_cifar/adapt_cifar.py --mode main`).  Then

    tent @ ResNet-26+GN   vs   ttt_rot / ttt_mask @ ResNet-26+GN
        differ ONLY in the objective;
    tent @ ResNet-26+GN   vs   tent @ WRN-28-10+BN
        differ ONLY in the architecture / normalisation.

Two contrasts, one held-fixed factor each.  Whatever the correlation does, the
confound is gone.

WHAT THIS SCRIPT CHANGES vs THE ORIGINAL CODE
Exactly one thing: `adapt_cifar.METHOD_ARCH["tent"]` is remapped from
"wrn2810" to "resnet26ttt" so the entropy runner loads the GN source model.
Everything else -- the episode sampler, the alignment measurement, the
adaptation subset (`METHOD_SUBSET["tent"] = "bn"`, which `collect_params`
already resolves to GroupNorm affine parameters), the loss, the step grid and
the record format -- is the original code, imported not copied.  The output
JSON therefore has the same schema the E2 aggregator already reads.

PROTOCOL (reduced-but-decisive grid)
  * dataset CIFAR-10-C, 15 corruptions x severities {1, 3, 5}
  * 256 episodes per cell, single instance (N = 1), 20 adaptation steps,
    lr 1e-3, bn-mode eval  -- identical to the published E2 `main` runs
  * ALTA is not used (adapt_cifar disables it for deterministic objectives at
    N = 1, where the K replicas would be identical)
  * seed 20260806 (fresh range; the original E2 used seeds 0/1/2), used both
    for source training and for the adaptation run, because
    `adapt_cifar.load_model` keys the checkpoint by the run seed.

SOURCE MODEL
Trained here from scratch with the original `train_source.py`
(200 epochs, SGD 0.1 / cosine, batch 128), because the only local
ResNet-26+GN CIFAR-10 checkpoints live under directories this work stream is
not permitted to read.  The gate asserted before any adaptation runs is that
the fresh source model is COMPARABLE TO THE PUBLISHED ONES, because that -- not
an absolute accuracy -- is what makes the contrast interpretable.

CRASH POSTMORTEM / FIX (2026-08-03), seed UNCHANGED at 20260806
    The first launch died during source training (last line ep140
    acc=0.8741 rot=0.8504, 56.6 min) with no Python traceback in the captured
    log, no Windows Error Reporting event, no OOM and no partial checkpoint.
    Two independent defects were found:

    (1) LATENT, FATAL, AND CERTAIN: this script asserted `gate_pass` from
        `train_source.py`, whose CIFAR-10 threshold for `resnet26ttt` is
        test acc >= 0.93.  The PUBLISHED E2 source models never met it --
        `experiments/results/m0/cifar10_resnet26ttt_s{0,1,2}.json` record
        final test acc 0.9203 / 0.9152 / 0.9216 (rot 0.9121 / 0.9061 / 0.9064)
        and `"gate_pass": false` in all three.  The 0.93 number in
        `train_source.py` is an aspiration that the models the paper actually
        used do not satisfy.  The fresh run was tracking those curves almost
        exactly (fresh ep140 acc 0.8741 vs published ep140 0.8742 / 0.8689 /
        0.8864), so it would have trained the full 200 epochs, landed at
        ~0.92, and then aborted on the assertion having thrown the
        checkpoint away.  The gate is therefore restated as the comparability
        criterion it was meant to be: rotation acc >= 0.85 (the original
        rotation gate, which the published models DO pass) and test acc >=
        0.905, i.e. no worse than the weakest published source model (0.9152)
        less a one-point tolerance.  The published range is loaded from the
        m0 records and written into the output for audit.  This changes no
        random number, so the seed stays 20260806.

    (2) NO FORENSICS AND NO CRASH TOLERANCE: only stdout was captured, so
        whatever ended the process left no record, and neither phase wrote
        anything incrementally -- 57 minutes of training produced zero bytes.
        Now: `faulthandler` is armed, the top level logs its traceback, a
        heartbeat lands in `f15_progress.log` every epoch and every
        corruption block, the weights are snapshotted every 10 epochs, and
        the adaptation phase writes per-corruption partial results and
        resumes from them.  The relaunch redirects stderr to a file too.

    The adaptation phase is chunked one corruption at a time by calling the
    ORIGINAL `adapt_cifar.run_main` once per corruption instead of once for
    all 15.  The records are bit-identical: at N = 1 with `tent`, nothing in
    `measure_alignment` or `EpisodeRunner.adapt` touches global RNG state
    (`entropy_loss` ignores its seed; `sigma2` short-circuits to 0.0 at
    N = 1), and `episode_indices` is seeded by `args.seed * 977 + sev`, which
    does not depend on the corruption or on how many ran before it.

COST (measured on the local RTX 3080 by f_scope_bench.py)
  source training   16.4 ms/step x 390 steps x 200 epochs  ~= 0.36 GPU-h
  adaptation        280 ms/episode x 15 x 3 x 256 episodes ~= 0.90 GPU-h
                    plus the per-episode alignment measurement (8 draws)
  total budget      ~2 GPU-h on one GPU, inside the 6 GPU-h ceiling.

OUTPUT
  experiments/results/is_fresh/e2_gn/cifar10_resnet26ttt_s20260806.pt  (ckpt)
  experiments/results/is_fresh/e2_gn/cifar10_tent_main_s20260806.json  (episodes)
  experiments/results/is_fresh/e2_gn/f15_progress.log         (heartbeat)
  experiments/results/is_fresh/e2_gn/f15_train_partial.pt     (every 10 epochs)
  experiments/results/is_fresh/e2_gn/f15_partial_cells.json   (per corruption)

The correlation analysis over these records is a separate pass (it reuses
f8_e2_crossfit.py's cross-fit machinery), so this script only produces the
records.
"""
import argparse
import datetime
import faulthandler
import json
import os
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_TTT = os.path.dirname(_HERE)
for _p in (_TTT,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

REPO = os.path.dirname(_TTT)


def rel(path):
    """Repository-relative POSIX form, for anything that is printed.

    The progress log and the run log are archived, so they must never carry
    the build machine's absolute prefix.  Mirrors `common.rel`; kept local
    because this script is deliberately import-light on the GPU host.
    """
    p = os.path.abspath(path)
    try:
        r = os.path.relpath(p, REPO)
    except ValueError:                      # different drive on Windows
        return os.path.basename(p)
    r = r.replace("\\", "/")
    return os.path.basename(p) if r.startswith("../") else r


DATA_ROOT = os.path.join(REPO, "data")
OUT_DIR = os.path.join(REPO, "results", "is_fresh", "e2_gn")
SEED = 20260806
ARCH = "resnet26ttt"
DATASET = "cifar10"

PROG_LOG = os.path.join(OUT_DIR, "f15_progress.log")
TRAIN_PARTIAL = os.path.join(OUT_DIR, "f15_train_partial.pt")
CELLS_PARTIAL = os.path.join(OUT_DIR, "f15_partial_cells.json")

# Published E2 source models (experiments/results/m0/) -- the comparability
# reference for the training gate.  Loaded at gate time; this is the fallback
# if the records are unreadable.
PUB_ACC_MIN = 0.9152
GATE_ACC = 0.905          # weakest published source model less 1 point
GATE_ROT = 0.85           # unchanged original rotation gate

_T0 = time.time()


def hb(msg):
    """Heartbeat: one timestamped line to stdout AND to f15_progress.log."""
    line = (f"{datetime.datetime.now().strftime('%H:%M:%S')} "
            f"[+{(time.time() - _T0) / 60:6.1f}m] {msg}")
    print(f"[f15] {msg}", flush=True)
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(PROG_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass


class _NpCifar:
    """CIFAR-10 clean split served from the local .npy arrays (module level so
    Windows `spawn` DataLoader workers can pickle it)."""

    def __init__(self, npdir, train, transform):
        import numpy as np
        tag = "train" if train else "test"
        self.x = np.load(os.path.join(npdir, f"{tag}_x.npy"))
        self.y = np.load(os.path.join(npdir, f"{tag}_y.npy"))
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        from PIL import Image
        return self.transform(Image.fromarray(self.x[i])), int(self.y[i])


def install_offline_cifar10():
    """Serve the CLEAN CIFAR-10 split from the local numpy arrays.

    `e2_cifar/data.py` builds its clean loaders with `torchvision.datasets.
    CIFAR10(..., download=True)`, which on this machine tries to reach the
    network because the cached `cifar-10-python.tar.gz` is a 1 MB truncated
    stub.  The genuine arrays are present as `experiments/data/cifar10_np/
    {train,test}_{x,y}.npy`, so this function swaps the loader route -- not the
    data, not the transforms, not the batch size, not the shuffling.

    Integrity is asserted, not assumed: `test_y` must equal each of the five
    10,000-image label blocks of `CIFAR-10-C/labels.npy` (CIFAR-10-C is the
    clean test set corrupted in place, so its labels ARE the clean test
    labels), and both splits must be exactly class-balanced.  If the local
    arrays were not the standard CIFAR-10 split, that check fails.
    """
    import numpy as np
    from torch.utils.data import DataLoader

    from e2_cifar import data as D

    npdir = os.path.join(DATA_ROOT, "cifar10_np")
    ty = np.load(os.path.join(npdir, "test_y.npy"))
    tr_y = np.load(os.path.join(npdir, "train_y.npy"))
    lc = np.load(os.path.join(DATA_ROOT, "CIFAR-10-C", "labels.npy"))
    for b in range(5):
        assert (lc[b * 10000:(b + 1) * 10000] == ty).all(), (
            "local clean CIFAR-10 test labels do not match the CIFAR-10-C "
            "label blocks -- the local arrays are not the standard split")
    assert (np.bincount(tr_y) == 5000).all() and (np.bincount(ty) == 1000).all()

    def get_train_loader(ds, root, batch_size=128, workers=8):
        assert ds == "cifar10", ds
        return DataLoader(_NpCifar(npdir, True, D.train_transforms(ds)),
                          batch_size=batch_size, shuffle=True,
                          num_workers=workers, pin_memory=True, drop_last=True,
                          persistent_workers=bool(workers))

    def get_test_loader(ds, root, batch_size=256, workers=0):
        assert ds == "cifar10", ds
        return DataLoader(_NpCifar(npdir, False, D.test_transforms(ds)),
                          batch_size=batch_size, shuffle=False,
                          num_workers=workers, pin_memory=True)

    D.get_train_loader = get_train_loader
    D.get_test_loader = get_test_loader
    for modname in ("e2_cifar.train_source", "e2_cifar.adapt_cifar"):
        mod = sys.modules.get(modname)
        if mod is None:
            continue
        if hasattr(mod, "get_train_loader"):
            mod.get_train_loader = get_train_loader
        if hasattr(mod, "get_test_loader"):
            mod.get_test_loader = get_test_loader
    print("[f15] offline CIFAR-10 clean loaders installed (integrity OK)",
          flush=True)


def _install_training_hooks(TS, epochs):
    """Per-epoch heartbeat + a weights snapshot every 10 epochs, WITHOUT
    forking the original training loop.

    Two hooks into `train_source.main`'s own call sites: the cosine scheduler's
    `.step()` (called exactly once per epoch) and `evaluate` (called every 10
    epochs, and holding the live model).  Neither changes the recipe, the data,
    the optimiser or any random draw.  Returns an undo callable.
    """
    import torch

    sched_cls = torch.optim.lr_scheduler.CosineAnnealingLR

    class _HeartbeatCosine(sched_cls):
        n = 0

        def __init__(self, *a, **k):
            super().__init__(*a, **k)      # base __init__ calls step() once
            _HeartbeatCosine.n = 0

        def step(self, *a, **k):
            super().step(*a, **k)
            _HeartbeatCosine.n += 1
            if _HeartbeatCosine.n <= epochs:
                hb(f"train epoch {_HeartbeatCosine.n}/{epochs} "
                   f"lr={self.get_last_lr()[0]:.5f}")

    orig_eval = TS.evaluate

    def _eval_hook(model, loader, device, ssl=False):
        acc, rot = orig_eval(model, loader, device, ssl)
        hb(f"train eval ep{_HeartbeatCosine.n} acc={acc:.4f} rot={rot}")
        try:
            tmp = TRAIN_PARTIAL + ".tmp"
            torch.save({"model": model.state_dict(),
                        "epoch": _HeartbeatCosine.n,
                        "test_acc": acc, "rot_acc": rot}, tmp)
            os.replace(tmp, TRAIN_PARTIAL)
        except OSError as e:                      # never kill training for this
            hb(f"WARNING: partial checkpoint write failed: {e}")
        return acc, rot

    torch.optim.lr_scheduler.CosineAnnealingLR = _HeartbeatCosine
    TS.evaluate = _eval_hook

    def undo():
        torch.optim.lr_scheduler.CosineAnnealingLR = sched_cls
        TS.evaluate = orig_eval
    return undo


def train_source(seed, epochs, ckpt_dir, out_dir):
    tag = f"{DATASET}_{ARCH}_s{seed}"
    ckpt = os.path.join(ckpt_dir, f"{tag}.pt")
    if os.path.exists(ckpt):
        hb(f"source checkpoint present, skipping training: {ckpt}")
        return ckpt
    from e2_cifar import train_source as TS
    install_offline_cifar10()
    argv = ["train_source.py", "--dataset", DATASET, "--arch", ARCH,
            "--seed", str(seed), "--epochs", str(epochs),
            "--data-root", DATA_ROOT, "--out-dir", out_dir,
            "--ckpt-dir", ckpt_dir]
    old = sys.argv
    sys.argv = argv
    undo = _install_training_hooks(TS, epochs)
    hb(f"source training start: {tag}, {epochs} epochs")
    try:
        TS.main()
    finally:
        sys.argv = old
        undo()
    hb(f"source training done: {rel(ckpt)}")
    return ckpt


def published_source_reference():
    """Final accuracies of the PUBLISHED E2 ResNet-26+GN source models.

    `experiments/results/m0/cifar10_resnet26ttt_s{0,1,2}.json` are the records
    of the models the paper's E2 numbers were produced with.  They are the
    right comparability target, and they report `"gate_pass": false` -- the
    0.93 threshold hard-coded in `train_source.py` is not met by any of them.
    """
    ref = []
    for s in (0, 1, 2):
        p = os.path.join(REPO, "results", "m0",
                         f"{DATASET}_{ARCH}_s{s}.json")
        try:
            with open(p, encoding="utf-8") as f:
                o = json.load(f)
        except OSError:
            continue
        ref.append({"seed": s, "test_acc": o["final"]["test_acc"],
                    "rot_acc": o["final"]["rot_acc"],
                    "train_source_gate_pass": o.get("gate_pass")})
    return ref


def assert_source_gate(out_dir, seed):
    """Comparability gate -- see the CRASH POSTMORTEM note in the module
    docstring for why this is NOT `train_source.py`'s `gate_pass` flag."""
    p = os.path.join(out_dir, f"{DATASET}_{ARCH}_s{seed}.json")
    with open(p, encoding="utf-8") as f:
        o = json.load(f)
    final = o["final"]
    acc, rot = float(final["test_acc"]), float(final["rot_acc"])
    ref = published_source_reference()
    if ref:
        lo = min(r["test_acc"] for r in ref)
        hi = max(r["test_acc"] for r in ref)
        hb(f"published source models: test acc {lo:.4f}-{hi:.4f} "
           f"(train_source gate_pass="
           f"{[r['train_source_gate_pass'] for r in ref]})")
    else:
        lo = hi = PUB_ACC_MIN
        hb("WARNING: published m0 records unreadable; using the recorded "
           f"minimum {PUB_ACC_MIN}")
    assert rot >= GATE_ROT, (
        f"fresh ResNet-26+GN source model fails the rotation gate "
        f"(rot {rot:.4f} < {GATE_ROT}); the TTT branch is not trained and the "
        f"architecture-controlled contrast would not be interpretable")
    assert acc >= GATE_ACC, (
        f"fresh ResNet-26+GN source model is not comparable to the published "
        f"E2 source models (acc {acc:.4f} < {GATE_ACC}; published "
        f"{lo:.4f}-{hi:.4f}); the architecture-controlled contrast would not "
        f"be interpretable")
    hb(f"source gate OK: acc={acc:.4f} (>= {GATE_ACC}, published "
       f"{lo:.4f}-{hi:.4f})  rot={rot:.4f} (>= {GATE_ROT})")
    gate = {"test_acc": acc, "rot_acc": rot, "gate_acc": GATE_ACC,
            "gate_rot": GATE_ROT, "published_reference": ref}
    with open(os.path.join(out_dir, "f15_source_gate.json"), "w",
              encoding="utf-8") as f:
        json.dump(gate, f, indent=1)
    return final


def _install_chunked_run_main(AC):
    """Run the ORIGINAL `adapt_cifar.run_main` one corruption at a time,
    persisting the finished cells after each, and resuming from them.

    Bit-identical to the monolithic call: every random draw in the tent / N=1
    path is explicitly seeded and independent of the corruption order
    (`episode_indices` keys off `args.seed * 977 + sev`; `entropy_loss` ignores
    its seed; `sigma2` short-circuits at N = 1), and `EpisodeRunner`
    snapshots/restores the model around every episode, so no state crosses a
    chunk boundary that would not have crossed an episode boundary.
    """
    orig = AC.run_main

    def wrapper(args, model, device, clean_ref):
        all_corr = list(args.corruptions)
        done, cells = [], []
        if os.path.exists(CELLS_PARTIAL):
            try:
                with open(CELLS_PARTIAL, encoding="utf-8") as f:
                    blob = json.load(f)
                if abs(blob.get("clean_ref_loss", 1e9) - clean_ref) < 1e-9:
                    done, cells = blob["done"], blob["cells"]
                    hb(f"resuming adaptation from {len(done)}/{len(all_corr)} "
                       f"completed corruptions")
                else:
                    hb("partial cells file is from a different source model; "
                       "ignoring it and restarting the adaptation phase")
            except (OSError, ValueError, KeyError) as e:
                hb(f"WARNING: unreadable partial cells file ({e}); restarting "
                   "the adaptation phase")
        try:
            for corr in all_corr:
                if corr in done:
                    continue
                t = time.time()
                args.corruptions = [corr]
                cells.extend(orig(args, model, device, clean_ref))
                done.append(corr)
                tmp = CELLS_PARTIAL + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"done": done, "cells": cells,
                               "clean_ref_loss": clean_ref}, f)
                os.replace(tmp, CELLS_PARTIAL)
                hb(f"adapt corruption {len(done)}/{len(all_corr)} {corr} "
                   f"done in {(time.time() - t) / 60:.1f} min "
                   f"({len(cells)} cells persisted)")
        finally:
            args.corruptions = all_corr
        return cells

    AC.run_main = wrapper


def run_entropy(seed, ckpt_dir, out_dir, episodes, steps, severities):
    from e2_cifar import adapt_cifar as AC
    install_offline_cifar10()
    assert AC.METHOD_ARCH["tent"] == "wrn2810", (
        "adapt_cifar.METHOD_ARCH['tent'] is not the published mapping; the "
        "one-line remap below would no longer be the only change")
    AC.METHOD_ARCH["tent"] = ARCH            # <-- the entire intervention
    _install_chunked_run_main(AC)
    hb(f"adaptation start: tent @ {ARCH}, {episodes} episodes, {steps} steps, "
       f"severities {severities}")
    argv = ["adapt_cifar.py", "--dataset", DATASET, "--method", "tent",
            "--seed", str(seed), "--mode", "main",
            "--episodes", str(episodes), "--steps", str(steps),
            "--severities", severities, "--bn-mode", "eval",
            "--data-root", DATA_ROOT, "--ckpt-dir", ckpt_dir,
            "--out-dir", out_dir]
    old = sys.argv
    sys.argv = argv
    try:
        AC.main()
    finally:
        sys.argv = old
        AC.METHOD_ARCH["tent"] = "wrn2810"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--episodes", type=int, default=256)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--severities", default="1,3,5")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    # C-level crash forensics: a segfault / abort now leaves a stack behind
    # instead of the silent disappearance that ended the first launch.
    try:
        faulthandler.enable(open(os.path.join(OUT_DIR, "f15_faulthandler.log"),
                                 "a", encoding="utf-8"))
    except OSError:
        faulthandler.enable()
    hb(f"launch pid={os.getpid()} "
       f"CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES', '<all>')} "
       f"seed={args.seed} epochs={args.epochs} episodes={args.episodes}")
    try:
        if not args.skip_train:
            train_source(args.seed, args.epochs, OUT_DIR, OUT_DIR)
            assert_source_gate(OUT_DIR, args.seed)
        run_entropy(args.seed, OUT_DIR, OUT_DIR, args.episodes, args.steps,
                    args.severities)
    except BaseException:
        hb("FATAL -- traceback follows")
        tb = traceback.format_exc()
        try:
            with open(PROG_LOG, "a", encoding="utf-8") as f:
                f.write(tb + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass
        print(tb, file=sys.stderr, flush=True)
        raise
    hb(f"DONE in {(time.time() - _T0) / 60:.1f} min")


if __name__ == "__main__":
    main()
