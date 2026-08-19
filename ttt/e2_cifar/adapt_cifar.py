"""E2 — episodic single-instance adaptation + alignment measurement on CIFAR-C.

Modes:
  main        : (a) alpha/sigma/gain measurement, all corruptions x severities,
                fixed-step grid + ALTA stop. Single instance (N=1).
  batch_sweep : (b) Tent batch-size effect, N in {1..64}, severity 5.
  calib       : (c) alpha_ent vs confidence/calibration; optional temperature
                scaling fitted on CLEAN test set (labels used for calibration
                fitting only; corrupted sets remain the evaluation target).

One job = one (dataset, arch/method, seed); loops corruptions internally.
"""
import argparse
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed, run_meta  # noqa: E402
from core.adapt import (EpisodeRunner, SSL_LOSSES, measure_alignment)  # noqa: E402
from core.alta import ALTAConfig, alta_run  # noqa: E402
from e2_cifar.data import CORRUPTIONS, corrupted_tensor, get_test_loader  # noqa: E402
from e2_cifar.models import ResNet26TTT, WRN2810, attach_recon_head  # noqa: E402

METHOD_ARCH = {"ttt_rot": "resnet26ttt", "ttt_mask": "resnet26ttt",
               "tent": "wrn2810", "pl": "wrn2810"}
DEFAULT_LR = {"ttt_rot": 1e-3, "ttt_mask": 1e-3, "tent": 1e-3, "pl": 1e-3}


def load_model(method, dataset, seed, ckpt_dir, device, bn_mode="eval"):
    nc = 10 if dataset == "cifar10" else 100
    arch = METHOD_ARCH[method]
    tag = f"{dataset}_{arch}_s{seed}"
    blob = torch.load(os.path.join(ckpt_dir, f"{tag}.pt"), map_location="cpu",
                      weights_only=False)
    model = ResNet26TTT(nc) if arch == "resnet26ttt" else WRN2810(nc)
    model.load_state_dict(blob["model"])
    if method == "ttt_mask":
        attach_recon_head(model)
        if "recon_head" not in blob:
            raise RuntimeError(f"recon head missing in {tag}.pt — run train_recon_head first")
        model.recon_head.load_state_dict(blob["recon_head"])
    model.to(device).eval()
    if bn_mode == "train":
        # published-Tent reference protocol: BN uses test-batch statistics
        for m in model.modules():
            if isinstance(m, torch.nn.BatchNorm2d):
                m.train()
    for p in model.parameters():
        p.requires_grad_(True)
    return model


@torch.no_grad()
def clean_ref_loss(model, dataset, data_root, device, n_max=2000):
    loader = get_test_loader(dataset, data_root, 256)
    tot = n = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        tot += float(F.cross_entropy(model(x), y, reduction="sum").item())
        n += y.numel()
        if n >= n_max:
            break
    return tot / n


def fit_temperature(model, dataset, data_root, device, index_range=(0, 5000)):
    """Fit softmax temperature on clean test indices [lo, hi) ONLY — episodes
    later use the disjoint index pool, avoiding same-image leakage."""
    loader = get_test_loader(dataset, data_root, 512)
    logits_all, ys = [], []
    with torch.no_grad():
        for x, y in loader:
            logits_all.append(model(x.to(device)).cpu())
            ys.append(y)
    lo, hi = index_range
    L = torch.cat(logits_all)[lo:hi]
    Y = torch.cat(ys)[lo:hi]
    logT = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=50)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(L / logT.exp(), Y)
        loss.backward()
        return loss
    opt.step(closure)
    return float(logT.exp().item())


def episode_indices(n_total, episodes, seed):
    return np.random.default_rng(seed).choice(n_total, size=min(episodes, n_total),
                                              replace=False)


