#!/usr/bin/env python
"""Generate tiny SYNTHETIC fixture result files for testing aggregate.py.

THESE ARE NOT EXPERIMENT RESULTS. All numbers are fabricated by a seeded RNG
purely to exercise the aggregator's schema handling. They live ONLY under
analysis/fixtures/results/ and must never be copied near real result paths.

Usage:  python make_fixtures.py [--root <dir>]   (default: ./results)
"""
import argparse
import json
import math
import os

import numpy as np

rng = np.random.default_rng(7)


def save(obj, *parts):
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1)
    print("wrote", path)


def meta(**argv):
    return {"argv": argv, "time": "1970-01-01T00:00:00",
            "torch": "fixture", "cuda": "fixture"}


# ---------------- m0 ----------------

def make_m0(root):
    for ds, arch, acc, rot in [("cifar10", "resnet26ttt", 0.935, 0.91),
                               ("cifar10", "wrn2810", 0.955, None)]:
        hist = [{"epoch": e, "test_acc": acc - 0.01 * (3 - i),
                 "rot_acc": (rot - 0.01 * (3 - i)) if rot else None,
                 "minutes": 10.0 * (i + 1)}
                for i, e in enumerate([10, 20, 30])]
        hist[-1]["test_acc"] = acc
        if rot:
            hist[-1]["rot_acc"] = rot
        save({"meta": meta(dataset=ds, arch=arch, seed=0),
              "history": hist, "final": hist[-1],
              "acc_gate": True, "rot_gate": True, "gate_pass": True},
             root, "m0", f"{ds}_{arch}_s0.json")


# ---------------- e1 ----------------

ETA, SIGMA, T = 0.05, 1.0, 40


def mean_u(t, a, d):
    return d * (1 - a**2) + d * a**2 * (1 - ETA) ** t


def var_u(t, a, s):
    return (a**2 * s**2 * ETA * (1 - (1 - ETA) ** (2 * t)) / (2 - ETA)
            + (1 - a**2) * s**2 * ETA**2 * t)


def risk(t, a, d, s):
    return mean_u(t, a, d) ** 2 + var_u(t, a, s)


