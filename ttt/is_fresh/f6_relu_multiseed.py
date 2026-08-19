"""F6 -- the two-layer-ReLU (beyond-the-exact-model) probe at fresh seeds.

CLASSIFICATION OF THE ORIGINAL: run_e1.part_e is MEASURED -- it really trains a
network and really runs adapted trajectories -- but it is *seed-frozen*. Its
`rng` argument is never used; every source of randomness is pinned inside the
function (`torch.manual_seed(0)`, generators seeded 100+rep, 999+rep*7+..., and
rep*31+1). Running run_e1 with --seed 43 reproduces part_e bit for bit. The
published numbers "alpha=0 mean excess 0.0411" and "alpha=1 vs alpha=0 margin
0.3485" are therefore single-draw values with no uncertainty attached, and the
paper reports them without one.

WHAT THIS SCRIPT DOES
Re-runs the same experimental design -- same architecture, same source task,
same synthetic (alpha, sigma) construction of the SSL gradient, same adaptation
recursion, same summary statistics -- with every seed replaced by a fresh one
in the 20260801+ range and threaded properly, so that each seed is an
independent replication. Headline numbers are reported as mean and range over
>= 5 seeds.

The design is deliberately unchanged: the point of part_e is to check
Theorem 2's *implication* (assume alignment alpha and noise sigma, get the
Theorem 1 curve shape) in a nonconvex model, which requires constructing the
SSL gradient from the oracle task gradient. That is a legitimate design; the
defect being repaired here is the missing seed variation, not the design.

PROTOCOL (per seed)
  * source task: random two-layer teacher, d = 20, n = 20000, student
    20-128-128-1 MLP trained 30 epochs with Adam(1e-3).
  * 3 shift replicates x delta_scale in {0.5, 1, 2} x alpha in
    {0, 0.25, 0.5, 0.75, 1} x sigma_rel in {0.5, 2}; T = 200 adaptation steps.
  * statistics: alpha0_mean_harm = mean(final risk - initial risk) at alpha=0;
    mean relative best-gain per alpha; margin = relgain(alpha=1) -
    relgain(alpha=0); monotonicity in alpha at tolerance 0.02.
  * seeds 20260801..20260805.

REPRODUCTION CHECK (asserted)
Per seed: adaptation at alpha = 0 must be harmful on average (alpha0_mean_harm
> 0) and the margin must be positive -- the two qualitative predictions the
original gate encodes. A seed that violates them is reported, not hidden: the
assertion is collected per seed and only raised if it fails on a majority.
"""
import argparse

import numpy as np
import torch

import common as C

D, N_SRC = 20, 20000
T_AD, ETA_AD = 200, 0.05
ETA_F = 0.05
ALPHAS_E = [0.0, 0.25, 0.5, 0.75, 1.0]
SIGMAS_E = [0.5, 2.0]
DELTAS_E = [0.5, 1.0, 2.0]
N_SHIFT_REPS = 3


