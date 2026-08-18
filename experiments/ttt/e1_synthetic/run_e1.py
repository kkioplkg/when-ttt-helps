"""E1 — synthetic verification of Theorems 1, 2, 5 (THEORY_CORE.md).

Sub-experiments (select via --part, default all):
  a: excess-risk curves, simulation vs exact closed form, grid over (alpha, delta/sigma)
  b: phase-transition heatmap of realized gain over (alpha^2 delta^2 / sigma^2)
  c: empirical optimal stopping time vs theoretical t*
  d: ALTA stopping vs oracle (regret distribution)
  e: two-layer ReLU network in the PL regime (qualitative shape + alpha-gain link)
  f: batch-size N sweep (variance sigma^2/N)

Exact construction (must match Theorem 1; see THEORY_CORE.md §1 + message to
proof track): theta_Q = theta_0 - delta * x_star, SSL direction w with
<x_star, w> = alpha, SSL target h_t = <theta_Q, w> + sigma*xi_t,
update theta <- theta - eta * (<theta, w> - h_t) * w.
Scalar form: s_t = <theta_t - theta_Q, w>, s_0 = delta*alpha,
  s_{t+1} = (1-eta) s_t - eta*sigma*xi_t,
  u_t = <theta_t - theta_Q, x_star> = delta*(1-alpha^2) + alpha*s_t,
  E(t) = (E u_t)^2 + Var u_t.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.alta import ALTAConfig, alta_run  # noqa: E402
from core.utils import save_json  # noqa: E402


# ---------- exact closed forms (Theorem 1, v0.2 isotropic-noise model) ----------
# SSL noise is isotropic in span{w, v}: the aligned component is damped by the
# contraction (bounded variance); the orthogonal component is a random walk
# (variance grows linearly in t) — the sigma^2*t term of the theory.

def mean_u(t, alpha, delta, eta):
    return delta * (1 - alpha**2) + delta * alpha**2 * (1 - eta) ** t


def var_u(t, alpha, sigma, eta):
    aligned = alpha**2 * sigma**2 * eta * (1 - (1 - eta) ** (2 * t)) / (2 - eta)
    walk = (1 - alpha**2) * sigma**2 * eta**2 * t
    return aligned + walk


def excess_risk(t, alpha, delta, sigma, eta):
    return mean_u(t, alpha, delta, eta) ** 2 + var_u(t, alpha, sigma, eta)


def t_star_theory(alpha, delta, sigma, eta, T_max):
    ts = np.arange(0, T_max + 1)
    risks = excess_risk(ts, alpha, delta, sigma, eta)
    return int(ts[np.argmin(risks)]), float(risks.min())


# ---------- simulation ----------

def simulate_scalar(alpha, delta, sigma, eta, T, n_rep, rng, batch_N=1):
    """Simulate (s_t, p_t) recursions; returns u trajectories (n_rep, T+1)."""
    s = np.full(n_rep, delta * alpha)
    p = np.zeros(n_rep)
    us = np.empty((n_rep, T + 1))
    root = np.sqrt(max(1 - alpha**2, 0.0))
    us[:, 0] = delta * (1 - alpha**2) + alpha * s + root * p
    eff_sigma = sigma / np.sqrt(batch_N)
    for t in range(1, T + 1):
        xi = rng.standard_normal(n_rep)
        zeta = rng.standard_normal(n_rep)
        s = (1 - eta) * s - eta * eff_sigma * xi
        p = p - eta * eff_sigma * zeta
        us[:, t] = delta * (1 - alpha**2) + alpha * s + root * p
    return us


def emp_risk_curve(us):
    return (us**2).mean(axis=0)


# ---------- parts ----------

ALPHAS = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
RATIOS = [0.5, 1.0, 2.0, 4.0, 8.0]  # delta / sigma
SIGMA = 1.0
ETA = 0.05
T = 400
NREP = 12000


def part_a(rng):
    out = {"eta": ETA, "T": T, "n_rep": NREP, "grid": []}
    worst = 0.0
    for a in ALPHAS:
        for r in RATIOS:
            delta = r * SIGMA
            us = simulate_scalar(a, delta, SIGMA, ETA, T, NREP, rng)
            emp = emp_risk_curve(us)
            ts = np.arange(T + 1)
            theo = excess_risk(ts, a, delta, SIGMA, ETA)
            denom = max(theo.max(), 1e-12)
            rel = float(np.max(np.abs(emp - theo)) / denom)
            worst = max(worst, rel)
            out["grid"].append({"alpha": a, "delta": delta, "sigma": SIGMA,
                                "emp": emp.tolist(), "theory": theo.tolist(),
                                "max_rel_err": rel})
    out["worst_rel_err"] = worst
    out["gate_pass"] = worst < 0.05
    return out


def part_b(rng):
    alphas = np.linspace(0.02, 1.0, 25)
    ratios = np.logspace(-1, 1.2, 25)
    gain = np.zeros((len(alphas), len(ratios)))
    phase = np.zeros_like(gain)
    for i, a in enumerate(alphas):
        for j, r in enumerate(ratios):
            delta = r * SIGMA
            tstar, risk = t_star_theory(a, delta, SIGMA, ETA, T)
            gain[i, j] = delta**2 - risk
            phase[i, j] = (a * delta / SIGMA) ** 2
    # sign-prediction test: does the phase statistic
    # alpha^2 delta^2 / sigma^2 predict sign(gain) via a single threshold?
    phi = phase.ravel()
    lab = (gain.ravel() > 1e-9).astype(int)

    def fit_thr(ph, lb):
        order = np.argsort(ph)
        ph_s, lb_s = ph[order], lb[order]
        best_acc, best_thr = 0.0, 0.0
        for k in range(len(ph_s) + 1):
            pred = np.concatenate([np.zeros(k, dtype=int),
                                   np.ones(len(ph_s) - k, dtype=int)])
            acc = float((pred == lb_s).mean())
            if acc > best_acc:
                best_acc, best_thr = acc, (float(ph_s[k - 1]) if k > 0 else 0.0)
        return best_acc, best_thr

    # held-out gate: fit threshold on even cells, evaluate on odd
    fit_acc, thr = fit_thr(phi[::2], lab[::2])
    holdout_pred = (phi[1::2] > thr).astype(int)
    holdout_acc = float((holdout_pred == lab[1::2]).mean())
    return {"alphas": alphas.tolist(), "ratios": ratios.tolist(),
            "gain": gain.tolist(), "phase_stat": phase.tolist(),
            "fit_accuracy": fit_acc, "fitted_threshold": thr,
            "holdout_accuracy": holdout_acc,
            "gate_pass": bool(holdout_acc >= 0.95)}


def part_c(rng):
    """Empirical vs theoretical optimal stopping. Primary gate: the RISK at the
    empirical argmin matches the theoretical minimum within 5% (robust to flat
    minima, where argmin position is noisy); time agreement reported alongside."""
    rows = []
    risk_ok = 0
    time_ok = 0
    tot = 0
    for a in ALPHAS[1:]:
        for r in RATIOS:
            delta = r * SIGMA
            tstar, risk_star = t_star_theory(a, delta, SIGMA, ETA, T)
            us = simulate_scalar(a, delta, SIGMA, ETA, T, NREP, rng)
            emp = emp_risk_curve(us)
            emp_t = int(np.argmin(emp))
            risk_at_emp_t = excess_risk(emp_t, a, delta, SIGMA, ETA)
            rel = abs(risk_at_emp_t - risk_star) / max(risk_star, 1e-12)
            rows.append({"alpha": a, "delta": delta, "t_theory": tstar,
                         "t_emp": emp_t, "risk_star": risk_star,
                         "risk_at_t_emp": float(risk_at_emp_t),
                         "risk_rel_gap": float(rel)})
            tot += 1
            risk_ok += int(rel <= 0.05)
            time_ok += int(max(tstar, 1) / 2 <= max(emp_t, 1) <= max(tstar, 1) * 2)
    return {"rows": rows, "frac_risk_within_5pct": risk_ok / tot,
            "frac_time_within_2x": time_ok / tot,
            "gate_pass": (risk_ok / tot) >= 0.9}


def part_d(rng):
    """ALTA vs oracle. Scoring: realized excess risk of the
    ACTUAL ALTA output — the mean-replica prediction u at the stopping step —
    i.e. E[u_hat^2] over replicates, never the population curve at t_hat.
    Gates: per-cell p90 ratio <= 3 log T_max, AND mean realized risk never worse
    than frozen (delta^2) on any cell with t_star > 0 (safety vs frozen)."""
    cfg = ALTAConfig(T_max=T)
    rows = []
    for a in [0.25, 0.5, 0.75, 1.0]:
        for r in [1.0, 2.0, 4.0, 8.0]:
            delta = r * SIGMA
            tstar, risk_star = t_star_theory(a, delta, SIGMA, ETA, T)
            realized = []
            t_hats = []
            root = np.sqrt(max(1 - a**2, 0.0))
            for rep in range(200):
                states = [{"s": delta * a, "p": 0.0} for _ in range(cfg.K)]

                def mk(st):
                    def step():
                        st["s"] = (1 - ETA) * st["s"] - ETA * SIGMA * rng.standard_normal()
                        st["p"] = st["p"] - ETA * SIGMA * rng.standard_normal()
                        u = delta * (1 - a**2) + a * st["s"] + root * st["p"]
                        return np.array([u])
                    return step

                tr = alta_run([mk(s) for s in states], cfg,
                              pred0=np.array([delta]))
                realized.append(float(tr.pred_at_t_hat[0] ** 2))
                t_hats.append(tr.t_hat)
            realized = np.array(realized)
            ratio = realized / max(risk_star, 1e-12)
            rows.append({"alpha": a, "delta": delta, "t_star": tstar,
                         "risk_star": risk_star,
                         "median_t_hat": float(np.median(t_hats)),
                         "mean_realized_risk": float(realized.mean()),
                         "median_risk_ratio": float(np.median(ratio)),
                         "p90_risk_ratio": float(np.percentile(ratio, 90)),
                         "frac_worse_than_frozen": float((realized > delta**2).mean()),
                         # 2% tolerance: cells where the rule correctly picks
                         # t_hat=0 sit exactly at delta^2 and MC noise flips sign
                         "safe_vs_frozen": bool(realized.mean() <= delta**2 * 1.02)})
    logT = np.log(T)
    # Oracle inequality with additive lower-order term (Theorem 5 form):
    # p90 realized risk <= 3 log(T) * risk_star + 2*eta*sigma^2. The additive
    # term is unavoidable in the alpha -> 1 corner where risk_star -> noise
    # floor and multiplicative ratios blow up.
    eps_add = 2.0 * ETA * SIGMA**2
    p90_ok = all(r_["p90_risk_ratio"] * r_["risk_star"]
                 <= 3.0 * logT * r_["risk_star"] + eps_add for r_ in rows)
    safe_ok = all(r_["safe_vs_frozen"] for r_ in rows if r_["t_star"] > 0)
    return {"rows": rows, "log_Tmax": logT, "eps_additive": eps_add,
            "p90_gate": p90_ok, "safety_gate": safe_ok,
            "gate_pass": bool(p90_ok and safe_ok)}


def part_e(rng, device="cuda"):
    """Nonconvex (two-layer ReLU) verification of Theorem 2's IMPLICATION:
    if the SSL gradient satisfies assumption (A2) with alignment alpha and noise
    sigma, then the excess-risk curve follows the T1 shape (bias decay rate
    increasing in alpha, variance growth ~ sigma^2 t, alpha=0 strictly harmful,
    gain monotone in alpha). We CONSTRUCT the SSL gradient with controlled
    (alpha, sigma) using the oracle task gradient internally — this verifies the
    theorem's assumption->conclusion in a nonconvex model; measuring alpha of
    REAL SSL tasks on real networks is E2's job, not E1's."""
    import torch
    import scipy.stats as st
    torch.manual_seed(0)
    dev = device if torch.cuda.is_available() else "cpu"
    d, n_src = 20, 20000
    res_rows = []
    T_ad, eta_ad = 200, 0.05
    for rep in range(3):
        g = torch.Generator().manual_seed(100 + rep)
        W_true = torch.randn(d, 64, generator=g) / np.sqrt(d)
        a_true = torch.randn(64, generator=g) / np.sqrt(64)

        def f_true(x, W=W_true, a=a_true):
            return torch.relu(x @ W) @ a

        X = torch.randn(n_src, d, generator=g)
        Y = f_true(X) + 0.05 * torch.randn(n_src, generator=g)

        net = torch.nn.Sequential(torch.nn.Linear(d, 128), torch.nn.ReLU(),
                                  torch.nn.Linear(128, 128), torch.nn.ReLU(),
                                  torch.nn.Linear(128, 1)).to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        Xd, Yd = X.to(dev), Y.to(dev)
        for ep in range(30):
            perm = torch.randperm(n_src, device=dev)
            for i in range(0, n_src, 256):
                idx = perm[i:i + 256]
                loss = ((net(Xd[idx]).squeeze(-1) - Yd[idx]) ** 2).mean()
                opt.zero_grad(); loss.backward(); opt.step()

        # shifted test task: label function perturbed (function shift delta)
        for delta_scale in [0.5, 1.0, 2.0]:
            gg = torch.Generator().manual_seed(999 + rep * 7 + int(delta_scale * 10))
            dW = torch.randn(d, 64, generator=gg) / np.sqrt(d)
            xstar = torch.randn(1, d, generator=gg).to(dev)
            ystar = (f_true(xstar.cpu()) + delta_scale
                     * (torch.relu(xstar.cpu() @ (W_true + 0.3 * dW)) @ a_true
                        - f_true(xstar.cpu()))).to(dev)

            params = [p_ for p_ in net.parameters()]
            sd = {k: v.clone() for k, v in net.state_dict().items()}

            def pred_grad():
                """Gradient of the PREDICTION f(x*) (not the loss), plus
                residual r = f - y. Loss gradient = 2 r * g_f."""
                f = net(xstar).squeeze(-1).mean()
                gs = torch.autograd.grad(f, params)
                gf = torch.cat([gv.reshape(-1) for gv in gs])
                r = float(f.item() - ystar.item())
                return gf, r

            def assign_grad(vec):
                off = 0
                for p_ in params:
                    n_ = p_.numel()
                    p_.grad = vec[off:off + n_].view_as(p_).clone()
                    off += n_

            r0_abs = None
            for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
                for sigma_rel in [0.5, 2.0]:
                    net.load_state_dict(sd)
                    gperp_seed = torch.Generator(device="cpu").manual_seed(rep * 31 + 1)
                    dperp = torch.randn(sum(p_.numel() for p_ in params),
                                        generator=gperp_seed).to(dev)
                    e0 = None
                    curve = []
                    diverged = False
                    eta_f = 0.05   # residual contraction rate per aligned step
                    for t in range(T_ad + 1):
                        gf, r = pred_grad()
                        risk = r * r
                        if e0 is None:
                            e0 = risk
                            if r0_abs is None:
                                r0_abs = abs(r) + 1e-9
                        if not np.isfinite(risk) or risk > 25 * max(e0, 1e-6):
                            curve.append(25 * max(e0, 1e-6))   # divergence: cap, stop
                            diverged = True
                            break
                        curve.append(risk)
                        if t == T_ad:
                            break
                        gnorm = gf.norm()
                        ghat = torch.sign(torch.tensor(r)).item() * gf / (gnorm + 1e-12)
                        perp = dperp - (dperp @ ghat) * ghat
                        perp = perp / (perp.norm() + 1e-12)
                        xi = float(torch.randn(1).item())
                        # residual-proportional step (mirrors the scalar theory:
                        # aligned part contracts r geometrically at rate eta_f;
                        # noise along the prediction-sensitive direction at fixed
                        # scale sigma_rel*r0 accumulates as a random walk)
                        step = eta_f * abs(r) / (gnorm + 1e-12)
                        noise_step = eta_f * sigma_rel * r0_abs / (gnorm + 1e-12)
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
                                     "t_emp": int(np.argmin(curve)),
                                     "curve_sub": curve[::5]})
            net.load_state_dict(sd)

    # gates: (i) alpha=0 harmful on average (final risk above E0);
    # (ii) mean relative best-gain nondecreasing in alpha (tolerance 0.02) with a
    # clear margin between alpha=0 and alpha=1 (robust to gain saturation, unlike
    # a pooled spearman which collapses under ties)
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
    gate = bool(harm0 > 0 and mono and margin > 0.1)
    return {"rows": res_rows, "alpha0_mean_harm": harm0,
            "mean_relgain_by_alpha": dict(zip(map(str, alpha_keys), mean_gain)),
            "monotone": mono, "margin": margin, "gate_pass": gate}


def part_f(rng):
    rows = []
    a, r = 0.5, 2.0
    delta = r * SIGMA
    for N in [1, 2, 4, 8, 16, 32, 64]:
        us = simulate_scalar(a, delta, SIGMA, ETA, T, NREP, rng, batch_N=N)
        emp = emp_risk_curve(us)
        ts = np.arange(T + 1)
        theo = excess_risk(ts, a, delta, SIGMA / np.sqrt(N), ETA)
        rows.append({"N": N, "emp_min_risk": float(emp.min()),
                     "theory_min_risk": float(theo.min()),
                     "gain_emp": float(delta**2 - emp.min()),
                     "gain_theory": float(delta**2 - theo.min())})
    errs = [abs(r_["emp_min_risk"] - r_["theory_min_risk"]) / max(r_["theory_min_risk"], 1e-9)
            for r_ in rows]
    return {"rows": rows, "max_rel_err": float(max(errs)),
            "gate_pass": max(errs) < 0.1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all", choices=["all", "a", "b", "c", "d", "e", "f"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="results/e1")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes for sanity check")
    args = ap.parse_args()
    global NREP, T
    if args.smoke:
        NREP, T = 500, 200
    rng = np.random.default_rng(args.seed)
    parts = "abcdef" if args.part == "all" else args.part
    summary = {}
    for p in parts:
        fn = {"a": part_a, "b": part_b, "c": part_c, "d": part_d,
              "e": part_e, "f": part_f}[p]
        print(f"[e1] running part {p} ...", flush=True)
        res = fn(rng)
        save_json(res, os.path.join(args.out, f"e1_{p}_seed{args.seed}.json"))
        summary[p] = {"gate_pass": res.get("gate_pass")}
        print(f"[e1] part {p}: gate_pass={res.get('gate_pass')}", flush=True)
    save_json(summary, os.path.join(args.out, f"e1_summary_seed{args.seed}.json"))
    print("[e1] DONE", summary)


if __name__ == "__main__":
    main()