def make_e1(root):
    alphas = [0.0, 0.25, 0.5, 1.0]
    ratios = [0.5, 2.0, 8.0]
    # part a
    grid, worst = [], 0.0
    for a in alphas:
        for r in ratios:
            d = r * SIGMA
            theo = [risk(t, a, d, SIGMA) for t in range(T + 1)]
            emp = [v * (1 + float(rng.normal(0, 0.01))) for v in theo]
            rel = max(abs(e - v) for e, v in zip(emp, theo)) / max(max(theo), 1e-12)
            worst = max(worst, rel)
            grid.append({"alpha": a, "delta": d, "sigma": SIGMA,
                         "emp": emp, "theory": theo, "max_rel_err": rel})
    save({"eta": ETA, "T": T, "n_rep": 100, "grid": grid,
          "worst_rel_err": worst, "gate_pass": worst < 0.05},
         root, "e1", "e1_a_seed42.json")
    # part b
    aa = np.linspace(0.05, 1.0, 8)
    rr = np.logspace(-1, 1.2, 8)
    gain = [[float(d := r * SIGMA) and float(
        d**2 - min(risk(t, a, d, SIGMA) for t in range(T + 1)))
        for r in rr] for a in aa]
    phase = [[float((a * r) ** 2) for r in rr] for a in aa]
    save({"alphas": aa.tolist(), "ratios": rr.tolist(),
          "gain": gain, "phase_stat": phase,
          "fit_accuracy": 0.97, "fitted_threshold": 0.028,
          "holdout_accuracy": 0.96, "gate_pass": True},
         root, "e1", "e1_b_seed42.json")
    # part c
    rows, ok = [], 0
    for a in alphas[1:]:
        for r in ratios:
            d = r * SIGMA
            risks = [risk(t, a, d, SIGMA) for t in range(T + 1)]
            ts = int(np.argmin(risks))
            te = max(0, ts + int(rng.integers(-1, 2)))
            rae = risks[min(te, T)]
            rel = abs(rae - risks[ts]) / max(risks[ts], 1e-12)
            ok += int(rel <= 0.05)
            rows.append({"alpha": a, "delta": d, "t_theory": ts, "t_emp": te,
                         "risk_star": risks[ts], "risk_at_t_emp": rae,
                         "risk_rel_gap": rel})
    save({"rows": rows, "frac_risk_within_5pct": ok / len(rows),
          "frac_time_within_2x": 1.0, "gate_pass": ok / len(rows) >= 0.9},
         root, "e1", "e1_c_seed42.json")
    # part d
    rows = []
    for a in [0.25, 0.5, 1.0]:
        for r in [1.0, 4.0]:
            d = r * SIGMA
            risks = [risk(t, a, d, SIGMA) for t in range(T + 1)]
            ts = int(np.argmin(risks))
            rows.append({"alpha": a, "delta": d, "t_star": ts,
                         "risk_star": risks[ts],
                         "median_t_hat": float(ts + 1),
                         "mean_realized_risk": risks[ts] * 1.4,
                         "median_risk_ratio": 1.3, "p90_risk_ratio": 2.1,
                         "frac_worse_than_frozen": 0.05,
                         "safe_vs_frozen": True})
    save({"rows": rows, "log_Tmax": math.log(T), "eps_additive": 0.1,
          "p90_gate": True, "safety_gate": True, "gate_pass": True},
         root, "e1", "e1_d_seed42.json")
    # part e
    rows = []
    base = {0.0: -0.05, 0.25: 0.1, 0.5: 0.3, 0.75: 0.5, 1.0: 0.7}
    for rep in range(2):
        for ds_ in [0.5, 2.0]:
            for a, bg in base.items():
                for sr in [0.5, 2.0]:
                    e0 = ds_**2
                    rows.append({"rep": rep, "delta_scale": ds_, "alpha": a,
                                 "sigma_rel": sr, "E0": e0,
                                 "best_gain": max(bg, 0.0) * e0,
                                 "final_risk": e0 * (1.2 if a == 0 else 0.8),
                                 "diverged": False, "t_emp": 5,
                                 "curve_sub": [e0, e0 * 0.9, e0 * 0.85]})
    save({"rows": rows, "alpha0_mean_harm": 0.3,
          "mean_relgain_by_alpha": {str(k): max(v, 0.0)
                                    for k, v in base.items()},
          "monotone": True, "margin": 0.7, "gate_pass": True},
         root, "e1", "e1_e_seed42.json")
    # part f
    rows = []
    a, d = 0.5, 2.0
    for N in [1, 2, 4, 8, 16, 32, 64]:
        s = SIGMA / math.sqrt(N)
        theo = min(risk(t, a, d, s) for t in range(T + 1))
        emp = theo * (1 + float(rng.normal(0, 0.02)))
        rows.append({"N": N, "emp_min_risk": emp, "theory_min_risk": theo,
                     "gain_emp": d**2 - emp, "gain_theory": d**2 - theo})
    err = max(abs(r["emp_min_risk"] - r["theory_min_risk"])
              / max(r["theory_min_risk"], 1e-9) for r in rows)
    save({"rows": rows, "max_rel_err": err, "gate_pass": err < 0.1},
         root, "e1", "e1_f_seed42.json")
    save({p: {"gate_pass": True} for p in "abcdef"},
         root, "e1", "e1_summary_seed42.json")


# ---------------- e2 ----------------

CORRS = ["gaussian_noise", "fog"]
STEPS = [1, 2, 5, 10, 20]


def e2_episode(method, alpha, sigma2, delta, stochastic):
    frozen_loss = 1.0 + delta
    eps = {"idx": int(rng.integers(0, 10000)),
           "alpha": alpha, "sigma2_rel": sigma2 if stochastic else 0.0,
           "sigma2_batch_rel": sigma2 if stochastic else 0.0,
           "gnorm_ssl": 0.5, "gnorm_task": 1.0,
           "frozen_loss": frozen_loss,
           "confidence": float(np.clip(rng.uniform(0.3, 0.99), 0, 1)),
           "frozen_correct": int(rng.random() < 0.6),
           "delta_proxy": delta}
    ph = alpha**2 * delta / max(sigma2, 1e-3)
    gain_scale = 0.1 * math.tanh(ph - 0.5) + float(rng.normal(0, 0.01))
    steps = {}
    for t in STEPS:
        g = gain_scale * (1 - math.exp(-t / 5.0))
        steps[str(t)] = {"loss": frozen_loss - g,
                         "correct": int(rng.random() < 0.6 + max(g, 0))}
    eps["steps"] = steps
    eps["alta"] = ({"t_hat": int(rng.integers(0, 20)),
                    "loss": frozen_loss - max(gain_scale, 0.0) * 0.9,
                    "correct": int(rng.random() < 0.65)}
                   if stochastic else None)
    return eps