def run_seed(seed, device="cuda"):
    dev = device if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    res_rows = []
    for rep in range(N_SHIFT_REPS):
        g = torch.Generator().manual_seed(seed + 1000 * rep)
        W_true = torch.randn(D, 64, generator=g) / np.sqrt(D)
        a_true = torch.randn(64, generator=g) / np.sqrt(64)

        def f_true(x, W=W_true, a=a_true):
            return torch.relu(x @ W) @ a

        X = torch.randn(N_SRC, D, generator=g)
        Y = f_true(X) + 0.05 * torch.randn(N_SRC, generator=g)

        net = torch.nn.Sequential(torch.nn.Linear(D, 128), torch.nn.ReLU(),
                                  torch.nn.Linear(128, 128), torch.nn.ReLU(),
                                  torch.nn.Linear(128, 1)).to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        Xd, Yd = X.to(dev), Y.to(dev)
        for _ep in range(30):
            perm = torch.randperm(N_SRC, device=dev)
            for i in range(0, N_SRC, 256):
                idx = perm[i:i + 256]
                loss = ((net(Xd[idx]).squeeze(-1) - Yd[idx]) ** 2).mean()
                opt.zero_grad()
                loss.backward()
                opt.step()

        for delta_scale in DELTAS_E:
            gg = torch.Generator().manual_seed(
                seed + 7919 * rep + int(delta_scale * 10))
            dW = torch.randn(D, 64, generator=gg) / np.sqrt(D)
            xstar = torch.randn(1, D, generator=gg).to(dev)
            ystar = (f_true(xstar.cpu()) + delta_scale
                     * (torch.relu(xstar.cpu() @ (W_true + 0.3 * dW)) @ a_true
                        - f_true(xstar.cpu()))).to(dev)

            params = list(net.parameters())
            sd = {k: v.clone() for k, v in net.state_dict().items()}

            def pred_grad():
                f = net(xstar).squeeze(-1).mean()
                gs = torch.autograd.grad(f, params)
                gf = torch.cat([gv.reshape(-1) for gv in gs])
                return gf, float(f.item() - ystar.item())

            r0_abs = None
            for alpha in ALPHAS_E:
                for sigma_rel in SIGMAS_E:
                    net.load_state_dict(sd)
                    gperp_seed = torch.Generator(device="cpu").manual_seed(
                        seed + 31 * rep + 3 + int(alpha * 100)
                        + int(sigma_rel * 10))
                    dperp = torch.randn(sum(p_.numel() for p_ in params),
                                        generator=gperp_seed).to(dev)
                    e0 = None
                    curve = []
                    diverged = False
                    for t in range(T_AD + 1):
                        gf, r = pred_grad()
                        risk = r * r
                        if e0 is None:
                            e0 = risk
                            if r0_abs is None:
                                r0_abs = abs(r) + 1e-9
                        if not np.isfinite(risk) or risk > 25 * max(e0, 1e-6):
                            curve.append(25 * max(e0, 1e-6))
                            diverged = True
                            break
                        curve.append(risk)
                        if t == T_AD:
                            break
                        gnorm = gf.norm()
                        ghat = (torch.sign(torch.tensor(r)).item() * gf
                                / (gnorm + 1e-12))
                        perp = dperp - (dperp @ ghat) * ghat
                        perp = perp / (perp.norm() + 1e-12)
                        xi = float(torch.randn(1).item())
                        step = ETA_F * abs(r) / (gnorm + 1e-12)
                        noise_step = ETA_F * sigma_rel * r0_abs / (gnorm + 1e-12)
                        upd = step * (alpha * ghat
                                      + np.sqrt(max(1 - alpha ** 2, 0.0)) * perp) \
                            + noise_step * xi * (gf / (gnorm + 1e-12))
                        with torch.no_grad():
                            off = 0
                            for p_ in params:
                                n_ = p_.numel()
                                p_ -= upd[off:off + n_].view_as(p_)
                                off += n_
                    res_rows.append({"rep": rep, "delta_scale": delta_scale,
                                     "alpha": alpha, "sigma_rel": sigma_rel,
                                     "E0": e0, "best_gain": e0 - min(curve),
                                     "final_risk": curve[-1],
                                     "diverged": diverged,
                                     "t_emp": int(np.argmin(curve))})
            net.load_state_dict(sd)
        print(f"[f6 seed {seed}] shift rep {rep+1}/{N_SHIFT_REPS} done",
              flush=True)

    means = {}
    for r_ in res_rows:
        means.setdefault(r_["alpha"], []).append(
            r_["best_gain"] / max(r_["E0"], 1e-9))
    alpha_keys = sorted(means)
    mean_gain = [float(np.mean(means[k])) for k in alpha_keys]
    a0 = [r_ for r_ in res_rows if r_["alpha"] == 0.0]
    harm0 = float(np.mean([r_["final_risk"] - r_["E0"] for r_ in a0]))
    mono = all(mean_gain[i + 1] >= mean_gain[i] - 0.02
               for i in range(len(mean_gain) - 1))
    margin = mean_gain[-1] - mean_gain[0]
    return {"seed": seed, "device": dev, "n_rows": len(res_rows),
            "rows": res_rows,
            "alpha0_mean_harm": harm0,
            "mean_relgain_by_alpha": dict(zip(map(str, alpha_keys), mean_gain)),
            "monotone": bool(mono), "margin": float(margin),
            "n_diverged": sum(1 for r_ in res_rows if r_["diverged"]),
            "gate_pass": bool(harm0 > 0 and mono and margin > 0.1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    per_seed = []
    for s in args.seeds:
        r = run_seed(s, args.device)
        C.save(r, f"f6_relu_multiseed_seed{s}.json")
        per_seed.append(r)
        print(f"[f6] seed {s}: alpha0_harm={r['alpha0_mean_harm']:.4f} "
              f"margin={r['margin']:.4f} monotone={r['monotone']}", flush=True)

    n_harm_ok = sum(1 for r in per_seed if r["alpha0_mean_harm"] > 0)
    n_margin_ok = sum(1 for r in per_seed if r["margin"] > 0.1)
    assert n_harm_ok > len(per_seed) / 2, (
        "adaptation at alpha=0 is not harmful on a majority of fresh seeds")
    assert n_margin_ok > len(per_seed) / 2, (
        "alpha=1 vs alpha=0 margin below 0.1 on a majority of fresh seeds")

    by_alpha = {}
    for r in per_seed:
        for k, v in r["mean_relgain_by_alpha"].items():
            by_alpha.setdefault(k, []).append(v)
    summary = {
        "script": "f6_relu_multiseed.py",
        "replaces": "run_e1.part_e (measured but seed-frozen; rng unused)",
        "seeds": args.seeds,
        "alpha0_mean_harm": C.mean_range(
            [r["alpha0_mean_harm"] for r in per_seed]),
        "margin_alpha1_minus_alpha0": C.mean_range(
            [r["margin"] for r in per_seed]),
        "mean_relgain_by_alpha": {k: C.mean_range(v)
                                  for k, v in sorted(by_alpha.items(),
                                                     key=lambda kv: float(kv[0]))},
        "n_seeds_monotone": sum(1 for r in per_seed if r["monotone"]),
        "n_seeds_gate_pass": sum(1 for r in per_seed if r["gate_pass"]),
        "n_seeds_alpha0_harmful": n_harm_ok,
        "n_seeds_margin_gt_0.1": n_margin_ok,
        "total_diverged_runs": sum(r["n_diverged"] for r in per_seed),
    }
    C.save(summary, "f6_relu_multiseed_summary.json")
    print("[f6] DONE", flush=True)


if __name__ == "__main__":
    main()
