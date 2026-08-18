"""Wall-clock scoping benchmark for the E2 fix-forward run and the E3
multi-seeding run.

This script runs NO experiment.  It times the exact code paths the two proposed
runs would use, on the local hardware, so the go/no-go decision is made from a
measurement rather than a guess:

  E2 path   ResNet-26+GN (e2_cifar/models.py:ResNet26TTT) --
            (a) one source-training epoch on CIFAR-10 (batch 128), and
            (b) one single-instance entropy adaptation episode
                (N = 1, 20 SGD steps on the BN/GN affine subset with a
                 snapshot/restore around it), which is the unit the E2 `main`
                mode repeats 256 times per (corruption, severity) cell.

  E3 path   torchvision ResNet-50 -- one adaptation step on a batch of 64 at
            224x224 with only BN affine parameters trainable, which is the
            unit run_e3.py repeats steps x batches x (K for ALTA) times.

Printed numbers are seconds; the caller converts them into GPU-hours for the
grid it is considering.  Nothing is written to results/.
"""
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))          # experiments/ttt

DEV = "cuda:0"


def timeit(fn, n, warmup=3):
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / n


def bench_e2():
    from e2_cifar.models import ResNet26TTT
    m = ResNet26TTT(10).to(DEV)
    n_par = sum(p.numel() for p in m.parameters())
    print(f"[e2] ResNet26TTT params: {n_par/1e6:.2f}M")

    # ---- (a) source training throughput
    opt = torch.optim.SGD(m.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    x = torch.randn(128, 3, 32, 32, device=DEV)
    y = torch.randint(0, 10, (128,), device=DEV)

    def train_step():
        opt.zero_grad(set_to_none=True)
        F.cross_entropy(m(x), y).backward()
        opt.step()

    t = timeit(train_step, 30)
    iters_per_epoch = 50_000 // 128
    print(f"[e2] train step (bs128): {t*1000:.1f} ms -> "
          f"{t*iters_per_epoch:.1f} s/epoch -> "
          f"{t*iters_per_epoch*200/3600:.2f} GPU-h for 200 epochs")

    # ---- (b) single-instance entropy adaptation episode (N = 1, 20 steps)
    m.eval()
    for p in m.parameters():
        p.requires_grad_(False)
    affine = []
    for mod in m.modules():
        if isinstance(mod, (torch.nn.GroupNorm, torch.nn.BatchNorm2d)):
            for p in mod.parameters():
                p.requires_grad_(True)
                affine.append(p)
    print(f"[e2] adapted (norm-affine) params: {sum(p.numel() for p in affine)}")
    x1 = torch.randn(1, 3, 32, 32, device=DEV)
    snap = {k: v.detach().clone() for k, v in m.state_dict().items()}

    def episode():
        m.load_state_dict(snap)
        o = torch.optim.SGD(affine, lr=1e-3, momentum=0.9)
        for _ in range(20):
            o.zero_grad(set_to_none=True)
            logits = m(x1)
            p = logits.softmax(-1)
            (-(p * p.clamp_min(1e-12).log()).sum(-1).mean()).backward()
            o.step()

    te = timeit(episode, 10, warmup=2)
    print(f"[e2] entropy episode (N=1, 20 steps + restore): {te*1000:.1f} ms")
    for n_sev, tag in ((3, "severities {1,3,5}"), (5, "all 5 severities")):
        n_ep = 15 * n_sev * 256
        print(f"[e2]   15 corruptions x {tag} x 256 episodes = {n_ep} episodes "
              f"-> {te*n_ep/3600:.2f} GPU-h (adaptation only)")


def bench_e3():
    import torchvision
    try:
        m = torchvision.models.resnet50(weights=None).to(DEV)
    except Exception as e:                      # pragma: no cover
        print(f"[e3] skipped: {e}")
        return
    m.eval()
    for mod in m.modules():
        if isinstance(mod, torch.nn.BatchNorm2d):
            mod.train()
            mod.momentum = 0.0
    for p in m.parameters():
        p.requires_grad_(False)
    affine = [p for mod in m.modules() if isinstance(mod, torch.nn.BatchNorm2d)
              for p in mod.parameters()]
    for p in affine:
        p.requires_grad_(True)
    opt = torch.optim.SGD(affine, lr=2.5e-4, momentum=0.9)
    x = torch.randn(64, 3, 224, 224, device=DEV)

    def step():
        opt.zero_grad(set_to_none=True)
        p = m(x).softmax(-1)
        (-(p * p.clamp_min(1e-12).log()).sum(-1).mean()).backward()
        opt.step()

    t = timeit(step, 20)
    print(f"[e3] ResNet-50 entropy step (bs64, 224px): {t*1000:.1f} ms")
    n_batches = 5000 // 64                       # the E3 per-cell subset
    fixed = t * 10 * n_batches
    alta = t * 3 * 10 * n_batches
    print(f"[e3]   one (method, severity) FIXED run  (10 steps x {n_batches} "
          f"batches): {fixed/60:.1f} min")
    print(f"[e3]   one (method, severity) ALTA  run  (K=3): {alta/60:.1f} min")
    per_seed_defocus = (fixed + alta) * 3 * 2    # 3 methods x 2 severities
    print(f"[e3]   defocus_blur family, 1 seed "
          f"(3 methods x {{fixed,alta}} x 2 severities): "
          f"{per_seed_defocus/3600:.2f} GPU-h")
    print(f"[e3]   full 15-corruption summary row, 1 seed: "
          f"{per_seed_defocus*15/3600:.2f} GPU-h")


if __name__ == "__main__":
    print(f"torch {torch.__version__}, device "
          f"{torch.cuda.get_device_name(0)}", flush=True)
    bench_e2()
    print(flush=True)
    bench_e3()