def make_e2(root):
    # E5 feature-shift records collected alongside episodes (delta_feat is a
    # property of (image, source model); joined by corr/sev/idx per arch)
    feat_records = {}
    arch_of = {"ttt_mask": "resnet26ttt", "ttt_rot": "resnet26ttt",
               "tent": "wrn2810"}
    for method, stoch in [("ttt_mask", True), ("ttt_rot", True),
                          ("tent", False)]:
        cells = []
        for corr in CORRS:
            for sev in [3, 5]:
                base_a = {"gaussian_noise": 0.55, "fog": 0.35}[corr]
                alpha = base_a + 0.02 * sev
                delta = 0.4 * sev * (1.2 if corr == "gaussian_noise" else 0.8)
                eps = []
                for _ in range(12):
                    d = float(delta + rng.normal(0, 0.1))
                    ep = e2_episode(
                        method,
                        float(np.clip(alpha + rng.normal(0, 0.05), -1, 1)),
                        float(abs(rng.normal(0.5, 0.1))), d, stoch)
                    eps.append(ep)
                    feat_records.setdefault(arch_of[method], []).append(
                        {"corruption": corr, "severity": sev,
                         "idx": ep["idx"],
                         "delta_feat": float(max(
                             0.05 + 0.3 * d + rng.normal(0, 0.02), 0.01))})
                cells.append({"corruption": corr, "severity": sev,
                              "episodes": eps})
        save({"meta": meta(dataset="cifar10", method=method, seed=0,
                           mode="main", episodes=12, steps=20,
                           bn_mode="eval"),
              "clean_ref_loss": 0.25, "results": cells},
             root, "e2", f"cifar10_{method}_main_s0.json")
    for arch in sorted(feat_records):
        save({"dataset": "cifar10", "arch": arch,
              "ref": "clean_feature_mean", "model_seed": 0,
              "records": feat_records[arch]},
             root, "e5", f"delta_feat_cifar10_{arch}.json")
    make_e2_batch(root, with_steps=True)
    make_e2_calib(root, with_steps=True)


def make_e2_batch(root, with_steps):
    """Batch sweep (tent), both bn modes.

    with_steps=True -> NEW schema (per-step "steps" stats); False -> OLD
    schema (final adapted_loss/acc only), kept to test the fallback path.
    Noise design: sigma2_point_abs = sigma2_batch_rel*gnorm^2*N ~ const 0.8;
    N=1 is deterministic (sigma^2=0).
    bn-train (PRIMARY, published-Tent protocol): N=1 gain trajectory is
    nonpositive and degrading; N>=2 step-1 gain grows with N (recovery).
    bn-eval mirrors the real-data documented negative: Tent in eval-BN mode
    does not gain at any N on clean-calibrated CIFAR models (secondary
    finding; must NOT fail the C3 gate).
    """
    gnorm = 0.5
    s2_point_abs = 0.8
    for bn, suffix in [("eval", ""), ("train", "_bntrain")]:
        cells = []
        for corr in CORRS:
            for N in [1, 2, 4, 8, 16, 32, 64]:
                batches = []
                for b in range(8):
                    fa = 0.45

                    def gain_t(t):
                        if bn == "eval":  # documented negative: never gains
                            return -0.002 - 0.0015 * t
                        if N == 1:  # collapse: nonpositive, degrading
                            return -0.005 - 0.004 * t
                        return (0.05 * (1 - 1.0 / N)
                                * (1 - math.exp(-t / 4.0))
                                - 0.001 * max(t - 10, 0) + 0.01)

                    # bn-train: BatchNorm couples per-sample gradients, so
                    # the measured point_abs is inflated at small N (real
                    # data: ratio ~12) -- the sigma^2 gates must come from
                    # bn-eval, where per-sample gradients are independent
                    pa = s2_point_abs * (12.0 if (bn == "train" and N == 2)
                                         else 1.0)
                    s2b_rel = (0.0 if N == 1 else
                               float(pa / (N * gnorm**2)
                                     * abs(rng.normal(1.0, 0.1))))
                    g_fin = gain_t(20) + float(rng.normal(0, 0.005))
                    rec = {
                        "alpha": float(np.clip(rng.normal(0.3, 0.1), -1, 1)),
                        "sigma2_rel": s2b_rel * N,
                        "sigma2_batch_rel": s2b_rel,
                        "gnorm_ssl": gnorm, "gnorm_task": 1.0,
                        "frozen_loss": 2.0, "frozen_acc": fa,
                        "adapted_loss": 2.0 - g_fin,
                        "adapted_acc": float(np.clip(fa + g_fin, 0, 1))}
                    if with_steps:
                        rec["steps"] = {
                            str(t): {"loss": 2.0 - gain_t(t),
                                     "acc": float(np.clip(
                                         fa + gain_t(t)
                                         + rng.normal(0, 0.003), 0, 1))}
                            for t in STEPS}
                    batches.append(rec)
                cells.append({"corruption": corr, "severity": 5, "N": N,
                              "batches": batches})
        save({"meta": meta(dataset="cifar10", method="tent", seed=0,
                           mode="batch_sweep", bn_mode=bn),
              "clean_ref_loss": 0.25, "results": cells},
             root, "e2", f"cifar10_tent_batch_sweep_s0{suffix}.json")


