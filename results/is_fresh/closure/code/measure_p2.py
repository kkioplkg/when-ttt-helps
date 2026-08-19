"""P2 -- Tier-2 measurement of (A2) persistence and of Assumption 5.4's
logit-Jacobian conditioning, along real single-instance adaptation trajectories.

DESIGN v2.  Three things this script is careful about, each because the first
review found the v1 version of it wrong:

1.  THE RECURSION IS PLAIN SGD, NO MOMENTUM.  Supplement S2 assumes
    theta_{t+1} = theta_t - eta g(theta_t, xi_t).  A momentum trajectory has
    state (theta_t, v_t) and is simply not the trajectory A4 constrains, so it
    cannot carry an envelope claim.  The manuscript's momentum-0.9 protocol is
    available behind --momentum as a T3 "practice trajectory" and is excluded
    from every A2/envelope statement.

2.  gbar FOR THE ROTATION OBJECTIVE IS EXACT, NOT MONTE CARLO.  A2 is about
    gbar(theta) = E_xi g(theta, xi).  The manuscript's rotation objective draws
    four independent uniform rotation indices and averages, so by linearity
        gbar(theta) = (1/4) sum_{k=0}^{3} grad CE(f_ssl(rot_k x), k)
    exactly, in four backward passes.  With gbar exact, <gbar, grad R> <= 0 is
    a fact about the network rather than a Monte-Carlo event, and the
    falsification claim needs no confidence bound.

3.  THE TARGET LAW IS DECLARED.  grad R is the gradient of the conditional
    expected cross-entropy under the declared deterministic target
    distribution Q_0 (DESIGN v2 s0), not "the loss at the observed label".

A2 falsification criterion, stated on the inner product rather than on a
cosine that the vanishing-gradient convention would set to 0:

    ||gbar_t|| > 0  and  ||grad R_t|| > 0  and  <gbar_t, grad R_t> <= 0.

Theta_loc is taken to be the closed ball around theta_0 containing the realized
trajectory, whose radius is recorded per episode.  A4 then holds by
construction for that region, so the falsification is unconditional on that
ball rather than conditional on an unverified containment assumption.

Assumption 5.4's mu_J is the LITERAL Loewner constant of J J^T >= mu^2 Pi,
computed by Schur complement -- not the minimum of the quadratic form
restricted to the 2-D span, which is >= the literal value and would report
kappa_J too small (i.e. flatter Proposition 5.5 than the truth).
"""
import argparse
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