def run_main(args, model, device, clean_ref):
    runner = EpisodeRunner(model, args.method, args.lr)
    step_grid = sorted(set([1, 2, 5, 10, args.steps]))
    sev_list = [int(s) for s in args.severities.split(",")]
    results = []
    for corr in args.corruptions:
        for sev in sev_list:
            xs, ys = corrupted_tensor(args.dataset, args.data_root, corr, sev,
                                      n=None, seed=0)
            idx = episode_indices(len(xs), args.episodes, args.seed * 977 + sev)
            cell = {"corruption": corr, "severity": sev, "episodes": []}
            for j, i in enumerate(idx):
                x = xs[i:i + 1].to(device)
                y = ys[i:i + 1].to(device)
                runner.snapshot()   # measurement may touch BN stats (train mode)
                meas = measure_alignment(model, x, y, args.method,
                                         n_draws=8, base_seed=j)
                runner.restore()
                runner.snapshot()
                rec = runner.adapt(x, steps=args.steps, seed=j,
                                   record_logits_at=set(step_grid))
                step_stats = {}
                for (t, logits) in rec:
                    loss_t = float(F.cross_entropy(logits.to(device), y).item())
                    step_stats[str(t)] = {"loss": loss_t,
                                          "correct": int(logits.argmax(1).item() == int(y.item()))}
                runner.restore()
                # ALTA (K replicas, prediction-level output)
                alta_res = None
                if args.alta:
                    cfg = ALTAConfig(K=3, T_max=args.steps)
                    with torch.no_grad():
                        pred0 = model(x).detach().cpu().numpy().ravel()
                    reps = []
                    for k in range(cfg.K):
                        runner.snapshot()
                        traj = runner.adapt(x, steps=args.steps, seed=1000 * k + j,
                                            record_logits_at=set(range(1, args.steps + 1)))
                        runner.restore()
                        reps.append([lg.numpy().ravel() for (_, lg) in traj])
                    step_fn_state = [{"i": 0, "seq": r} for r in reps]

                    def mk(st):
                        def fn():
                            v = st["seq"][st["i"]]
                            st["i"] += 1
                            return v
                        return fn
                    tr = alta_run([mk(s) for s in step_fn_state], cfg, pred0=pred0)
                    logits_hat = torch.from_numpy(tr.pred_at_t_hat).unsqueeze(0).to(device)
                    alta_res = {"t_hat": int(tr.t_hat),
                                "loss": float(F.cross_entropy(logits_hat, y).item()),
                                "correct": int(logits_hat.argmax(1).item() == int(y.item()))}
                with torch.no_grad():
                    p = F.softmax(model(x), 1)
                    conf = float(p.max().item())
                cell["episodes"].append({
                    "idx": int(i), **meas, "confidence": conf,
                    "frozen_correct": int(model(x).argmax(1).item() == int(y.item())),
                    "delta_proxy": meas["frozen_loss"] - clean_ref,
                    "steps": step_stats, "alta": alta_res})
            results.append(cell)
            print(f"[e2] {args.method} {corr} s{sev}: done "
                  f"({len(cell['episodes'])} episodes)", flush=True)
    return results


def run_batch_sweep(args, model, device, clean_ref):
    runner = EpisodeRunner(model, args.method, args.lr)
    Ns = [1, 2, 4, 8, 16, 32, 64]
    results = []
    for corr in args.corruptions:
        xs, ys = corrupted_tensor(args.dataset, args.data_root, corr, 5, n=None, seed=0)
        for N in Ns:
            rng = np.random.default_rng(args.seed * 31 + N)
            n_batches = min(args.episodes, 64)
            cell = {"corruption": corr, "severity": 5, "N": N, "batches": []}
            for b in range(n_batches):
                sel = rng.choice(len(xs), size=N, replace=False)
                x = xs[sel].to(device)
                y = ys[sel].to(device)
                runner.snapshot()
                meas = measure_alignment(model, x, y, args.method,
                                         n_draws=min(8, max(N, 2)), base_seed=b)
                runner.restore()
                step_grid = sorted(set([1, 2, 5, args.steps]))
                runner.snapshot()
                rec = runner.adapt(x, steps=args.steps, seed=b,
                                   record_logits_at=set(step_grid))
                runner.restore()
                step_stats = {}
                for (t, logits) in rec:
                    lg = logits.to(device)
                    step_stats[str(t)] = {
                        "loss": float(F.cross_entropy(lg, y).item()),
                        "acc": float((lg.argmax(1) == y).float().mean().item())}
                last = step_stats[str(args.steps)]
                with torch.no_grad():
                    lf = model(x)
                cell["batches"].append({
                    **meas,
                    "frozen_acc": float((lf.argmax(1) == y).float().mean().item()),
                    "adapted_loss": last["loss"], "adapted_acc": last["acc"],
                    "steps": step_stats})
            results.append(cell)
        print(f"[e2:batch] {corr} done", flush=True)
    return results