def make_e2_calib(root, with_steps):
    """Calib mode. with_steps=True adds per-step {loss, correct} (new schema):
    temp scaling helps at steps 1-2 (higher alpha_ent); the 20-step endpoint
    is in the collapse regime for the uncalibrated model."""
    cal_cells = []
    for temp in [False, True]:
        for corr in CORRS:
            eps = []
            for _ in range(40):
                conf = float(rng.uniform(0.2, 0.999))
                correct = int(rng.random() < conf * 0.8)
                # overconfident-wrong -> alpha_ent < 0; temp scaling helps
                mu = 0.3 if (correct or conf < 0.7) else -0.25
                if temp:
                    mu += 0.15
                a_ent = float(rng.normal(mu, 0.1))
                fl = float(abs(rng.normal(1.5, 0.3)))

                def loss_t(t):
                    late = 0.05 * max(t - 5, 0) / 15.0 * (0.7 if temp else 1.0)
                    return fl - 0.1 * a_ent * (1 - math.exp(-t / 2.0)) + late

                rec = {"alpha_ent": a_ent, "confidence": conf,
                       "correct": correct, "frozen_loss": fl,
                       "adapted_loss": loss_t(20),
                       "adapted_correct": int(rng.random()
                                              < conf * 0.8 + 0.05)}
                if with_steps:
                    rec["steps"] = {
                        str(t): {"loss": loss_t(t),
                                 "correct": int(rng.random() < min(max(
                                     conf * 0.8 + 0.1 * a_ent, 0.0), 1.0))}
                        for t in STEPS}
                eps.append(rec)
            cal_cells.append({"corruption": corr, "temp_scaled": temp,
                              "episodes": eps})
    save({"meta": meta(dataset="cifar10", method="tent", seed=0, mode="calib"),
          "clean_ref_loss": 0.25,
          "results": {"temperature": 1.8, "cells": cal_cells}},
         root, "e2", "cifar10_tent_calib_s0.json")


# ---------------- e3 ----------------