_HERE = os.path.dirname(os.path.abspath(__file__))
_TTT = os.path.dirname(_HERE)
for _p in (_HERE, _TTT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common import (RecordWriter, heartbeat, rel, run_meta, save_json,  # noqa: E402
                    set_seed, shift_cells, _normalize, load_cifar10_np)
from e2_cifar.models import ResNet26TTT  # noqa: E402
from measure_p1 import flat_grad_of  # noqa: E402
from models import subset_params  # noqa: E402

JACOBIAN_STEPS = [0, 1, 5, 10, 20]     # preregistered; not every step
OBJ_SUBSET = {"tent": "norm", "ttt_rot": "encoder"}


# ----------------------------------------------------------------- objectives

def entropy_loss(model, x, seed=None):
    """Tent's objective: mean prediction entropy.  Deterministic, so gbar = g."""
    logits = model(x)
    logp = F.log_softmax(logits, dim=1)
    return -(logp.exp() * logp).sum(1).mean()


def rotation_loss_stochastic(model, x, seed):
    """The manuscript's rotation objective: four independently drawn rotations
    of the instance, averaged.  This is g(theta, xi) -- the STEP direction."""
    g = torch.Generator(device="cpu").manual_seed(int(seed))
    ks = torch.randint(0, 4, (4 * x.size(0),), generator=g)
    xs, ys = [], []
    for j, k in enumerate(ks.tolist()):
        xs.append(torch.rot90(x[j % x.size(0)], k, dims=(1, 2)))
        ys.append(k)
    xr = torch.stack(xs)
    yr = torch.tensor(ys, dtype=torch.long, device=x.device)
    return F.cross_entropy(model.forward_ssl(xr), yr)


def rotation_gbar(model, params, x):
    """EXACT E_xi of the rotation gradient: the mean over the four rotations."""
    acc = None
    for k in range(4):
        xr = torch.rot90(x, k, dims=(2, 3))
        yr = torch.tensor([k], dtype=torch.long, device=x.device)
        loss = F.cross_entropy(model.forward_ssl(xr), yr)
        g = flat_grad_of(loss, params)
        acc = g if acc is None else acc + g
    return acc / 4.0


# ------------------------------------------------------- Jacobian conditioning

def logit_jacobian_gram(model, params, x, K):
    """A = J J^T in R^{K x K}, from K backward passes on the logits.

    PRECISION.  This matrix is severely ill-conditioned on a trained network --
    lambda_max/lambda_min was measured at ~1e8 on the first smoke episodes -- and
    mu_J is a lambda_min-like quantity, so forming A from float32 gradients puts
    mu_J (and hence kappa_J, and hence Proposition 5.5's whole certificate) at
    the float32 noise floor: the smoke run returned mu_J = 0 exactly on the
    encoder subset, which is indistinguishable from "rank deficient" without
    more precision.  The trajectory itself stays in float32 -- that is the
    protocol the manuscript runs -- and only this measurement is lifted, by
    syncing a float64 replica of the network at the measurement point.
    """
    rows = [flat_grad_of(model(x)[0][k], params) for k in range(K)]
    G = torch.stack(rows).double()              # (K, d)
    A = (G @ G.T).cpu().numpy()
    return 0.5 * (A + A.T)                      # symmetrize away round-off


class Float64Replica:
    """A float64 copy of the network whose adapted parameters are re-synced from
    the live float32 model on demand.  Used only for the Jacobian/Prop-5.5
    measurement (see the precision note above)."""

    def __init__(self, model, subset, K):
        import copy
        self.model = copy.deepcopy(model).double()
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad_(True)
        self.params, self.names = subset_params(self.model, subset)
        self.K = K

    @torch.no_grad()
    def sync(self, src_params):
        for dst, src in zip(self.params, src_params):
            dst.copy_(src.detach().double())

    def measure(self, x, y_clean, src_params):
        self.sync(src_params)
        x64 = x.double()
        with torch.no_grad():
            p_vec = F.softmax(self.model(x64), dim=1)[0].cpu().numpy()
        q_vec = np.zeros(self.K)
        q_vec[int(y_clean)] = 1.0               # declared Q_0 conditional
        terms = prop55_terms(p_vec, q_vec, self.K)
        A = logit_jacobian_gram(self.model, self.params, x64, self.K)
        jc = jacobian_constants(A, [np.asarray(terms["grad_z_H"]),
                                    np.asarray(terms["p_minus_q"])])
        return terms, jc, A


def jacobian_constants(A, span_vectors, tol=1e-12):
    """L_J, mu_J(literal), mu_J(restricted), kappa_J for Assumption 5.4.

    Assumption 5.4 reads J J^T >= mu_J^2 Pi as a Loewner inequality on ALL of
    R^K, i.e. v^T A v >= mu_J^2 ||Pi v||^2 for every v -- not merely for v in
    the span.  In a basis (U | V) with U spanning S = range(Pi):

        [[A_SS - mu^2 I, A_SR], [A_RS, A_RR]] >= 0
        <=>  A_SS - mu^2 I - A_SR A_RR^+ A_RS >= 0     (Schur complement)

    so mu_J^2(literal) = lambda_min( A_SS - A_SR A_RR^+ A_RS ), which is <=
    lambda_min(A_SS) = mu_J^2(restricted).  Reporting the restricted value as
    mu_J would understate kappa_J and overstate how active Proposition 5.5 is.
    """
    K = A.shape[0]
    M = np.stack(span_vectors, axis=1)                 # (K, r0)
    U, sv, _ = np.linalg.svd(M, full_matrices=False)
    r = int((sv > tol * max(1.0, sv[0])).sum())
    if r == 0:
        return None
    U = U[:, :r]                                        # orthonormal basis of S
    # orthonormal complement
    Q, _ = np.linalg.qr(np.concatenate([U, np.eye(K)], axis=1))
    V = Q[:, r:K]

    A_SS = U.T @ A @ U
    L_J = float(math.sqrt(max(np.linalg.eigvalsh(A)[-1], 0.0)))
    mu2_restricted = float(max(np.linalg.eigvalsh(A_SS)[0], 0.0))
    if V.shape[1] == 0:
        mu2_literal = mu2_restricted
    else:
        A_SR = U.T @ A @ V
        A_RR = V.T @ A @ V
        S = A_SS - A_SR @ np.linalg.pinv(A_RR, rcond=1e-12) @ A_SR.T
        mu2_literal = float(np.linalg.eigvalsh(0.5 * (S + S.T))[0])
    mu2_literal = max(mu2_literal, 0.0)
    mu_lit = math.sqrt(mu2_literal)
    return {"L_J": L_J,
            "mu_J_literal": mu_lit,
            "mu_J_restricted": math.sqrt(mu2_restricted),
            "kappa_J": (L_J / mu_lit) if mu_lit > 0 else None,
            "span_rank": r,
            "sigma_min_full": float(math.sqrt(max(np.linalg.eigvalsh(A)[0], 0.0)))}


# ------------------------------------------------- Proposition 5.5 quantities

def prop55_terms(p, q, K):
    """Definition 5.3 / Proposition 5.5 quantities, exactly as stated.

    phi_k = p_k (log p_k + H(p)) are the components of -grad_z H; yhat is the
    unique argmax of p (a hypothesis, not a convention: ties make mar and
    Lambda_tail undefined and the instance ineligible).
    """
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    H = float(-(p * np.log(np.clip(p, 1e-300, None))).sum())
    phi = p * (np.log(np.clip(p, 1e-300, None)) + H)
    order = np.argsort(p)[::-1]
    yhat = int(order[0])
    unique_top = bool(p[order[0]] > p[order[1]])
    tail = np.delete(phi, yhat)
    mar = float(phi[yhat] - tail.max())
    lam_tail = float(tail.max() - tail.min())
    Lam = float(np.max(p * np.abs(np.log(np.clip(p, 1e-300, None)) + H)))
    PCD = float(np.abs(p - q).sum())
    Delta = float(q[yhat] - p[yhat])
    Z = Delta * mar - lam_tail * (PCD - abs(Delta))
    return {"H": H, "yhat": yhat, "unique_top": unique_top,
            "p_min": float(p.min()), "p_uniform": bool(np.allclose(p, 1.0 / K)),
            "mar": mar, "Lambda_tail": lam_tail, "Lambda": Lam,
            "PCD": PCD, "Delta": Delta, "Z": Z,
            "grad_z_H": (-phi).tolist(), "p_minus_q": (p - q).tolist()}


def prop55_bound(Z, Lam, K, kappa_J):
    """LB = (1/kappa^2) Z / (2 sqrt(K) Lambda) - (kappa^2 - 1), and the largest
    kappa at which LB would still be > 0 (kappa_crit)."""
    if kappa_J is None or Lam <= 0:
        return {"LB": None, "W": None, "kappa_crit": None}
    W = Z / (2.0 * math.sqrt(K) * Lam)
    LB = W / (kappa_J ** 2) - (kappa_J ** 2 - 1.0)
    # LB(u) > 0 with u = kappa^2  <=>  u^2 - u - W < 0  <=>  u < (1+sqrt(1+4W))/2
    if W > 0:
        u_max = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * W))
        kappa_crit = math.sqrt(u_max) if u_max >= 1.0 else None
    else:
        kappa_crit = None            # not certifiable at any kappa >= 1
    return {"LB": float(LB), "W": float(W), "kappa_crit": kappa_crit}