def run_calib(args, model, device, clean_ref):
    """alpha_ent vs confidence/calibration, with and without temperature scaling,
    PLUS actual tent adaptation outcome under both settings (T3 verification).

    Leakage control (temperature must not see the calibration episodes):
    temperature is fitted on clean
    test indices [0, 5000); calib episodes are drawn ONLY from indices
    [5000, 10000) of the corrupted sets (CIFAR-C images are corrupted versions of
    the same test identities, so the two pools are image-disjoint)."""
    temp = fit_temperature(model, args.dataset, args.data_root, device,
                           index_range=(0, 5000))
    results = {"temperature": temp, "cells": []}
    orig_fc = model.fc

    class ScaledFC(torch.nn.Module):
        def __init__(self, fc, T):
            super().__init__()
            self.fc = fc
            self.T = T

        def forward(self, h):
            return self.fc(h) / self.T

    for use_temp in [False, True]:
        model.fc = ScaledFC(orig_fc, temp) if use_temp else orig_fc
        runner = EpisodeRunner(model, "tent", args.lr)
        for corr in args.corruptions:
            xs, ys = corrupted_tensor(args.dataset, args.data_root, corr, 5, n=None, seed=0)
            rng = np.random.default_rng(args.seed * 7 + 5)
            pool = np.arange(5000, len(xs))
            idx = rng.choice(pool, size=min(args.episodes, len(pool)), replace=False)
            eps = []
            for j, i in enumerate(idx):
                x = xs[i:i + 1].to(device)
                y = ys[i:i + 1].to(device)
                runner.snapshot()
                meas = measure_alignment(model, x, y, "tent", base_seed=j)
                runner.restore()
                with torch.no_grad():
                    p = F.softmax(model(x), 1)
                step_grid = sorted(set([1, 2, 5, args.steps]))
                runner.snapshot()
                rec = runner.adapt(x, steps=args.steps, seed=j,
                                   record_logits_at=set(step_grid))
                runner.restore()
                step_stats = {}
                for (t, logits_a) in rec:
                    lg = logits_a.to(device)
                    step_stats[str(t)] = {
                        "loss": float(F.cross_entropy(lg, y).item()),
                        "correct": int(lg.argmax(1).item() == int(y.item()))}
                last = step_stats[str(args.steps)]
                eps.append({"alpha_ent": meas["alpha"],
                            "confidence": float(p.max().item()),
                            "correct": int(p.argmax(1).item() == int(y.item())),
                            "frozen_loss": meas["frozen_loss"],
                            "adapted_loss": last["loss"],
                            "adapted_correct": last["correct"],
                            "steps": step_stats})
            results["cells"].append({"corruption": corr, "temp_scaled": use_temp,
                                     "episodes": eps})
            print(f"[e2:calib] {corr} temp={use_temp} done", flush=True)
    model.fc = orig_fc
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--method", required=True, choices=list(SSL_LOSSES))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--mode", default="main", choices=["main", "batch_sweep", "calib"])
    ap.add_argument("--episodes", type=int, default=256)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--severities", default="1,2,3,4,5")
    ap.add_argument("--corruptions", nargs="*", default=CORRUPTIONS)
    ap.add_argument("--alta", action="store_true")
    ap.add_argument("--bn-mode", default="eval", choices=["eval", "train"],
                    help="eval = frozen running stats (theory-aligned); "
                         "train = published-Tent test-batch statistics")
    ap.add_argument("--data-root", default="workdir/data")
    ap.add_argument("--ckpt-dir", default="workdir/ttt/ckpt")
    ap.add_argument("--out-dir", default="workdir/ttt/results/e2")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.lr is None:
        args.lr = DEFAULT_LR[args.method]
    if args.smoke:
        args.episodes = 4
        args.corruptions = args.corruptions[:2]
        args.severities = "5"
        args.steps = 5
    set_seed(args.seed)
    from core.adapt import STOCHASTIC
    if args.alta and not STOCHASTIC[args.method]:
        print(f"[e2] WARNING: {args.method} is deterministic at N=1 — ALTA "
              "replicas would be identical; disabling ALTA for this run.")
        args.alta = False
    device = "cuda"
    model = load_model(args.method, args.dataset, args.seed, args.ckpt_dir, device,
                       bn_mode=args.bn_mode)
    clean_ref = clean_ref_loss(model, args.dataset, args.data_root, device)
    fn = {"main": run_main, "batch_sweep": run_batch_sweep, "calib": run_calib}[args.mode]
    results = fn(args, model, device, clean_ref)
    tag = f"{args.dataset}_{args.method}_{args.mode}_s{args.seed}"
    if args.bn_mode == "train":
        tag += "_bntrain"
    if args.lr != DEFAULT_LR[args.method]:
        tag += f"_lr{args.lr:g}"
    save_json({"meta": run_meta(args), "clean_ref_loss": clean_ref,
               "results": results},
              os.path.join(args.out_dir, f"{tag}.json"))
    print(f"[e2] DONE {tag}")


if __name__ == "__main__":
    main()