def make_e3(root):
    steps = 10
    for corr in CORRS:
        for method in ["tent"]:
            for stopping in ["fixed", "alta", "oracle"]:
                cells = []
                for sev in [3, 5]:
                    frozen = 0.30 - 0.03 * sev
                    bn0 = frozen + 0.10
                    curve = [bn0 + 0.05 * (1 - math.exp(-t / 3.0))
                             - 0.004 * t for t in range(steps + 1)]
                    best_t = int(np.argmax(curve))
                    if stopping == "fixed":
                        t_sel, adapted = steps, curve[steps]
                    elif stopping == "oracle":
                        t_sel, adapted = best_t, curve[best_t]
                    else:
                        t_sel = max(0, best_t - 1)
                        adapted = curve[t_sel] - 0.001
                    n_b, bsz = 6, 64
                    batches = []
                    for b in range(n_b):
                        rec = {"batch": b,
                               "frozen_correct": int(frozen * bsz),
                               "t_hat": t_sel,
                               "bn0_correct": int(bn0 * bsz),
                               "adapted_correct": int(adapted * bsz),
                               "acc_by_step": [int(c * bsz) for c in curve],
                               "n": bsz}
                        if stopping in ("fixed", "oracle"):
                            rec["loss_by_step"] = [2.5 - c for c in curve]
                        else:
                            rec["dispersion"] = [0.0] + [0.1 * t for t in
                                                         range(1, steps + 1)]
                            # post-safety-fix semantics: ALTA's t=0 candidate
                            # is the TRUE eval-BN frozen prediction
                            rec["alta_t0_is_frozen"] = True
                        batches.append(rec)
                    align = [{"batch": b, "alpha": 0.4, "sigma2_rel": 0.02,
                              "sigma2_batch_rel": 0.02 / 64,
                              "gnorm_ssl": 0.5, "gnorm_task": 1.0,
                              "frozen_loss": 2.2} for b in range(3)]
                    hist = [0] * (steps + 1)
                    hist[t_sel] = n_b
                    cells.append({
                        "corruption": corr, "severity": sev,
                        "n_batches": n_b, "n_images": n_b * bsz,
                        "alignment": align, "batches": batches,
                        "frozen_acc": frozen, "bn0_acc": bn0,
                        "adapted_acc": adapted,
                        "mean_t_hat": float(t_sel), "t_hat_hist": hist,
                        "acc_by_step": curve,
                        "frozen_loss_mean": 2.2, "delta_proxy": 1.3})
                save({"meta": meta(corruption=corr, severities="3,5",
                                   method=method, stopping=stopping,
                                   steps=steps, seed=0),
                      "clean_ref_loss": 0.9, "results": cells},
                     root, "e3", f"{corr}_{method}_{stopping}_s0.json")

    # STALE-semantics alta file (pre-safety-fix: no alta_t0_is_frozen flag),
    # same key as the flagged gaussian_noise/tent/alta run above, with a
    # deliberate safety violation (adapted << frozen). The aggregator must
    # DROP these cells in favor of the flagged ones -- if the preference
    # logic breaks, a spurious C5 safety violation appears.
    stale_cells = []
    for sev in [3, 5]:
        frozen = 0.30 - 0.03 * sev
        bad = frozen - 0.05     # would violate the 0.2pt safety margin
        n_b, bsz = 6, 64
        batches = [{"batch": b, "frozen_correct": int(frozen * bsz),
                    "t_hat": steps, "bn0_correct": int((frozen + 0.10) * bsz),
                    "adapted_correct": int(bad * bsz),
                    "acc_by_step": [int(bad * bsz)] * (steps + 1),
                    "dispersion": [0.1 * t for t in range(steps + 1)],
                    "n": bsz} for b in range(n_b)]
        stale_cells.append({
            "corruption": "gaussian_noise", "severity": sev,
            "n_batches": n_b, "n_images": n_b * bsz,
            "alignment": [{"batch": 0, "alpha": 0.4, "sigma2_rel": 0.02,
                           "sigma2_batch_rel": 0.02 / 64, "gnorm_ssl": 0.5,
                           "gnorm_task": 1.0, "frozen_loss": 2.2}],
            "batches": batches,
            "frozen_acc": frozen, "bn0_acc": frozen + 0.10,
            "adapted_acc": bad, "mean_t_hat": float(steps),
            "t_hat_hist": [0] * steps + [n_b],
            "acc_by_step": [bad] * (steps + 1),
            "frozen_loss_mean": 2.2, "delta_proxy": 1.3})
    save({"meta": meta(corruption="gaussian_noise", severities="3,5",
                       method="tent", stopping="alta", steps=steps, seed=1),
          "clean_ref_loss": 0.9, "results": stale_cells},
         root, "e3", "gaussian_noise_tent_alta_s1.json")


# ---------------- e4 ----------------