# ----------------------------------------------------------------- trajectory

def run_episode(model, params, x, y_clean, objective, lr, steps, seed, momentum,
                K, jac_steps, replica=None):
    """One episodic adaptation trajectory with per-step A2 quantities."""
    base = [p.detach().clone() for p in params]
    loss_fn = entropy_loss if objective == "tent" else rotation_loss_stochastic
    yt = torch.tensor([int(y_clean)], device=x.device)
    buf = [torch.zeros_like(p) for p in params] if momentum > 0 else None

    per_step, jac = [], {}
    grad_R_prev, theta_prev = None, None
    for t in range(steps + 1):
        # --- measurement at theta_t ---------------------------------------
        # declared target law Q_0: R = conditional expected CE = CE at the
        # declared deterministic conditional
        R = F.cross_entropy(model(x), yt)
        g_R = flat_grad_of(R, params)
        if objective == "tent":
            g_bar = flat_grad_of(loss_fn(model, x), params)
        else:
            g_bar = rotation_gbar(model, params, x)
        nR = float(g_R.norm().item())
        nG = float(g_bar.norm().item())
        inner = float(torch.dot(g_bar, g_R).item())
        theta_now = torch.cat([p.detach().reshape(-1) for p in params])
        disp = float((theta_now - torch.cat([b.reshape(-1) for b in base])).norm().item())
        rec = {"t": t, "R": float(R.item()), "gnorm_bar": nG, "gnorm_R": nR,
               "inner": inner,
               "alpha": (inner / (nG * nR)) if (nG > 0 and nR > 0) else 0.0,
               "rho": (nG / nR) if nR > 0 else None,
               "disp": disp,
               "falsifies_A2": int(nG > 0 and nR > 0 and inner <= 0)}
        if grad_R_prev is not None and theta_prev is not None:
            dth = float((theta_now - theta_prev).norm().item())
            rec["lip_secant"] = (float((g_R - grad_R_prev).norm().item()) / dth
                                 if dth > 0 else None)
        per_step.append(rec)
        grad_R_prev, theta_prev = g_R.clone(), theta_now.clone()

        # --- Jacobian conditioning at the preregistered grid ---------------
        if t in jac_steps and replica is not None:
            terms, jc, A = replica.measure(x, y_clean, params)
            entry = {"t": t, **{k: v for k, v in terms.items()
                                if k not in ("grad_z_H", "p_minus_q")}}
            entry["gram_cond"] = float(np.linalg.cond(A))
            if jc:
                entry.update(jc)
                entry.update(prop55_bound(terms["Z"], terms["Lambda"], K,
                                          jc["kappa_J"]))
                # Definition 5.3's hypotheses, plus Assumption 5.4's mu_J > 0
                entry["eligible_def53"] = int(bool(terms["unique_top"]) and
                                              terms["p_min"] > 0 and
                                              not terms["p_uniform"])
                entry["eligible"] = int(entry["eligible_def53"] and
                                        (jc["mu_J_literal"] or 0) > 0)
            jac[str(t)] = entry

        if t == steps:
            break
        # --- the S2 recursion ---------------------------------------------
        loss = loss_fn(model, x, seed * 10007 + t) if objective != "tent" else loss_fn(model, x)
        grads = torch.autograd.grad(loss, params, allow_unused=True)
        with torch.no_grad():
            for i, (prm, g) in enumerate(zip(params, grads)):
                if g is None:
                    continue
                if buf is not None:
                    buf[i].mul_(momentum).add_(g)
                    prm.sub_(lr * buf[i])
                else:
                    prm.sub_(lr * g)            # plain SGD, exactly S2's update

    with torch.no_grad():
        for prm, b in zip(params, base):
            prm.copy_(b)
    return per_step, jac