def make_e4(root):
    """Mirror the real-data structure: intrinsic domain entropy differs
    wildly (code frozen ppl ~6.6 << wikitext ~23) while adaptation gains are
    LARGEST on code -> the cross-domain delta_proxy is confounded (kept only
    as the aggregator's diagnostic path). WITHIN each domain, the centered
    delta correlates positively with per-doc gain (C6 primary test), and
    mean ppl improvement is positive in ALL domains with ALTA within 15%
    relative of the best fixed step."""
    steps = 20
    rec_steps = [1, 2, 5, 10, 20]
    ref_mean = 3.15  # wikitext frozen mean (ppl ~23)
    save({"mean_frozen_cont_ce": ref_mean, "n_docs": 20, "seed": 0},
         root, "e4", "wikitext_ref_s0.json")
    # (base frozen ce, base alpha, base gain in nats, base delta_v2 distance)
    doms = {"wikitext": (3.15, 0.35, 0.04, 0.20),
            "pubmed": (3.60, 0.45, 0.12, 0.35),
            "code": (1.90, 0.60, 0.30, 0.60),
            "legal": (3.80, 0.40, 0.10, 0.30)}
    for dom, (base_ce, base_a, base_g, base_v2) in doms.items():
        records = []
        e5_records = []
        for i in range(20):
            alpha = float(np.clip(base_a + rng.normal(0, 0.08), -1, 1))
            sigma2 = float(abs(rng.normal(0.6, 0.1)))
            d_cent = float(rng.normal(0, 0.4))   # within-domain shift
            frozen = base_ce + d_cent
            # E5 hidden-state shift proxy: direct distance to the wikitext
            # ref, monotone in the within-domain shift (no centering needed)
            e5_records.append({"doc": i, "delta_v2": float(max(
                base_v2 + 0.3 * d_cent + rng.normal(0, 0.01), 0.005))})
            # per-doc gain rises with the delta_v2 phase statistic (mirrors
            # the real-data finding: representation-space shift predicts
            # gain); always positive (adaptation helps everywhere)
            ph_v2 = alpha**2 * e5_records[-1]["delta_v2"] / sigma2
            g = base_g * (0.4 + 1.2 * math.tanh(ph_v2)) \
                + float(rng.normal(0, 0.005))
            curve = [frozen - g * (1 - math.exp(-t / 6.0))
                     for t in range(steps + 1)]
            rep_ce = [[c + float(rng.normal(0, 0.003))
                       for c in curve[1:]] for _ in range(3)]
            mean_ce = np.mean(rep_ce, axis=0)
            full = np.concatenate([[frozen], mean_ce])
            t_star = int(np.argmin(full))
            t_hat = int(rng.integers(10, 15))    # near-best stop (<=15% gap)
            records.append({
                "doc": i, "alpha": alpha, "sigma2_rel": sigma2,
                "gnorm_ssl": 0.4, "gnorm_task": 1.0,
                "frozen_cont_ce": frozen,
                "delta_proxy": (frozen - ref_mean if dom == "wikitext"
                                else None),
                "cont_ce": [[float(c) for c in r] for r in rep_ce],
                "fixed": {str(t): float(full[t]) for t in rec_steps},
                "oracle": {"t_star": t_star, "cont_ce": float(full[t_star])},
                "alta": {"t_hat": t_hat, "cont_ce": float(full[t_hat]),
                         "dispersion": [0.01 * t for t in range(steps + 1)]}})
        save({"meta": meta(domain=dom, seed=0, n_docs=20, steps=steps,
                           adapt_params="ln", stopping="all"),
              "protocol": {"prefix_len": 768, "cont_len": 256,
                           "window": 512, "tail": 32},
              "wikitext_ref_mean": ref_mean if dom == "wikitext" else None,
              "records": records},
             root, "e4", f"{dom}_ln_s0.json")
        save({"domain": dom, "layer": 6, "ref": "wikitext_mean_layer6",
              "records": e5_records},
             root, "e5", f"delta_v2_{dom}.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root",
                    default=os.path.join(os.path.dirname(__file__), "results"))
    ap.add_argument("--old-root",
                    default=os.path.join(os.path.dirname(__file__),
                                         "results_oldschema"),
                    help="root for OLD-schema e2 batch/calib files "
                         "(no per-step stats; tests the fallback path)")
    args = ap.parse_args()
    make_m0(args.root)
    make_e1(args.root)
    make_e2(args.root)
    make_e3(args.root)
    make_e4(args.root)
    print("fixtures done under", args.root)
    # old-schema variants (pre per-step "steps" key) for the fallback path
    make_e2_batch(args.old_root, with_steps=False)
    make_e2_calib(args.old_root, with_steps=False)
    print("old-schema fixtures done under", args.old_root)


if __name__ == "__main__":
    main()