def summarize(per_step):
    """Path statistics.  These are NOT A2's region constants: for any Theta_loc
    containing the path, min_t alpha_t >= alpha_*, min_t rho_t >= c_*, and
    max_t rho_t <= C_*.  They are therefore named path statistics throughout."""
    al = [r["alpha"] for r in per_step]
    ro = [r["rho"] for r in per_step if r["rho"] is not None]
    lp = [r["lip_secant"] for r in per_step if r.get("lip_secant") is not None]
    flip = next((r["t"] for r in per_step if r["falsifies_A2"]), None)
    out = {"alpha_path_min": min(al) if al else None,
           "alpha_t0": al[0] if al else None,
           "rho_path_min": min(ro) if ro else None,
           "rho_path_max": max(ro) if ro else None,
           "lip_secant_max": max(lp) if lp else None,
           "T_flip": flip,
           "any_falsifies_A2": int(any(r["falsifies_A2"] for r in per_step)),
           "theta_loc_radius": max(r["disp"] for r in per_step),
           "R_0": per_step[0]["R"], "R_T": per_step[-1]["R"]}
    # trajectory-derived OPTIMISTIC UPPER BOUND on the maximal admissible step
    # cap: alpha_hat >= alpha_*, c_hat >= c_*, C_hat <= C_*, Lhat <= L_*, so the
    # ratio is >= eta_*.  Only eta_practical > eta_hat is informative.
    if (out["alpha_path_min"] is not None and out["rho_path_min"] is not None
            and out["rho_path_max"] not in (None, 0) and out["lip_secant_max"]):
        out["eta_hat_optimistic_upper"] = (
            out["alpha_path_min"] * out["rho_path_min"]
            / (out["lip_secant_max"] * out["rho_path_max"] ** 2))
    else:
        out["eta_hat_optimistic_upper"] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="source model seed")
    ap.add_argument("--objective", required=True, choices=list(OBJ_SUBSET))
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--momentum", type=float, default=0.0,
                    help="0.0 = S2's plain-SGD recursion (primary). "
                         "0.9 reproduces the manuscript's practice protocol and "
                         "is a T3 stress test, excluded from envelope claims.")
    ap.add_argument("--instances", type=int, default=100)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    cells = shift_cells()
    if args.smoke:
        cells, args.instances = cells[:2], 3

    device = "cuda" if torch.cuda.is_available() else "cpu"
    set_seed(args.seed)
    blob = torch.load(os.path.join(args.ckpt_dir,
                                   f"cifar10_resnet26ttt_s{args.seed}.pt"),
                      map_location="cpu", weights_only=False)
    model = ResNet26TTT(10)
    model.load_state_dict(blob["model"])
    model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(True)
    params, _ = subset_params(model, OBJ_SUBSET[args.objective])
    # float64 replica for the Jacobian / Proposition 5.5 measurement only
    replica = Float64Replica(model, OBJ_SUBSET[args.objective], K=10)

    from common import binary_test_ids  # noqa: F401  (kept: shared id helpers)
    _, _, tex, tey = load_cifar10_np(args.data_root)
    ids = np.arange(len(tey))

    tag = (f"p2_{args.objective}_s{args.seed}_lr{args.lr:g}"
           f"_mom{args.momentum:g}")
    rec_path = os.path.join(args.out_dir, f"{tag}.jsonl.gz")
    if os.path.exists(rec_path):
        os.remove(rec_path)
    writer = RecordWriter(rec_path)

    t0, n = time.time(), 0
    for corr, sev in cells:
        if corr == "clean":
            xs = _normalize(tex)
        else:
            from common import corrupted_test_images
            xs = corrupted_test_images(args.data_root, corr, sev, ids)
        xs = torch.from_numpy(xs).to(device)
        rng = np.random.default_rng(np.random.SeedSequence(
            entropy=args.seed, spawn_key=(4241, abs(hash(corr)) % 9973, sev)))
        sel = rng.choice(len(tey), size=min(args.instances, len(tey)), replace=False)
        for j, i in enumerate(sel):
            per_step, jac = run_episode(
                model, params, xs[int(i):int(i) + 1], int(tey[int(i)]),
                args.objective, args.lr, args.steps, seed=int(i) * 31 + j,
                momentum=args.momentum, K=10, jac_steps=set(JACOBIAN_STEPS),
                replica=replica)
            writer.write({"objective": args.objective, "model_seed": args.seed,
                          "subset": OBJ_SUBSET[args.objective], "lr": args.lr,
                          "momentum": args.momentum, "corruption": corr,
                          "severity": sev, "test_id": int(i),
                          "y_clean": int(tey[int(i)]),
                          "steps": per_step, "jacobian": jac,
                          "summary": summarize(per_step)})
            n += 1
        writer.flush()
        print(f"[p2] {tag} {corr} s{sev}: {len(sel)} episodes "
              f"({n} total, {time.time() - t0:.0f}s)", flush=True)
        if args.heartbeat:
            heartbeat(args.heartbeat, {"job": tag, "cell": f"{corr}_{sev}",
                                       "episodes": n,
                                       "elapsed_s": time.time() - t0})
    writer.close()
    save_json({"meta": run_meta(args, {"jacobian_steps": JACOBIAN_STEPS,
                                       "n_episodes": n,
                                       "source_acc": blob.get("test_acc")}),
               "records": rel(rec_path)},
              os.path.join(args.out_dir, f"{tag}_meta.json"))
    print(f"[p2] DONE {tag} {n} episodes in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
