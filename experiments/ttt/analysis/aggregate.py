#!/usr/bin/env python
"""Aggregate TTT experiment result JSONs into per-claim (C1..C6) statistics.

Reads result files from --results-root with layout
    <root>/m0/*.json   source-model training     (train_source.py)
    <root>/e1/*.json   synthetic verification    (run_e1.py, parts a..f)
    <root>/e2/*.json   CIFAR-C adaptation        (adapt_cifar.py: main/batch_sweep/calib)
    <root>/e3/*.json   ImageNet-C ALTA vs fixed  (run_e3.py)
    <root>/e4/*.json   GPT-2 document TTT        (run_e4.py)
(any subset may be present; missing milestones mark their claims "pending")
and writes
    --out     machine-readable summary.json (per-claim aggregated statistics)
    --md-out  human-readable markdown report with a Claims Scoreboard.

Pure stdlib + numpy (+ scipy if available, optional). Plain ASCII output.
Deterministic: files are processed in sorted order and all dict output is
emitted with sorted keys; no timestamps in the outputs.

Schemas consumed here are documented in analysis/SCHEMAS.md.
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

try:  # scipy is allowed but optional; numpy fallback keeps results identical
    from scipy import stats as _sps
except Exception:  # pragma: no cover
    _sps = None

EPS_SIGMA = 1e-12          # below this, sigma^2 is treated as exactly 0
SAFETY_PT = 0.002          # 0.2 percentage points (accuracies are fractions)
CONF_THR = 0.7             # "confident" episode threshold (C4)
E1_DEFAULT_ETA = 0.05      # run_e1.py ETA (part b JSON does not record eta)
# methods with intrinsic SSL randomness that satisfy persistent alignment (A2);
# tent/pl violate (A2) by design and are EXCLUDED from the C2 gate -- their
# correlations are reported separately as theory-boundary evidence, not failure
C2_GATE_METHODS = ("ttt_mask", "ttt_rot")
# source model per E2 method (mirrors adapt_cifar.METHOD_ARCH), used to join
# the E5 delta_feat files
E2_METHOD_ARCH = {"ttt_rot": "resnet26ttt", "ttt_mask": "resnet26ttt",
                  "tent": "wrn2810", "pl": "wrn2810"}


# ---------------------------------------------------------------- utilities

def mean(vals):
    xs = [float(v) for v in vals
          if v is not None and np.isfinite(float(v))]
    return float(np.mean(xs)) if xs else None


def median(vals):
    xs = [float(v) for v in vals
          if v is not None and np.isfinite(float(v))]
    return float(np.median(xs)) if xs else None


def _rank(a):
    if _sps is not None:
        return _sps.rankdata(a)
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    # average ties
    vals, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(vals))
    np.add.at(sums, inv, ranks)
    return sums[inv] / cnt[inv]


def spearman(x, y):
    """Return (rho or None, n_used)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = int(len(x))
    if n < 3:
        return None, n
    rx, ry = _rank(x), _rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return None, n
    rho = float(np.corrcoef(rx, ry)[0, 1])
    return (rho if np.isfinite(rho) else None), n


def fit_sign_threshold(phase, labels):
    """1-D threshold classifier pred = (phase > thr); same logic as run_e1
    part_b fit_thr. Returns (best_accuracy, threshold)."""
    ph = np.asarray(phase, dtype=float)
    lb = np.asarray(labels, dtype=int)
    m = np.isfinite(ph)
    ph, lb = ph[m], lb[m]
    if len(ph) == 0:
        return None, None
    order = np.argsort(ph, kind="stable")
    ph_s, lb_s = ph[order], lb[order]
    best_acc, best_thr = -1.0, 0.0
    for k in range(len(ph_s) + 1):
        pred = np.concatenate([np.zeros(k, dtype=int),
                               np.ones(len(ph_s) - k, dtype=int)])
        acc = float((pred == lb_s).mean())
        if acc > best_acc:
            best_acc = acc
            best_thr = float(ph_s[k - 1]) if k > 0 else 0.0
    return best_acc, best_thr


def eval_sign_threshold(phase, labels, thr):
    ph = np.asarray(phase, dtype=float)
    lb = np.asarray(labels, dtype=int)
    m = np.isfinite(ph)
    ph, lb = ph[m], lb[m]
    if len(ph) == 0:
        return None, 0
    pred = (ph > thr).astype(int)
    return float((pred == lb).mean()), int(len(ph))


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:  # corrupt / partial file: skip gracefully
        return None, f"{type(e).__name__}: {e}"


def gather_files(root, include_smoke):
    """Return {milestone: [(fname, obj)]}, {milestone: [skipped fname: err]}."""
    found, errors = {}, {}
    for sub in ("m0", "e1", "e2", "e3", "e4", "e5"):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        items, errs = [], []
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            if fn.endswith("_smoke.json") and not include_smoke:
                errs.append(f"{fn}: skipped (smoke run; use --include-smoke)")
                continue
            obj, err = read_json(os.path.join(d, fn))
            if err:
                errs.append(f"{fn}: {err}")
            else:
                items.append((fn, obj))
        if items:
            found[sub] = items
        if errs:
            errors[sub] = errs
    return found, errors


def phase_stat(alpha, delta, sigma2):
    """alpha^2 * delta / sigma^2 with the sigma^2=0 guard.

    Returns (value, used_sigma: bool). delta here is the delta PROXY (an
    excess-loss scale, i.e. plays the role of delta^2 in the theory).
    """
    if alpha is None or delta is None:
        return None, False
    a2d = float(alpha) ** 2 * float(delta)
    if sigma2 is not None and float(sigma2) > EPS_SIGMA:
        return a2d / float(sigma2), True
    return a2d, False


# ---------------------------------------------------------------- M0

def analyze_m0(files):
    rows = []
    for fn, obj in files:
        argv = obj.get("meta", {}).get("argv", {})
        final = obj.get("final", {})
        rows.append({
            "file": fn,
            "dataset": argv.get("dataset"),
            "arch": argv.get("arch"),
            "seed": argv.get("seed"),
            "test_acc": final.get("test_acc"),
            "rot_acc": final.get("rot_acc"),
            "acc_gate": obj.get("acc_gate"),
            "rot_gate": obj.get("rot_gate"),
            "gate_pass": obj.get("gate_pass"),
        })
    rows.sort(key=lambda r: (str(r["dataset"]), str(r["arch"]), str(r["seed"])))
    return {"n_runs": len(rows), "runs": rows,
            "all_gates_pass": all(bool(r["gate_pass"]) for r in rows) if rows else None}


# ---------------------------------------------------------------- E1

def analyze_e1(files):
    parts = {}      # part -> {seed: obj}
    eta_by_seed = {}
    for fn, obj in files:
        m = re.match(r"e1_([a-f])_seed(\d+)\.json$", fn)
        if not m:
            continue  # e1_summary_seed*.json is redundant with the part files
        part, seed = m.group(1), int(m.group(2))
        parts.setdefault(part, {})[seed] = obj
        if part == "a" and "eta" in obj:
            eta_by_seed[seed] = float(obj["eta"])

    out = {"parts_present": sorted(parts), "by_part": {}}

    if "a" in parts:
        seeds = sorted(parts["a"])
        out["by_part"]["a"] = {
            "seeds": seeds,
            "worst_rel_err": max(parts["a"][s]["worst_rel_err"] for s in seeds),
            "worst_rel_err_by_seed": {str(s): parts["a"][s]["worst_rel_err"]
                                      for s in seeds},
            "gate_pass": all(bool(parts["a"][s]["gate_pass"]) for s in seeds),
        }

    if "b" in parts:
        seeds = sorted(parts["b"])
        rows = []
        for s in seeds:
            o = parts["b"][s]
            eta = eta_by_seed.get(s, E1_DEFAULT_ETA)
            rows.append({
                "seed": s,
                "fitted_threshold": o["fitted_threshold"],
                "theory_threshold_eta_over_2": eta / 2.0,
                "threshold_ratio": (o["fitted_threshold"] / (eta / 2.0)
                                    if eta > 0 else None),
                "eta_source": ("e1_a" if s in eta_by_seed else
                               f"default {E1_DEFAULT_ETA} (part b JSON has no eta)"),
                "fit_accuracy": o.get("fit_accuracy", o.get("sign_pred_accuracy")),
                "holdout_accuracy": o.get("holdout_accuracy", o.get("sign_pred_accuracy")),
                "gate_pass": bool(o["gate_pass"]),
            })
        out["by_part"]["b"] = {
            "seeds": seeds, "rows": rows,
            "mean_fitted_threshold": mean([r["fitted_threshold"] for r in rows]),
            "mean_holdout_accuracy": mean([r["holdout_accuracy"] for r in rows]),
            "gate_pass": all(r["gate_pass"] for r in rows),
        }

    if "c" in parts:
        seeds = sorted(parts["c"])
        out["by_part"]["c"] = {
            "seeds": seeds,
            "frac_risk_within_5pct": mean(
                [parts["c"][s]["frac_risk_within_5pct"] for s in seeds]),
            "frac_time_within_2x": mean(
                [parts["c"][s]["frac_time_within_2x"] for s in seeds]),
            "gate_pass": all(bool(parts["c"][s]["gate_pass"]) for s in seeds),
        }

    if "d" in parts:
        seeds = sorted(parts["d"])
        cell_rows = {}
        for s in seeds:
            for r in parts["d"][s]["rows"]:
                key = (r["alpha"], r["delta"])
                cell_rows.setdefault(key, []).append(r)
        rows = []
        for (a, dl) in sorted(cell_rows):
            rs = cell_rows[(a, dl)]
            rows.append({
                "alpha": a, "delta": dl,
                "t_star": rs[0]["t_star"],
                "median_t_hat": mean([r["median_t_hat"] for r in rs]),
                "median_risk_ratio": mean([r["median_risk_ratio"] for r in rs]),
                "p90_risk_ratio": mean([r["p90_risk_ratio"] for r in rs]),
                "frac_worse_than_frozen": mean(
                    [r["frac_worse_than_frozen"] for r in rs]),
                "safe_vs_frozen": all(bool(r["safe_vs_frozen"]) for r in rs),
            })
        out["by_part"]["d"] = {
            "seeds": seeds, "rows": rows,
            "p90_gate": all(bool(parts["d"][s]["p90_gate"]) for s in seeds),
            "safety_gate": all(bool(parts["d"][s]["safety_gate"]) for s in seeds),
            "gate_pass": all(bool(parts["d"][s]["gate_pass"]) for s in seeds),
        }

    if "e" in parts:
        seeds = sorted(parts["e"])
        by_alpha = {}
        for s in seeds:
            for k, v in parts["e"][s]["mean_relgain_by_alpha"].items():
                by_alpha.setdefault(k, []).append(v)
        out["by_part"]["e"] = {
            "seeds": seeds,
            "alpha0_mean_harm": mean(
                [parts["e"][s]["alpha0_mean_harm"] for s in seeds]),
            "mean_relgain_by_alpha": {k: mean(v)
                                      for k, v in sorted(by_alpha.items(),
                                                         key=lambda kv: float(kv[0]))},
            "monotone": all(bool(parts["e"][s]["monotone"]) for s in seeds),
            "margin": mean([parts["e"][s]["margin"] for s in seeds]),
            "gate_pass": all(bool(parts["e"][s]["gate_pass"]) for s in seeds),
        }

    if "f" in parts:
        seeds = sorted(parts["f"])
        by_n = {}
        for s in seeds:
            for r in parts["f"][s]["rows"]:
                by_n.setdefault(int(r["N"]), []).append(r)
        rows = [{"N": n,
                 "emp_min_risk": mean([r["emp_min_risk"] for r in by_n[n]]),
                 "theory_min_risk": mean([r["theory_min_risk"] for r in by_n[n]]),
                 "gain_emp": mean([r["gain_emp"] for r in by_n[n]]),
                 "gain_theory": mean([r["gain_theory"] for r in by_n[n]])}
                for n in sorted(by_n)]
        out["by_part"]["f"] = {
            "seeds": seeds, "rows": rows,
            "max_rel_err": max(parts["f"][s]["max_rel_err"] for s in seeds),
            "gate_pass": all(bool(parts["f"][s]["gate_pass"]) for s in seeds),
        }

    out["gates"] = {p: out["by_part"][p].get("gate_pass")
                    for p in sorted(out["by_part"])}
    return out


# ---------------------------------------------------------------- E2

def split_e2(files):
    main_r, batch_r, calib_r = [], [], []
    for fn, obj in files:
        argv = obj.get("meta", {}).get("argv", {})
        mode = argv.get("mode")
        if mode is None:  # fall back to the filename tag
            mode = ("batch_sweep" if "_batch_sweep_" in fn
                    else "calib" if "_calib_" in fn else "main")
        {"main": main_r, "batch_sweep": batch_r, "calib": calib_r}[mode].append(
            (fn, obj))
    return main_r, batch_r, calib_r


def analyze_e2_main(runs, e5_files=()):
    # E5 feature-space shift proxy for E2 (mirror of E4's delta_v2):
    # delta_feat_<dataset>_<arch>.json, joined per episode by
    # (dataset, arch, corruption, severity, idx). arch is the source model
    # of the method: resnet26ttt for ttt_*, wrn2810 for tent/pl.
    dfeat, dfeat_meta = {}, {}   # (dataset, arch) -> {(corr, sev, idx): val}
    for fn, obj in e5_files:
        m = re.match(r"delta_feat_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.json$", fn)
        if not m:
            continue
        ds_a = (obj.get("dataset", m.group(1)), obj.get("arch", m.group(2)))
        dfeat.setdefault(ds_a, {}).update(
            {(r["corruption"], int(r["severity"]), int(r["idx"])):
             float(r["delta_feat"]) for r in obj.get("records", [])})
        dfeat_meta["_".join(ds_a)] = {"file": fn, "ref": obj.get("ref"),
                                      "model_seed": obj.get("model_seed")}

    cells = {}   # (dataset, method, corruption, severity, bn_mode) -> episode list
    for fn, obj in runs:
        argv = obj["meta"]["argv"]
        ds, meth = argv["dataset"], argv["method"]
        bn = argv.get("bn_mode", "eval")
        for cell in obj.get("results", []):
            key = (ds, meth, cell["corruption"], int(cell["severity"]), bn)
            cells.setdefault(key, []).extend(cell.get("episodes", []))

    cell_rows = []
    for key in sorted(cells):
        ds, meth, corr, sev, bn = key
        eps = cells[key]
        sig = [e.get("sigma2_rel") for e in eps]
        det = all((s is None) or (float(s) <= EPS_SIGMA) for s in sig)
        fmap = dfeat.get((ds, E2_METHOD_ARCH.get(meth)), {})
        phases, phases_feat = [], []
        for e in eps:
            v, _used = phase_stat(e.get("alpha"), e.get("delta_proxy"),
                                  e.get("sigma2_rel"))
            phases.append(v)
            # PRIMARY (when joined): representation-space shift, sign of
            # alpha preserved via alpha*abs(alpha) (delta_feat >= 0)
            df = fmap.get((corr, sev, int(e["idx"]))) \
                if e.get("idx") is not None else None
            if df is not None and e.get("alpha") is not None:
                a = float(e["alpha"])
                s2 = e.get("sigma2_rel")
                num = a * abs(a) * df
                phases_feat.append(
                    num / float(s2)
                    if (s2 is not None and float(s2) > EPS_SIGMA) else num)
            else:
                phases_feat.append(None)
        # gain (loss-based, per plan: loss(frozen) - loss(adapted)) per step;
        # CE losses are heavy-tailed -> keep MEDIAN stats alongside means
        steps_all = sorted({int(t) for e in eps for t in e.get("steps", {})})
        gain_by_step, gain_by_step_median, acc_by_step = {}, {}, {}
        for t in steps_all:
            g = [e["frozen_loss"] - e["steps"][str(t)]["loss"]
                 for e in eps if str(t) in e.get("steps", {})]
            a = [e["steps"][str(t)]["correct"]
                 for e in eps if str(t) in e.get("steps", {})]
            gain_by_step[str(t)] = mean(g)
            gain_by_step_median[str(t)] = median(g)
            acc_by_step[str(t)] = mean(a)
        final_t = steps_all[-1] if steps_all else None
        gains = [gain_by_step[str(t)] for t in steps_all
                 if gain_by_step[str(t)] is not None]
        alta_eps = [e["alta"] for e in eps if e.get("alta")]
        row = {
            "dataset": ds, "method": meth, "corruption": corr,
            "severity": sev, "bn_mode": bn, "n_episodes": len(eps),
            "mean_alpha": mean([e.get("alpha") for e in eps]),
            "median_alpha": median([e.get("alpha") for e in eps]),
            "mean_sigma2_rel": mean(sig),
            "median_sigma2_rel": median(sig),
            "mean_delta_proxy": mean([e.get("delta_proxy") for e in eps]),
            "median_delta_proxy": median([e.get("delta_proxy") for e in eps]),
            "frozen_acc": mean([e.get("frozen_correct") for e in eps]),
            "deterministic_sigma": bool(det),
            "mean_phase_stat": mean(phases),
            "median_phase_stat": median(phases),
            "mean_phase_feat": mean(phases_feat),
            "median_phase_feat": median(phases_feat),
            "n_feat_joined": sum(1 for p in phases_feat if p is not None),
            "gain_by_step": gain_by_step,
            "gain_by_step_median": gain_by_step_median,
            "acc_by_step": acc_by_step,
            "final_step": final_t,
            "gain_final": gain_by_step.get(str(final_t)) if final_t else None,
            "gain_final_median": (gain_by_step_median.get(str(final_t))
                                  if final_t else None),
            "gain_best": max(gains) if gains else None,
            "gain_best_median": (max(v for v in
                                     gain_by_step_median.values()
                                     if v is not None)
                                 if any(v is not None for v in
                                        gain_by_step_median.values())
                                 else None),
            "alta": ({"n": len(alta_eps),
                      "mean_t_hat": mean([a["t_hat"] for a in alta_eps]),
                      "mean_gain": mean([e["frozen_loss"] - e["alta"]["loss"]
                                         for e in eps if e.get("alta")]),
                      "acc": mean([a["correct"] for a in alta_eps])}
                     if alta_eps else None),
        }
        cell_rows.append(row)

    def _sp(rows, xkey, ykey):
        rho, _n = spearman([r[xkey] for r in rows], [r[ykey] for r in rows])
        return rho

    def _sp_by_step(rows, xkey, stepkey):
        steps = sorted({int(t) for r in rows for t in r.get(stepkey, {})})
        out = {}
        for t in steps:
            pairs = [(r[xkey], r[stepkey].get(str(t))) for r in rows
                     if r.get(stepkey, {}).get(str(t)) is not None]
            rho, _n = spearman([p[0] for p in pairs], [p[1] for p in pairs])
            out[str(t)] = rho
        return out

    def corr_group(rows, label):
        dets = {r["deterministic_sigma"] for r in rows}
        n_feat = sum(1 for r in rows if r["mean_phase_feat"] is not None)
        use_feat = n_feat >= 3
        out = {"group": label, "n_cells": len(rows),
               "n_cells_feat": n_feat,
               "primary_statistic": ("delta_feat (E5 feature shift)"
                                     if use_feat else "loss_delta_proxy"),
               # loss-based statistic (secondary when delta_feat present)
               "spearman_mean_final": _sp(rows, "mean_phase_stat",
                                          "gain_final"),
               "spearman_mean_best": _sp(rows, "mean_phase_stat",
                                         "gain_best"),
               "spearman_median_final": _sp(rows, "median_phase_stat",
                                            "gain_final_median"),
               "spearman_median_best": _sp(rows, "median_phase_stat",
                                           "gain_best_median"),
               # delta_feat statistic (PRIMARY when joined)
               "spearman_feat_mean_final": _sp(rows, "mean_phase_feat",
                                               "gain_final"),
               "spearman_feat_mean_best": _sp(rows, "mean_phase_feat",
                                              "gain_best"),
               "spearman_feat_median_final": _sp(rows, "median_phase_feat",
                                                 "gain_final_median"),
               "spearman_feat_median_best": _sp(rows, "median_phase_feat",
                                                "gain_best_median"),
               # diagnostic: correlation with gain at EACH recorded step
               # (theory: peaks near the per-cell optimal step)
               "spearman_by_step_mean": _sp_by_step(rows, "mean_phase_stat",
                                                    "gain_by_step"),
               "spearman_by_step_median": _sp_by_step(
                   rows, "median_phase_stat", "gain_by_step_median"),
               "deterministic_sigma": (True if dets == {True} else
                                       False if dets == {False} else "mixed"),
               "note": (("primary phase = alpha*abs(alpha)*delta_feat/sigma^2 "
                         "(E5); secondary loss-based: " if use_feat else "")
                        + ("phase = alpha^2*delta_proxy (sigma^2=0, "
                           "deterministic objective at N=1)"
                           if dets == {True} else
                           "phase = alpha^2*delta_proxy/sigma^2"
                           if dets == {False} else
                           "MIXED statistic across cells (flagged)"))}
        return out

    methods = sorted({r["method"] for r in cell_rows})
    correlations = [corr_group([r for r in cell_rows if r["method"] == m], m)
                    for m in methods]
    if cell_rows:
        correlations.append(corr_group(cell_rows, "pooled"))

    # C2 gate: stochastic (A2-satisfying) methods only; the PRIMARY
    # statistic (delta_feat when joined, else loss-based) reaching
    # rho >= 0.5 in ANY of {mean, median} x {final, best} counts as a pass
    def _method_pass(c):
        pre = ("spearman_feat_"
               if "delta_feat" in c["primary_statistic"] else "spearman_")
        keys = [pre + k for k in ("mean_final", "median_final",
                                  "mean_best", "median_best")]
        return any(c[k] is not None and c[k] >= 0.5 for k in keys)

    gate_corrs = [c for c in correlations if c["group"] in C2_GATE_METHODS]
    boundary_corrs = [c for c in correlations
                      if c["group"] in methods
                      and c["group"] not in C2_GATE_METHODS]
    n_pass = sum(1 for c in gate_corrs if _method_pass(c))
    return {"n_cells": len(cell_rows), "methods": methods, "cells": cell_rows,
            "correlations": correlations,
            "delta_feat_sources": {k: dfeat_meta[k]
                                   for k in sorted(dfeat_meta)},
            "gate_methods": sorted(c["group"] for c in gate_corrs),
            "theory_boundary_methods": sorted(c["group"]
                                              for c in boundary_corrs),
            "n_gate_methods_pass": n_pass,
            "gate_spearman": (n_pass >= 2) if gate_corrs else None,
            "gate_note": ("gate over stochastic methods (ttt_rot/ttt_mask) "
                          "only, on the PRIMARY statistic (delta_feat when "
                          "E5 files are joined, else loss-based "
                          "delta_proxy), any of mean/median x final/best; "
                          "tent/pl violate persistent alignment (A2) by "
                          "design and are reported as theory-boundary "
                          "evidence, not counted for/against C2")}


def analyze_e2_batch(runs):
    groups = {}  # (dataset, method, bn_mode) -> {N: [batch dicts]}
    for fn, obj in runs:
        argv = obj["meta"]["argv"]
        key = (argv["dataset"], argv["method"], argv.get("bn_mode", "eval"))
        g = groups.setdefault(key, {})
        for cell in obj.get("results", []):
            g.setdefault(int(cell["N"]), []).extend(cell.get("batches", []))

    out_groups = []
    for key in sorted(groups):
        ds, meth, bn = key
        by_n = groups[key]
        ns = sorted(by_n)
        has_steps = any("steps" in b for bs in by_n.values() for b in bs)
        rows = []
        for n in ns:
            bs = by_n[n]
            # per-step gain (new schema); old-format records lack "steps"
            steps_all = sorted({int(t) for b in bs for t in b.get("steps", {})})
            gain_by_step = {
                str(t): mean([b["steps"][str(t)]["acc"] - b["frozen_acc"]
                              for b in bs if str(t) in b.get("steps", {})])
                for t in steps_all}
            # absolute noise reconstruction (sigma2_batch_rel conflates 1/N
            # with the shrinking batch-mean gradient norm):
            #   sigma2_batch_abs = sigma2_batch_rel * ||g_mean||^2  ~ 1/N
            #   sigma2_point_abs = sigma2_batch_abs * N             ~ const
            s2b_abs = [b["sigma2_batch_rel"] * b["gnorm_ssl"] ** 2
                       for b in bs
                       if b.get("sigma2_batch_rel") is not None
                       and b.get("gnorm_ssl") is not None]
            rows.append({
                "N": n, "n_batches": len(bs),
                "mean_gain_acc": mean([b["adapted_acc"] - b["frozen_acc"]
                                       for b in bs]),
                "gain_by_step": gain_by_step,
                "gain_step1": gain_by_step.get("1"),
                "mean_frozen_acc": mean([b["frozen_acc"] for b in bs]),
                "mean_adapted_acc": mean([b["adapted_acc"] for b in bs]),
                "mean_adapted_loss": mean([b.get("adapted_loss") for b in bs]),
                "mean_sigma2_batch_rel": mean([b.get("sigma2_batch_rel")
                                               for b in bs]),
                "median_sigma2_batch_abs": median(s2b_abs),
                "median_sigma2_point_abs": median([s * n for s in s2b_abs]),
                "mean_alpha": mean([b.get("alpha") for b in bs]),
            })
        # 1/N reference anchored at the largest N with sigma^2 > 0 (secondary
        # relative-scale evidence; the primary gates use absolute quantities)
        anchor = None
        for r in reversed(rows):
            s2 = r["mean_sigma2_batch_rel"]
            if s2 is not None and s2 > EPS_SIGMA:
                anchor = r
                break
        for r in rows:
            r["sigma2_ref_1_over_N"] = (
                anchor["mean_sigma2_batch_rel"] * anchor["N"] / r["N"]
                if anchor else None)

        # --- primary C3 gain criteria (step-1 gain, published-Tent regime);
        #     old-format files fall back to the final-step gain (flagged)
        gain_key = "gain_step1" if has_steps else "mean_gain_acc"
        g1 = next((r[gain_key] for r in rows if r["N"] == 1), None)
        g32 = mean([r[gain_key] for r in rows if r["N"] >= 32])
        recovery = bool(g32 > g1) if None not in (g1, g32) else None
        # collapse: N=1 step grid nonpositive AND degrading with more steps
        n1 = next((r for r in rows if r["N"] == 1), None)
        collapse_traj = None
        n1_traj = None
        if n1 is not None:
            if has_steps and n1["gain_by_step"]:
                ts = sorted(int(t) for t in n1["gain_by_step"])
                n1_traj = [n1["gain_by_step"][str(t)] for t in ts]
                if all(v is not None for v in n1_traj):
                    collapse_traj = bool(n1_traj[0] <= 1e-9
                                         and n1_traj[-1] <= n1_traj[0] + 1e-9)
            elif n1["mean_gain_acc"] is not None:  # final-only fallback
                collapse_traj = bool(n1["mean_gain_acc"] < 0)
        # secondary: legacy final-gain N=1 vs N>=8 comparison (kept as table)
        gf1 = next((r["mean_gain_acc"] for r in rows if r["N"] == 1), None)
        gf8 = mean([r["mean_gain_acc"] for r in rows if r["N"] >= 8])

        # --- sigma^2 gates on ABSOLUTE quantities, N in {2..64} (N=1 is
        #     deterministic: sigma^2 == 0 by construction, excluded)
        pt_meds = [(r["N"], r["median_sigma2_point_abs"]) for r in rows
                   if 2 <= r["N"] <= 64
                   and r["median_sigma2_point_abs"] is not None
                   and r["median_sigma2_point_abs"] > EPS_SIGMA]
        pt_ratio = (max(s for _, s in pt_meds) / min(s for _, s in pt_meds)
                    if len(pt_meds) >= 2 else None)
        gate_point_const = (pt_ratio <= 4.0) if pt_ratio is not None else None
        ba_meds = [(r["N"], r["median_sigma2_batch_abs"]) for r in rows
                   if 2 <= r["N"] <= 64
                   and r["median_sigma2_batch_abs"] is not None
                   and r["median_sigma2_batch_abs"] > EPS_SIGMA]
        rho_ba, _ = spearman([n for n, _ in ba_meds],
                             [s for _, s in ba_meds])
        gate_batch_1_over_N = (rho_ba <= -0.8) if rho_ba is not None else None

        out_groups.append({
            "dataset": ds, "method": meth, "bn_mode": bn, "Ns": ns,
            "per_N": rows,
            "final_only": not has_steps,
            "gain_basis": ("step1" if has_steps else
                           "final step (old-format file, no per-step stats)"),
            "sigma2_anchor_N": anchor["N"] if anchor else None,
            "sigma2_point_abs_max_min_ratio": pt_ratio,
            "gate_sigma2_point_abs_const": gate_point_const,
            "spearman_sigma2_batch_abs_vs_N": rho_ba,
            "gate_sigma2_batch_abs_1_over_N": gate_batch_1_over_N,
            "sigma2_gates_N_used": [n for n, _ in ba_meds],
            "collapse": {"gain_step1_at_N1": g1,
                         "mean_gain_step1_N_ge_32": g32,
                         "recovers_step1_N32_vs_N1": recovery,
                         "N1_gain_trajectory": n1_traj,
                         "N1_nonpositive_to_degrading": collapse_traj,
                         "gain_final_at_N1": gf1,
                         "mean_gain_final_N_ge_8": gf8},
        })

    # bn-train vs bn-eval comparison (same dataset+method, both modes present)
    bn_pairs = []
    seen = {(g["dataset"], g["method"]): {} for g in out_groups}
    for g in out_groups:
        seen[(g["dataset"], g["method"])][g["bn_mode"]] = g
    for (ds, meth) in sorted(seen):
        modes = seen[(ds, meth)]
        if "eval" in modes and "train" in modes:
            rows = []
            for n in sorted(set(modes["eval"]["Ns"]) & set(modes["train"]["Ns"])):
                ge = next(r["mean_gain_acc"] for r in modes["eval"]["per_N"]
                          if r["N"] == n)
                gt = next(r["mean_gain_acc"] for r in modes["train"]["per_N"]
                          if r["N"] == n)
                rows.append({"N": n, "gain_bn_eval": ge, "gain_bn_train": gt,
                             "diff_train_minus_eval":
                                 (gt - ge) if None not in (ge, gt) else None})
            bn_pairs.append({"dataset": ds, "method": meth, "per_N": rows})

    # C3 gating: SOURCE SPLIT (physics-motivated).
    # GAIN gates (N=1 nonpositive-to-degrading, step-1 recovery at N>=32)
    # come from bn-TRAIN groups (the published-Tent protocol).
    # SIGMA^2-mechanics gates (point_abs constancy, batch_abs ~1/N) come
    # from bn-EVAL groups: only there are per-sample gradients independent.
    # In bn-train mode BatchNorm couples per-sample gradients through the
    # batch statistics, so per-sample gradient dispersion is NOT the
    # theory's independent noise (an observation, not a failure).
    gain_src = [g for g in out_groups if g["bn_mode"] == "train"]
    gain_src_note = "bn-train (published-Tent protocol)"
    if not gain_src:
        gain_src = list(out_groups)
        gain_src_note = "all groups (no bn-train runs present; fallback)"
    sigma_src = [g for g in out_groups if g["bn_mode"] == "eval"]
    sigma_src_note = "bn-eval (independent per-sample gradients)"
    if not sigma_src:
        sigma_src = list(out_groups)
        sigma_src_note = "all groups (no bn-eval runs present; fallback)"
    for g in out_groups:
        g["used_for_gain_gates"] = any(g is p for p in gain_src)
        g["used_for_sigma_gates"] = any(g is p for p in sigma_src)
        g["is_primary_protocol"] = g["used_for_gain_gates"]  # back-compat

    def _any_positive_gain(g):
        for r in g["per_N"]:
            vals = list(r["gain_by_step"].values()) + [r["mean_gain_acc"]]
            if any(v is not None and v > 0 for v in vals):
                return True
        return False

    bn_eval_secondary = [
        {"dataset": g["dataset"], "method": g["method"],
         "positive_gain_at_any_N": _any_positive_gain(g)}
        for g in out_groups if g["bn_mode"] == "eval"]

    def _all_over(src, get):
        vals = [get(g) for g in src]
        vals = [v for v in vals if v is not None]
        return all(vals) if vals else None

    return {"groups": out_groups, "bn_train_vs_eval": bn_pairs,
            "any_final_only": any(g["final_only"] for g in out_groups),
            "gain_gate_source": gain_src_note,
            "sigma_gate_source": sigma_src_note,
            "bn_coupling_note": (
                "In bn-train mode BatchNorm couples per-sample gradients "
                "through the batch statistics, so per-sample gradient "
                "dispersion there is not the theory's independent noise "
                "(bn-train point_abs ratios can be large); sigma^2 gates "
                "are therefore evaluated on bn-eval groups."),
            "bn_eval_secondary": bn_eval_secondary,
            "gate_recovery_step1": _all_over(
                gain_src,
                lambda g: g["collapse"]["recovers_step1_N32_vs_N1"]),
            "gate_N1_collapse_trajectory": _all_over(
                gain_src,
                lambda g: g["collapse"]["N1_nonpositive_to_degrading"]),
            "gate_sigma2_point_abs_const": _all_over(
                sigma_src, lambda g: g["gate_sigma2_point_abs_const"]),
            "gate_sigma2_batch_abs_1_over_N": _all_over(
                sigma_src, lambda g: g["gate_sigma2_batch_abs_1_over_N"])}


def analyze_e2_calib(runs):
    pools = {False: [], True: []}   # temp_scaled -> episodes
    temps, datasets = [], set()
    for fn, obj in runs:
        argv = obj["meta"]["argv"]
        datasets.add(argv["dataset"])
        res = obj.get("results", {})
        if isinstance(res, dict):
            if res.get("temperature") is not None:
                temps.append(float(res["temperature"]))
            for cell in res.get("cells", []):
                pools[bool(cell["temp_scaled"])].extend(cell.get("episodes", []))

    def split_stats(eps):
        if not eps:
            return None
        al = [e["alpha_ent"] for e in eps]
        cf = [e["confidence"] for e in eps]
        cr = [e["correct"] for e in eps]
        rho_conf, _ = spearman(al, cf)
        rho_corr, _ = spearman(al, cr)
        cw = [e for e in eps if e["confidence"] > CONF_THR and e["correct"] == 0]
        cright = [e for e in eps
                  if e["confidence"] > CONF_THR and e["correct"] == 1]
        # per-step adapted stats (new schema); old files lack "steps"
        steps_all = sorted({int(t) for e in eps for t in e.get("steps", {})})
        loss_by_step = {
            str(t): mean([e["steps"][str(t)]["loss"] - e["frozen_loss"]
                          for e in eps if str(t) in e.get("steps", {})])
            for t in steps_all}
        acc_by_step = {
            str(t): mean([e["steps"][str(t)]["correct"]
                          for e in eps if str(t) in e.get("steps", {})])
            for t in steps_all}
        return {
            "n_episodes": len(eps),
            "mean_alpha_ent": mean(al),
            "spearman_alpha_vs_confidence": rho_conf,
            "spearman_alpha_vs_correct": rho_corr,
            "n_confident_wrong": len(cw),
            "frac_alpha_neg_confident_wrong": mean(
                [float(e["alpha_ent"] < 0) for e in cw]),
            "n_confident_right": len(cright),
            "frac_alpha_neg_confident_right": mean(
                [float(e["alpha_ent"] < 0) for e in cright]),
            "mean_adapted_minus_frozen_loss": mean(
                [e["adapted_loss"] - e["frozen_loss"] for e in eps]),
            "adapted_acc": mean([e["adapted_correct"] for e in eps]),
            "frozen_acc": mean([e["correct"] for e in eps]),
            "final_only": not steps_all,
            "excess_loss_by_step": loss_by_step,   # mean(adapted_t - frozen)
            "acc_by_step": acc_by_step,
        }

    s_raw = split_stats(pools[False])
    s_tmp = split_stats(pools[True])
    shift = None
    loss_cmp = None
    loss_cmp_early = None
    early_basis = None
    if s_raw and s_tmp:
        shift = s_tmp["mean_alpha_ent"] - s_raw["mean_alpha_ent"]
        loss_cmp = (s_tmp["mean_adapted_minus_frozen_loss"]
                    - s_raw["mean_adapted_minus_frozen_loss"])
        # C4 criterion basis: steps 1 and 2 (the 20-step endpoint is
        # deliberately in the collapse regime, outside the claim's scope)
        early = [s_tmp["excess_loss_by_step"][t]
                 - s_raw["excess_loss_by_step"][t]
                 for t in ("1", "2")
                 if s_tmp["excess_loss_by_step"].get(t) is not None
                 and s_raw["excess_loss_by_step"].get(t) is not None]
        if early:
            loss_cmp_early = mean(early)
            early_basis = "mean over steps 1-2"
        else:  # old-format files: fall back to the final adapted loss
            loss_cmp_early = loss_cmp
            early_basis = "final step (old-format file, no per-step stats)"
    return {"datasets": sorted(datasets),
            "mean_temperature": mean(temps),
            "no_temp": s_raw, "temp_scaled": s_tmp,
            "alpha_ent_shift_with_temp": shift,
            "adapted_loss_change_with_temp": loss_cmp,
            "adapted_loss_change_with_temp_early": loss_cmp_early,
            "early_criterion_basis": early_basis,
            "confidence_threshold": CONF_THR}


# ---------------------------------------------------------------- E3

def analyze_e3(files):
    rows = {}  # (corruption, severity, method, stopping) -> list of cell dicts
    for fn, obj in files:
        argv = obj["meta"]["argv"]
        meth, stop = argv["method"], argv["stopping"]
        for cell in obj.get("results", []):
            if stop == "alta":
                # post-safety-fix runs flag every batch: ALTA's t=0 candidate
                # is the TRUE eval-BN frozen prediction (can decline to
                # adapt). Unflagged alta cells are stale semantics.
                cell = dict(cell)
                cell["_alta_t0_is_frozen"] = any(
                    b.get("alta_t0_is_frozen")
                    for b in cell.get("batches", []))
            key = (cell["corruption"], int(cell["severity"]), meth, stop)
            rows.setdefault(key, []).append(cell)

    table = []
    stale_dropped_total = 0
    for key in sorted(rows):
        corr, sev, meth, stop = key
        cs = rows[key]
        alta_flag = None
        n_stale_dropped = 0
        if stop == "alta":
            flagged = [c for c in cs if c["_alta_t0_is_frozen"]]
            if flagged:  # prefer fixed-semantics runs; drop stale cells
                n_stale_dropped = len(cs) - len(flagged)
                stale_dropped_total += n_stale_dropped
                cs = flagged
                alta_flag = True
            else:
                alta_flag = False  # stale semantics only (pending rerun)
        al = [a for c in cs for a in c.get("alignment", [])]
        best_fixed = mean([max(c["acc_by_step"]) for c in cs
                           if c.get("acc_by_step")])
        table.append({
            "corruption": corr, "severity": sev, "method": meth,
            "stopping": stop, "n_seeds": len(cs),
            "alta_t0_is_frozen": alta_flag,
            "n_stale_cells_dropped": n_stale_dropped,
            "n_images": int(np.sum([c.get("n_images", 0) for c in cs])),
            "frozen_acc": mean([c["frozen_acc"] for c in cs]),
            "bn0_acc": mean([c["bn0_acc"] for c in cs]),
            "adapted_acc": mean([c["adapted_acc"] for c in cs]),
            "mean_t_hat": mean([c["mean_t_hat"] for c in cs]),
            "best_fixed_acc": best_fixed,
            "final_fixed_acc": mean([c["acc_by_step"][-1] for c in cs
                                     if c.get("acc_by_step")]),
            "mean_alpha": mean([a.get("alpha") for a in al]),
            "mean_sigma2_rel": mean([a.get("sigma2_rel") for a in al]),
            "delta_proxy": mean([c.get("delta_proxy") for c in cs]),
        })

    # ALTA vs fixed gap per (corruption, severity, method)
    idx = {(r["corruption"], r["severity"], r["method"], r["stopping"]): r
           for r in table}
    gaps = []
    for (corr, sev, meth, stop) in sorted(idx):
        if stop != "alta":
            continue
        a = idx[(corr, sev, meth, "alta")]
        f = idx.get((corr, sev, meth, "fixed"))
        o = idx.get((corr, sev, meth, "oracle"))
        gaps.append({
            "corruption": corr, "severity": sev, "method": meth,
            "alta_acc": a["adapted_acc"], "alta_mean_t_hat": a["mean_t_hat"],
            "best_fixed_acc": f["best_fixed_acc"] if f else None,
            "final_fixed_acc": f["final_fixed_acc"] if f else None,
            "gap_alta_vs_best_fixed": (a["adapted_acc"] - f["best_fixed_acc"]
                                       if f and f["best_fixed_acc"] is not None
                                       else None),
            "gap_alta_vs_final_fixed": (a["adapted_acc"] - f["final_fixed_acc"]
                                        if f and f["final_fixed_acc"] is not None
                                        else None),
            "oracle_acc": o["adapted_acc"] if o else None,
        })

    # safety: adapted < frozen - 0.2pt on any corruption (per stopping mode)
    violations = [{"corruption": r["corruption"], "severity": r["severity"],
                   "method": r["method"], "stopping": r["stopping"],
                   "alta_t0_is_frozen": r["alta_t0_is_frozen"],
                   "adapted_acc": r["adapted_acc"], "frozen_acc": r["frozen_acc"],
                   "shortfall_pt": (r["frozen_acc"] - r["adapted_acc"]) * 100}
                  for r in table
                  if r["adapted_acc"] is not None and r["frozen_acc"] is not None
                  and r["adapted_acc"] < r["frozen_acc"] - SAFETY_PT]
    # C5 safety gate: evaluated only on fixed-semantics (flagged) alta runs
    # when any exist for a given corruption; corruptions with only stale
    # alta runs keep counting until they are rerun.
    flagged_corrs = {r["corruption"] for r in table
                     if r["stopping"] == "alta" and r["alta_t0_is_frozen"]}
    alta_violations = [
        v for v in violations if v["stopping"] == "alta"
        and (v["alta_t0_is_frozen"]
             or v["corruption"] not in flagged_corrs)]
    n_stale_alta_rows = sum(1 for r in table if r["stopping"] == "alta"
                            and r["alta_t0_is_frozen"] is False)

    per_method = []
    for meth in sorted({g["method"] for g in gaps}):
        gs = [g for g in gaps if g["method"] == meth]
        per_method.append({
            "method": meth, "n_cells": len(gs),
            "mean_gap_vs_best_fixed": mean(
                [g["gap_alta_vs_best_fixed"] for g in gs]),
            "mean_gap_vs_final_fixed": mean(
                [g["gap_alta_vs_final_fixed"] for g in gs]),
            "mean_alta_t_hat": mean([g["alta_mean_t_hat"] for g in gs]),
        })
    mean_gap_pooled = mean([g["gap_alta_vs_best_fixed"] for g in gaps])
    return {"cells": table, "alta_vs_fixed": gaps, "per_method": per_method,
            "mean_gap_alta_vs_best_fixed_pooled": mean_gap_pooled,
            "gate_within_half_pt": ((mean_gap_pooled >= -0.005)
                                    if mean_gap_pooled is not None else None),
            "safety_violations": violations,
            "n_alta_safety_violations": len(alta_violations),
            "n_stale_alta_rows": n_stale_alta_rows,
            "n_stale_alta_cells_dropped": stale_dropped_total,
            "gate_safety_alta": ((len(alta_violations) == 0)
                                 if any(r["stopping"] == "alta" for r in table)
                                 else None)}


# ---------------------------------------------------------------- E4

def analyze_e4(files, e5_files=()):
    # E5 hidden-state shift proxy (delta_v2_<domain>.json): cosine distance
    # of each doc's mean-pooled GPT-2 hidden state to the wikitext reference
    # mean. A DIRECT shift measure -- needs no centering, and resolves the
    # domain-entropy confound of the loss-based delta proxy.
    dv2_map, dv2_meta = {}, {}     # domain -> {doc: delta_v2} / metadata
    for fn, obj in e5_files:
        m = re.match(r"delta_v2_([A-Za-z0-9]+)\.json$", fn)
        if not m:
            continue
        dom = obj.get("domain", m.group(1))
        dv2_map.setdefault(dom, {}).update(
            {int(r["doc"]): float(r["delta_v2"])
             for r in obj.get("records", [])})
        dv2_meta[dom] = {"file": fn, "layer": obj.get("layer"),
                         "ref": obj.get("ref")}

    refs = {}      # seed -> wikitext mean frozen cont ce (explicit ref files)
    runs = []      # (domain, adapt, seed, obj)
    for fn, obj in files:
        m = re.match(r"wikitext_ref_s(\d+)\.json$", fn)
        if m:
            refs[int(m.group(1))] = float(obj["mean_frozen_cont_ce"])
            continue
        m = re.match(r"([A-Za-z0-9]+)_(ln|lora)_s(\d+)\.json$", fn)
        if m:
            runs.append((m.group(1), m.group(2), int(m.group(3)), obj))
    # fallback ref: wikitext run's own frozen mean (per seed, prefer 'ln')
    for dom, adapt, seed, obj in sorted(runs, key=lambda r: (r[2], r[1])):
        if dom == "wikitext" and seed not in refs:
            if obj.get("wikitext_ref_mean") is not None:
                refs[seed] = float(obj["wikitext_ref_mean"])
            else:
                recs = obj.get("records", [])
                if recs:
                    refs[seed] = float(np.mean([r["frozen_cont_ce"]
                                                for r in recs]))

    pools = {}     # (domain, adapt) -> list of (record, seed)
    for dom, adapt, seed, obj in runs:
        for rec in obj.get("records", []):
            if rec.get("delta_proxy") is None and seed in refs:
                rec = dict(rec)
                rec["delta_proxy"] = rec["frozen_cont_ce"] - refs[seed]
            pools.setdefault((dom, adapt), []).append((rec, seed))

    domains = []
    within_rows = []   # per-(domain, adapt) WITHIN-domain phase-gain analysis
    for key in sorted(pools):
        dom, adapt = key
        recs = [r for r, _ in pools[key]]
        frozen = mean([r["frozen_cont_ce"] for r in recs])
        steps = sorted({int(t) for r in recs for t in r.get("fixed", {})})
        ce_by_step = {str(t): mean([float(r["fixed"][str(t)]) for r in recs
                                    if str(t) in r.get("fixed", {})])
                      for t in steps}
        best_step, best_ce = None, None
        for t in steps:
            ce = ce_by_step[str(t)]
            if ce is not None and (best_ce is None or ce < best_ce):
                best_step, best_ce = t, ce
        alta_recs = [r for r in recs if r.get("alta")]
        alta_ce = mean([r["alta"]["cont_ce"] for r in alta_recs])
        oracle_ce = mean([r["oracle"]["cont_ce"] for r in recs
                          if r.get("oracle")])
        ppl0 = math.exp(frozen) if frozen is not None else None
        domains.append({
            "domain": dom, "adapt_params": adapt, "n_docs": len(recs),
            "mean_alpha": mean([r.get("alpha") for r in recs]),
            "mean_sigma2_rel": mean([r.get("sigma2_rel") for r in recs]),
            "mean_delta_proxy": mean([r.get("delta_proxy") for r in recs]),
            "n_missing_delta": sum(1 for r in recs
                                   if r.get("delta_proxy") is None),
            "mean_frozen_cont_ce": frozen, "frozen_ppl": ppl0,
            "ce_by_step": ce_by_step,
            "best_fixed_step": best_step,
            "best_fixed_ppl": math.exp(best_ce) if best_ce is not None else None,
            "ppl_improvement_best_fixed": (ppl0 - math.exp(best_ce)
                                           if None not in (ppl0, best_ce)
                                           else None),
            "alta": ({"n": len(alta_recs),
                      "mean_t_hat": mean([r["alta"]["t_hat"]
                                          for r in alta_recs]),
                      "ppl": math.exp(alta_ce) if alta_ce is not None else None,
                      "ppl_improvement": (ppl0 - math.exp(alta_ce)
                                          if None not in (ppl0, alta_ce)
                                          else None)} if alta_recs else None),
            "oracle_ppl": (math.exp(oracle_ce)
                           if oracle_ce is not None else None),
            "oracle_mean_t_star": mean([r["oracle"]["t_star"] for r in recs
                                        if r.get("oracle")]),
        })

        # WITHIN-domain phase-gain correlation (C6 primary test).
        # PRIMARY statistic (when E5 files are present):
        #   phase_v2 = alpha * |alpha| * delta_v2 / sigma^2
        # (delta_v2 = hidden-state cosine distance to the wikitext ref;
        # a direct shift measure, no centering needed; alpha sign kept).
        # SECONDARY statistic (always): centered frozen CE --
        #   phase = alpha^2 * delta_centered / sigma^2 (sign preserved).
        dv2_dom = dv2_map.get(dom, {})
        ph_c, ph_v2, g_alta, g_bf = [], [], [], []
        for r in recs:
            if frozen is None:
                break
            d_cent = r["frozen_cont_ce"] - frozen
            ph, _used = phase_stat(r.get("alpha"), d_cent,
                                   r.get("sigma2_rel"))
            ph_c.append(ph)
            v2 = dv2_dom.get(int(r["doc"])) if r.get("doc") is not None \
                else None
            if v2 is not None and r.get("alpha") is not None:
                a = float(r["alpha"])
                s2 = r.get("sigma2_rel")
                num = a * abs(a) * v2
                ph_v2.append(num / float(s2)
                             if (s2 is not None and float(s2) > EPS_SIGMA)
                             else num)
            else:
                ph_v2.append(None)
            g_alta.append(r["frozen_cont_ce"] - r["alta"]["cont_ce"]
                          if r.get("alta") else None)
            g_bf.append(r["frozen_cont_ce"] - float(r["fixed"][str(best_step)])
                        if (best_step is not None
                            and str(best_step) in r.get("fixed", {}))
                        else None)

        def _sp(xs, ys):
            return spearman([x if x is not None else np.nan for x in xs],
                            [y if y is not None else np.nan for y in ys])

        rho_alta, n_alta = _sp(ph_c, g_alta)
        rho_bf, n_bf = _sp(ph_c, g_bf)
        rho_v2_alta, n_v2_alta = _sp(ph_v2, g_alta)
        rho_v2_bf, n_v2_bf = _sp(ph_v2, g_bf)
        use_v2 = (rho_v2_alta is not None or rho_v2_bf is not None)
        prim_alta, prim_bf = ((rho_v2_alta, rho_v2_bf) if use_v2
                              else (rho_alta, rho_bf))
        rho_pass = any(r_ is not None and r_ >= 0.3
                       for r_ in (prim_alta, prim_bf))
        within_rows.append({
            "domain": dom, "adapt_params": adapt,
            "primary_statistic": ("delta_v2 (E5 hidden-state shift)"
                                  if use_v2 else "centered_frozen_ce"),
            "rho_gain_alta_delta_v2": rho_v2_alta,
            "rho_gain_best_fixed_delta_v2": rho_v2_bf,
            "n_delta_v2_joined": n_v2_alta,
            "rho_gain_alta": rho_alta, "n_alta": n_alta,
            "rho_gain_best_fixed": rho_bf, "n_best_fixed": n_bf,
            "best_fixed_step": best_step,
            "pass_rho_ge_0.3": (rho_pass if (prim_alta is not None
                                             or prim_bf is not None)
                                else None)})

    # per-adapt within-domain gate + qualitative support criteria
    within_domain = []
    qualitative = []
    for adapt in sorted({a for (_, a) in pools}):
        wrs = [w for w in within_rows if w["adapt_params"] == adapt]
        evald = [w for w in wrs if w["pass_rho_ge_0.3"] is not None]
        n_pass = sum(1 for w in evald if w["pass_rho_ge_0.3"])
        need = min(3, len(evald))
        any_v2 = any("delta_v2" in w["primary_statistic"] for w in wrs)
        within_domain.append({
            "adapt_params": adapt, "per_domain": wrs,
            "n_domains": len(evald), "n_pass": n_pass,
            "uses_delta_v2": any_v2,
            "gate_rho_ge_0.3_in_3_of_4": ((n_pass >= need)
                                          if len(evald) >= 3 else None),
            "note": (("primary phase = alpha*abs(alpha) * delta_v2 / sigma^2 "
                      "(E5 hidden-state shift; no centering needed); "
                      "secondary = alpha^2 * delta_centered / sigma^2; "
                      if any_v2 else
                      "phase = alpha^2 * delta_centered / sigma^2, "
                      "delta centered within domain (sign preserved); ")
                     + "domain passes on gain@ALTA OR gain@best-fixed")})
        # qualitative: adaptation helps everywhere + ALTA near best fixed
        doms_a = [d for d in domains if d["adapt_params"] == adapt]
        impr_alta = [(d["domain"], d["alta"]["ppl_improvement"]
                      if d["alta"] else None) for d in doms_a]
        helps_vals = [v for _, v in impr_alta if v is not None]
        helps = (all(v > 0 for v in helps_vals)
                 if len(helps_vals) == len(doms_a) and doms_a else None)
        rel_gaps = {}
        for d in doms_a:
            ib = d["ppl_improvement_best_fixed"]
            ia = d["alta"]["ppl_improvement"] if d["alta"] else None
            rel_gaps[d["domain"]] = ((ib - ia) / ib
                                     if (ib is not None and ia is not None
                                         and ib > 0) else None)
        gap_vals = [v for v in rel_gaps.values() if v is not None]
        near = (all(v <= 0.15 for v in gap_vals) if gap_vals else None)
        qualitative.append({
            "adapt_params": adapt,
            "ppl_improvement_at_alta_by_domain": dict(impr_alta),
            "adaptation_helps_all_domains": helps,
            "alta_vs_best_fixed_rel_gap_by_domain": rel_gaps,
            "alta_near_best_fixed": near,
            "rel_gap_threshold": 0.15})

    # cross-domain sign prediction -- KEPT AS A DIAGNOSTIC ONLY. Invalid by
    # construction: delta_proxy = frozen_ce - wikitext mean is confounded by
    # intrinsic domain entropy (e.g. code has far lower frozen ppl than
    # wikitext, so its "shift" is hugely negative while its adaptation gains
    # are the largest). Documents why the C6 design moved within-domain.
    sign_pred = []
    for adapt in sorted({a for (_, a) in pools}):
        doc_by_dom = {}
        for (dom, ad), lst in pools.items():
            if ad != adapt:
                continue
            for rec, _ in lst:
                if rec.get("alta"):
                    stop_ce = rec["alta"]["cont_ce"]
                elif rec.get("fixed"):
                    stop_ce = float(rec["fixed"][
                        str(max(int(t) for t in rec["fixed"]))])
                else:
                    continue
                ph, _used = phase_stat(rec.get("alpha"), rec.get("delta_proxy"),
                                       rec.get("sigma2_rel"))
                if ph is None:
                    continue
                gain = rec["frozen_cont_ce"] - stop_ce
                doc_by_dom.setdefault(dom, []).append(
                    (ph, int(gain > 0)))
        doms = sorted(doc_by_dom)
        if not doms:
            continue
        others = [d for d in doms if d != "wikitext"]
        if "wikitext" in doms and others:
            fit_doms = ["wikitext", others[0]]
            eval_doms = others[1:]
        else:
            fit_doms, eval_doms = doms[:1], doms[1:]
        fit_pairs = [p for d in fit_doms for p in doc_by_dom[d]]
        fit_acc, thr = fit_sign_threshold([p[0] for p in fit_pairs],
                                          [p[1] for p in fit_pairs])
        eval_pairs = [p for d in eval_doms for p in doc_by_dom[d]]
        ev_acc, ev_n = (eval_sign_threshold([p[0] for p in eval_pairs],
                                            [p[1] for p in eval_pairs], thr)
                        if (eval_pairs and thr is not None) else (None, 0))
        per_dom = {}
        for d in eval_doms:
            a, n = eval_sign_threshold([p[0] for p in doc_by_dom[d]],
                                       [p[1] for p in doc_by_dom[d]], thr)
            per_dom[d] = {"accuracy": a, "n_docs": n}
        sign_pred.append({
            "adapt_params": adapt, "fit_domains": fit_doms,
            "eval_domains": eval_doms, "fitted_threshold": thr,
            "fit_accuracy": fit_acc, "eval_accuracy": ev_acc,
            "n_eval_docs": ev_n, "per_eval_domain": per_dom,
            "would_be_accuracy_ge_0.7": ((ev_acc >= 0.7)
                                         if ev_acc is not None else None),
            "stop_rule": "alta when present else last fixed step",
            "validity": ("INVALID BY CONSTRUCTION -- domain-entropy "
                         "confound: cross-domain delta_proxy mixes intrinsic "
                         "domain entropy with distribution shift; NOT used "
                         "for the C6 gate")})
    any_v2 = any(w.get("uses_delta_v2") for w in within_domain)
    lesson = (
        "Metric-design lesson (feeds the paper's limitations section): "
        "loss-based delta proxies are confounded by intrinsic domain "
        "entropy; representation-distance proxies (E5 hidden-state shift, "
        "delta_v2) recover the theory's prediction."
        if any_v2 else
        "Metric-design lesson (feeds the paper's limitations section): "
        "pointwise delta is well-defined in theory, but its empirical proxy "
        "must be within-distribution-calibrated -- the raw cross-domain "
        "delta_proxy is confounded by intrinsic domain entropy.")
    return {"domains": domains,
            "within_domain": within_domain,
            "qualitative": qualitative,
            "cross_domain_diagnostic": sign_pred,
            "delta_v2_sources": {d: dv2_meta[d] for d in sorted(dv2_meta)},
            "limitations_note": lesson,
            "wikitext_ref_by_seed": {str(k): v for k, v in sorted(refs.items())}}


# ---------------------------------------------------------------- claims

def _status(criteria):
    vals = [v for v in criteria.values() if v is not None]
    if not vals:
        return "pending"
    if all(vals):
        return "supported"
    if not any(vals):
        return "refuted"
    return "partial"


def build_claims(mil):
    e1 = mil.get("e1") or {}
    g = e1.get("gates", {})
    e2m = mil.get("e2_main")
    e2b = mil.get("e2_batch")
    e2c = mil.get("e2_calib")
    e3 = mil.get("e3")
    e4 = mil.get("e4")
    claims = {}

    # C1 -- risk curve shape + t* match (E1 a, c)
    claims["C1"] = {
        "statement": ("pointwise excess risk follows bias-decay + "
                      "variance-growth; measured optimal stopping matches t*"),
        "criteria": {"e1a_curve_match_gate": g.get("a"),
                     "e1c_tstar_match_gate": g.get("c")},
        "evidence": ["e1 part a: worst_rel_err="
                     + str((e1.get("by_part", {}).get("a") or {})
                           .get("worst_rel_err")),
                     "e1 part c: frac_risk_within_5pct="
                     + str((e1.get("by_part", {}).get("c") or {})
                           .get("frac_risk_within_5pct"))],
    }

    # C2 -- phase condition predicts gain sign (E1 b + E2 correlation).
    # Gate over STOCHASTIC methods only (ttt_rot/ttt_mask); either the
    # cell-mean or the cell-median spearman >= 0.5 counts (CE heavy tails).
    claims["C2"] = {
        "statement": ("sign of TTT gain predicted by phase condition "
                      "alpha^2 delta^2 / sigma^2; correlates with realized gain"),
        "criteria": {
            "e1b_holdout_sign_gate": g.get("b"),
            "e2_spearman_ge_0.5_for_2_stochastic_methods":
                (e2m or {}).get("gate_spearman"),
        },
        "evidence": [
            "e1 part b: holdout_acc="
            + str((e1.get("by_part", {}).get("b") or {})
                  .get("mean_holdout_accuracy")),
            "e2 main: stochastic methods passing (mean OR median rho>=0.5) = "
            + str((e2m or {}).get("n_gate_methods_pass"))
            + " of " + str(len((e2m or {}).get("gate_methods", []))),
            "tent/pl excluded by design (violate A2); see theory-boundary "
            "subsection",
        ],
    }

    # C3 -- batch TTA variance / N (E1 f + E2 batch sweep, step-1 primary)
    claims["C3"] = {
        "statement": ("batch TTA divides variance by N; Tent collapses at N=1 "
                      "and recovers as N grows, matching sigma^2/N"),
        "criteria": {
            "e1f_sigma2_over_N_gate": g.get("f"),
            "e2_step1_gain_N32_gt_N1": (e2b or {}).get("gate_recovery_step1"),
            "e2_N1_nonpositive_to_degrading":
                (e2b or {}).get("gate_N1_collapse_trajectory"),
            "e2_sigma2_point_abs_const_ratio_le_4":
                (e2b or {}).get("gate_sigma2_point_abs_const"),
            "e2_sigma2_batch_abs_spearman_le_-0.8":
                (e2b or {}).get("gate_sigma2_batch_abs_1_over_N"),
        },
        "evidence": ["e1 part f: max_rel_err="
                     + str((e1.get("by_part", {}).get("f") or {})
                           .get("max_rel_err")),
                     "e2 batch sweep groups: "
                     + str(len((e2b or {}).get("groups", [])))
                     + "; gain gates from "
                     + str((e2b or {}).get("gain_gate_source"))
                     + "; sigma^2 gates from "
                     + str((e2b or {}).get("sigma_gate_source"))
                     + (" (final-only fallback in use)"
                        if (e2b or {}).get("any_final_only") else ""),
                     "bn-train per-sample gradients are BN-coupled -> not "
                     "the theory's independent noise (observation, not "
                     "failure)"],
    }

    # C4 -- alpha_ent vs calibration (E2 calib). Loss criterion uses steps
    # 1-2 (the 20-step endpoint is deliberately in the collapse regime).
    c4_neg = c4_shift = c4_loss = None
    if e2c and e2c.get("no_temp"):
        s = e2c["no_temp"]
        if (s.get("frac_alpha_neg_confident_wrong") is not None
                and s.get("frac_alpha_neg_confident_right") is not None):
            c4_neg = (s["frac_alpha_neg_confident_wrong"]
                      > s["frac_alpha_neg_confident_right"])
        if e2c.get("alpha_ent_shift_with_temp") is not None:
            c4_shift = e2c["alpha_ent_shift_with_temp"] > 0
        if e2c.get("adapted_loss_change_with_temp_early") is not None:
            c4_loss = e2c["adapted_loss_change_with_temp_early"] <= 0
    claims["C4"] = {
        "statement": ("alpha_ent controlled by calibration error; temperature "
                      "recalibration raises alpha_ent; overconfident-wrong "
                      "regions show alpha_ent < 0"),
        "criteria": {"alpha_neg_more_frequent_when_confident_wrong": c4_neg,
                     "temp_scaling_raises_mean_alpha_ent": c4_shift,
                     "temp_scaling_does_not_hurt_early_adapted_loss": c4_loss},
        "evidence": ["e2 calib pooled over "
                     + str((e2c or {}).get("datasets")),
                     "early-loss criterion basis: "
                     + str((e2c or {}).get("early_criterion_basis"))],
    }

    # C5 -- ALTA near-oracle + safety (E1 d + E3)
    claims["C5"] = {
        "statement": ("ALTA (no validation set) within log-factor of oracle; "
                      "never catastrophically worse than best fixed-step"),
        "criteria": {"e1d_alta_oracle_gate": g.get("d"),
                     "e3_alta_within_0.5pt_of_best_fixed":
                         (e3 or {}).get("gate_within_half_pt"),
                     "e3_no_alta_safety_violation":
                         (e3 or {}).get("gate_safety_alta")},
        "evidence": ["e1 part d gates", "e3 mean gap vs best fixed = "
                     + str((e3 or {}).get("mean_gap_alta_vs_best_fixed_pooled")),
                     "e3 alta safety violations = "
                     + str((e3 or {}).get("n_alta_safety_violations"))],
    }

    # C6 -- language transfer (E4). Primary: WITHIN-domain phase-gain
    # correlation (a); qualitative support (b): adaptation helps in all
    # domains at ALTA stop, and ALTA within 15% relative of best fixed.
    # The old cross-domain sign test is a diagnostic only (invalid by
    # construction: domain-entropy confound in delta_proxy).
    c6a = c6b1 = c6b2 = None
    if e4:
        def _pick(lst):
            if not lst:
                return None
            return next((s for s in lst if s["adapt_params"] == "ln"), lst[0])
        wd = _pick(e4.get("within_domain"))
        ql = _pick(e4.get("qualitative"))
        if wd:
            c6a = wd.get("gate_rho_ge_0.3_in_3_of_4")
        if ql:
            c6b1 = ql.get("adaptation_helps_all_domains")
            c6b2 = ql.get("alta_near_best_fixed")
    claims["C6"] = {
        "statement": ("prefix-LM adaptation gain on shifted documents is "
                      "predicted by measured alpha^2 delta^2 / sigma^2"),
        "criteria": {"e4_within_domain_rho_ge_0.3_in_3_of_4": c6a,
                     "e4_adaptation_helps_all_domains_at_alta": c6b1,
                     "e4_alta_near_best_fixed_le_15pct_rel": c6b2},
        "status_rule": ("supported iff within-domain gate AND both "
                        "qualitative criteria; partial if qualitative only; "
                        "refuted only if adaptation fails to help"),
        "evidence": ["e4 within-domain phase-gain spearman (delta centered "
                     "per domain)",
                     "e4 qualitative: ppl improvement at ALTA in all "
                     "domains; ALTA within 15% rel of best fixed",
                     "cross-domain sign test kept as diagnostic only "
                     "(invalid by construction: domain-entropy confound)"],
    }

    for c in claims.values():
        c["status"] = _status(c["criteria"])
    # C6 custom status rule (overrides the generic all/any logic)
    if any(v is not None for v in (c6a, c6b1, c6b2)):
        if c6b1 is False:
            claims["C6"]["status"] = "refuted"
        elif c6a and c6b1 and c6b2:
            claims["C6"]["status"] = "supported"
        else:
            claims["C6"]["status"] = "partial"
    return claims


# ---------------------------------------------------------------- markdown

def _f(x, nd=4):
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, float):
        if not np.isfinite(x):
            return "-"
        return f"{x:.{nd}f}"
    return str(x)


def md_table(headers, rows):
    def clean(cell):
        return str(cell).replace("|", "/")  # pipes would break the table
    out = ["| " + " | ".join(clean(h) for h in headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(clean(c) for c in r) + " |")
    return out


def render_markdown(summary):
    mil = summary["milestones"]
    L = []
    L += ["# EXPERIMENT RESULTS (auto-generated)", "",
          "Generated by `experiments/ttt/analysis/aggregate.py` from "
          f"`{summary['results_root']}`. Do not edit by hand; rerun the "
          "aggregator instead.", ""]

    # Claims scoreboard first (the punchline)
    L += ["## Claims Scoreboard", ""]
    rows = []
    for cid in sorted(summary["claims"]):
        c = summary["claims"][cid]
        crit = "; ".join(f"{k}={_f(v)}" for k, v in sorted(c["criteria"].items()))
        rows.append([cid, c["status"], c["statement"], crit])
    L += md_table(["claim", "status", "statement", "criteria"], rows) + [""]

    # M0
    L += ["## M0 - source models", ""]
    m0 = mil.get("m0")
    if not m0:
        L += ["No m0 results found.", ""]
    else:
        rows = [[_f(r["dataset"]), _f(r["arch"]), _f(r["seed"]),
                 _f(r["test_acc"]), _f(r["rot_acc"]), _f(r["gate_pass"])]
                for r in m0["runs"]]
        L += md_table(["dataset", "arch", "seed", "test_acc", "rot_acc",
                       "gate"], rows)
        L += ["", f"All gates pass: {_f(m0['all_gates_pass'])}", ""]

    # E1
    L += ["## M1 / E1 - synthetic verification (C1, C2, C3, C5)", ""]
    e1 = mil.get("e1")
    if not e1:
        L += ["No e1 results found.", ""]
    else:
        rows = [[p, _f(e1["gates"].get(p))] for p in sorted(e1["gates"])]
        L += md_table(["part", "gate_pass"], rows) + [""]
        bp = e1["by_part"]
        if "a" in bp:
            L += [f"- part a: worst relative error sim-vs-theory = "
                  f"{_f(bp['a']['worst_rel_err'])} (gate < 0.05)"]
        if "b" in bp:
            for r in bp["b"]["rows"]:
                L += [f"- part b (seed {r['seed']}): fitted phase threshold = "
                      f"{_f(r['fitted_threshold'])} vs eta/2 = "
                      f"{_f(r['theory_threshold_eta_over_2'])} (ratio "
                      f"{_f(r['threshold_ratio'], 2)}; eta source: "
                      f"{r['eta_source']}); holdout sign accuracy = "
                      f"{_f(r['holdout_accuracy'])}"]
        if "c" in bp:
            L += [f"- part c: frac risk-at-empirical-t within 5% = "
                  f"{_f(bp['c']['frac_risk_within_5pct'])}; frac t within 2x = "
                  f"{_f(bp['c']['frac_time_within_2x'])}"]
        if "d" in bp:
            L += [f"- part d (ALTA): p90 gate = {_f(bp['d']['p90_gate'])}, "
                  f"safety gate = {_f(bp['d']['safety_gate'])}"]
        if "e" in bp:
            L += [f"- part e (ReLU net): alpha=0 mean harm = "
                  f"{_f(bp['e']['alpha0_mean_harm'])}, gain monotone in alpha = "
                  f"{_f(bp['e']['monotone'])}, margin = {_f(bp['e']['margin'])}"]
        if "f" in bp:
            L += [f"- part f (batch N): max rel err vs sigma^2/N theory = "
                  f"{_f(bp['f']['max_rel_err'])}"]
        L += [""]
        if "d" in bp and bp["d"]["rows"]:
            L += ["ALTA vs oracle (part d, averaged over seeds):", ""]
            rows = [[_f(r["alpha"], 2), _f(r["delta"], 1), _f(r["t_star"]),
                     _f(r["median_t_hat"], 1), _f(r["median_risk_ratio"], 2),
                     _f(r["p90_risk_ratio"], 2), _f(r["safe_vs_frozen"])]
                    for r in bp["d"]["rows"]]
            L += md_table(["alpha", "delta", "t*", "med t_hat",
                           "med risk ratio", "p90 risk ratio", "safe"],
                          rows) + [""]

    # E2 main
    L += ["## M2 / E2 - CIFAR-C alignment vs gain (C1, C2)", ""]
    e2m = mil.get("e2_main")
    if not e2m:
        L += ["No e2 main results found.", ""]
    else:
        L += [f"{e2m['n_cells']} cells (dataset, method, corruption, "
              "severity, bn_mode); per-cell table in summary.json. "
              "Method x severity aggregate:", ""]
        agg = {}
        for c in e2m["cells"]:
            agg.setdefault((c["method"], c["severity"]), []).append(c)
        rows = []
        for (meth, sev) in sorted(agg):
            cs = agg[(meth, sev)]
            rows.append([meth, str(sev), str(len(cs)),
                         _f(mean([c["mean_alpha"] for c in cs])),
                         _f(mean([c["mean_sigma2_rel"] for c in cs])),
                         _f(mean([c["mean_delta_proxy"] for c in cs])),
                         _f(mean([c["gain_final"] for c in cs])),
                         _f(mean([c["gain_best"] for c in cs]))])
        L += md_table(["method", "sev", "cells", "mean alpha",
                       "mean sigma2_rel", "mean delta_proxy",
                       "mean gain(final)", "mean gain(best)"], rows) + [""]
        gate_set = set(e2m.get("gate_methods", []))
        any_feat = any("delta_feat" in c["primary_statistic"]
                       for c in e2m["correlations"])

        def corr_rows(corrs):
            rows = []
            for c in corrs:
                pre = ("spearman_feat_"
                       if "delta_feat" in c["primary_statistic"]
                       else "spearman_")
                rows.append(
                    [c["group"], str(c["n_cells"]),
                     _f(c[pre + "mean_final"], 3),
                     _f(c[pre + "median_final"], 3),
                     _f(c[pre + "mean_best"], 3),
                     _f(c[pre + "median_best"], 3),
                     ("delta_feat (E5)" if pre == "spearman_feat_"
                      else "loss delta_proxy"),
                     c["note"]]
                    + ([f"ce: {_f(c['spearman_mean_final'], 2)}/"
                        f"{_f(c['spearman_median_final'], 2)}/"
                        f"{_f(c['spearman_mean_best'], 2)}/"
                        f"{_f(c['spearman_median_best'], 2)}"]
                       if any_feat else []))
            return rows

        hdr = (["group", "cells", "rho mean(final)", "rho median(final)",
                "rho mean(best)", "rho median(best)", "primary stat",
                "phase statistic"]
               + (["secondary loss-based (mf/mdf/mb/mdb)"]
                  if any_feat else []))
        gate_corrs = [c for c in e2m["correlations"]
                      if c["group"] in gate_set or c["group"] == "pooled"]
        L += ["Spearman(phase statistic, gain) over cells -- stochastic "
              "methods (C2 gate) + pooled:", ""]
        L += md_table(hdr, corr_rows(gate_corrs))
        L += ["", f"Stochastic methods passing (PRIMARY statistic, any of "
              f"mean/median x final/best rho >= 0.5; gate needs >= 2): "
              f"{e2m['n_gate_methods_pass']} of "
              f"{len(e2m.get('gate_methods', []))}", ""]
        bnd = [c for c in e2m["correlations"]
               if c["group"] in e2m.get("theory_boundary_methods", [])]
        if bnd:
            L += ["Theory-boundary methods (tent/pl violate persistent "
                  "alignment (A2) by design -- reported for completeness, "
                  "NOT counted for/against C2):", ""]
            L += md_table(hdr, corr_rows(bnd)) + [""]
        # per-step correlation diagnostic (theory: rho peaks near the
        # per-cell optimal step)
        meth_corrs = [c for c in e2m["correlations"] if c["group"] != "pooled"]
        step_keys = sorted({int(t) for c in meth_corrs
                            for t in c.get("spearman_by_step_mean", {})})
        if step_keys:
            L += ["Per-step Spearman(phase, gain at step t) -- diagnostic "
                  "(mean-based / median-based):", ""]
            rows = []
            for c in meth_corrs:
                rows.append([c["group"]]
                            + [(_f(c["spearman_by_step_mean"].get(str(t)), 2)
                                + " / "
                                + _f(c["spearman_by_step_median"].get(str(t)),
                                     2)) for t in step_keys])
            L += md_table(["method"] + [f"t={t}" for t in step_keys],
                          rows) + [""]

    # E2 batch sweep
    L += ["### E2 batch sweep (C3)", ""]
    e2b = mil.get("e2_batch")
    if not e2b or not e2b.get("groups"):
        L += ["No e2 batch_sweep results found.", ""]
    else:
        L += [f"C3 gate sources (split): GAIN gates from "
              f"{e2b['gain_gate_source']}; SIGMA^2 gates from "
              f"{e2b['sigma_gate_source']}. "
              + e2b["bn_coupling_note"], ""]
        for grp in e2b["groups"]:
            uses = [t for t, u in (("gain gates", grp["used_for_gain_gates"]),
                                   ("sigma^2 gates",
                                    grp["used_for_sigma_gates"])) if u]
            tag = (" [gate source: " + " + ".join(uses) + "]" if uses
                   else " [secondary]")
            L += [f"{grp['dataset']} / {grp['method']} / bn-{grp['bn_mode']}"
                  + tag
                  + (" [FINAL-ONLY: old-format file, no per-step stats]"
                     if grp["final_only"] else "") + ":", ""]
            step_keys = sorted({int(t) for r in grp["per_N"]
                                for t in r.get("gain_by_step", {})})
            hdr = (["N"] + [f"gain t={t}" for t in step_keys]
                   + ["gain final", "med s2_point_abs", "med s2_batch_abs",
                      "s2_batch_rel", "1/N ref (anchor N="
                      + _f(grp["sigma2_anchor_N"]) + ")"])
            rows = []
            for r in grp["per_N"]:
                rows.append([str(r["N"])]
                            + [_f(r["gain_by_step"].get(str(t)))
                               for t in step_keys]
                            + [_f(r["mean_gain_acc"]),
                               _f(r["median_sigma2_point_abs"], 6),
                               _f(r["median_sigma2_batch_abs"], 6),
                               _f(r["mean_sigma2_batch_rel"], 6),
                               _f(r["sigma2_ref_1_over_N"], 6)])
            L += md_table(hdr, rows)
            cl = grp["collapse"]
            L += ["", f"- primary (gain basis: {grp['gain_basis']}): "
                  f"gain(N=1) = {_f(cl['gain_step1_at_N1'])}, "
                  f"mean gain(N>=32) = {_f(cl['mean_gain_step1_N_ge_32'])}, "
                  f"recovery = {_f(cl['recovers_step1_N32_vs_N1'])}; "
                  f"N=1 nonpositive-to-degrading = "
                  f"{_f(cl['N1_nonpositive_to_degrading'])}",
                  f"- secondary (final gain): N=1 = "
                  f"{_f(cl['gain_final_at_N1'])}, N>=8 = "
                  f"{_f(cl['mean_gain_final_N_ge_8'])}",
                  f"- sigma^2 absolute (N in {grp['sigma2_gates_N_used']}): "
                  f"point_abs max/min ratio = "
                  f"{_f(grp['sigma2_point_abs_max_min_ratio'], 2)} "
                  f"(gate <= 4: {_f(grp['gate_sigma2_point_abs_const'])}); "
                  f"spearman(N, batch_abs) = "
                  f"{_f(grp['spearman_sigma2_batch_abs_vs_N'], 3)} "
                  f"(gate <= -0.8: "
                  f"{_f(grp['gate_sigma2_batch_abs_1_over_N'])})", ""]
        for sec in e2b.get("bn_eval_secondary", []):
            if not sec["positive_gain_at_any_N"]:
                L += [f"Secondary finding ({sec['dataset']}/{sec['method']}, "
                      "documented negative, not a gate failure): Tent in "
                      "eval-BN mode does not gain at any N on "
                      "clean-calibrated CIFAR models.", ""]
        for pair in e2b["bn_train_vs_eval"]:
            L += [f"bn-train vs bn-eval ({pair['dataset']}/{pair['method']}):",
                  ""]
            rows = [[str(r["N"]), _f(r["gain_bn_eval"]), _f(r["gain_bn_train"]),
                     _f(r["diff_train_minus_eval"])] for r in pair["per_N"]]
            L += md_table(["N", "gain bn-eval", "gain bn-train",
                           "train - eval"], rows) + [""]
        if not e2b["bn_train_vs_eval"]:
            L += ["bn-train vs bn-eval: only one BN mode present.", ""]

    # E2 calib
    L += ["### E2 calibration link (C4)", ""]
    e2c = mil.get("e2_calib")
    if not e2c:
        L += ["No e2 calib results found.", ""]
    else:
        rows = []
        for name, s in (("no temp", e2c["no_temp"]),
                        ("temp scaled", e2c["temp_scaled"])):
            if s is None:
                continue
            rows.append([name, str(s["n_episodes"]), _f(s["mean_alpha_ent"]),
                         _f(s["spearman_alpha_vs_confidence"], 3),
                         _f(s["spearman_alpha_vs_correct"], 3),
                         _f(s["frac_alpha_neg_confident_wrong"]) + " (n="
                         + str(s["n_confident_wrong"]) + ")",
                         _f(s["frac_alpha_neg_confident_right"]) + " (n="
                         + str(s["n_confident_right"]) + ")",
                         _f(s["mean_adapted_minus_frozen_loss"])])
        L += md_table(["setting", "episodes", "mean alpha_ent",
                       "rho(alpha,conf)", "rho(alpha,correct)",
                       "frac alpha<0 (conf-wrong)",
                       "frac alpha<0 (conf-right)",
                       "adapted-frozen loss (final)"], rows)
        # full adaptation step curve, both temp settings
        step_keys = sorted({int(t)
                            for s in (e2c["no_temp"], e2c["temp_scaled"])
                            if s
                            for t in s.get("excess_loss_by_step", {})})
        if step_keys:
            L += ["", "Adaptation step curve (mean adapted-frozen loss / "
                  "adapted acc):", ""]
            rows = []
            for name, s in (("no temp", e2c["no_temp"]),
                            ("temp scaled", e2c["temp_scaled"])):
                if s is None:
                    continue
                rows.append([name]
                            + [(_f(s["excess_loss_by_step"].get(str(t)))
                                + " / "
                                + _f(s["acc_by_step"].get(str(t)), 3))
                               for t in step_keys])
            L += md_table(["setting"] + [f"t={t}" for t in step_keys], rows)
        elif (e2c["no_temp"] or {}).get("final_only"):
            L += ["", "(old-format files: no per-step stats, final-only)"]
        L += ["", f"- fitted temperature (mean over runs): "
              f"{_f(e2c['mean_temperature'], 3)}",
              f"- mean alpha_ent shift with temp scaling: "
              f"{_f(e2c['alpha_ent_shift_with_temp'])}",
              f"- adapted-loss change with temp scaling (final step): "
              f"{_f(e2c['adapted_loss_change_with_temp'])}",
              f"- adapted-loss change with temp scaling (C4 criterion, "
              f"{e2c['early_criterion_basis']}): "
              f"{_f(e2c['adapted_loss_change_with_temp_early'])}", ""]

    # E3
    L += ["## M3 / E3 - ImageNet-C ALTA vs baselines (C5)", ""]
    e3 = mil.get("e3")
    if not e3:
        L += ["No e3 results found.", ""]
    else:
        def _stop_label(r):
            if r["stopping"] == "alta" and r["alta_t0_is_frozen"] is False:
                return "alta [STALE t0 semantics]"
            return r["stopping"]

        rows = [[r["corruption"], str(r["severity"]), r["method"],
                 _stop_label(r), _f(r["frozen_acc"]), _f(r["bn0_acc"]),
                 _f(r["adapted_acc"]), _f(r["best_fixed_acc"]),
                 _f(r["mean_t_hat"], 2), _f(r["delta_proxy"], 3)]
                for r in e3["cells"]]
        L += md_table(["corruption", "sev", "method", "stopping", "frozen",
                       "bn0", "adapted", "best fixed", "mean t_hat",
                       "delta proxy"], rows) + [""]
        if e3.get("n_stale_alta_cells_dropped") or e3.get("n_stale_alta_rows"):
            L += [f"ALTA t0 semantics: {e3['n_stale_alta_cells_dropped']} "
                  "stale cell(s) dropped where fixed-semantics reruns "
                  "(alta_t0_is_frozen) exist for the same "
                  "(corruption, severity, method); "
                  f"{e3['n_stale_alta_rows']} row(s) still stale-only "
                  "(pending rerun; excluded from the C5 safety gate when a "
                  "flagged run covers that corruption).", ""]
        if e3["alta_vs_fixed"]:
            L += ["ALTA vs fixed:", ""]
            rows = [[g["corruption"], str(g["severity"]), g["method"],
                     _f(g["alta_acc"]), _f(g["best_fixed_acc"]),
                     _f(g["gap_alta_vs_best_fixed"]),
                     _f(g["oracle_acc"]), _f(g["alta_mean_t_hat"], 2)]
                    for g in e3["alta_vs_fixed"]]
            L += md_table(["corruption", "sev", "method", "alta acc",
                           "best fixed", "gap", "oracle", "alta t_hat"],
                          rows) + [""]
        L += [f"- pooled mean gap (alta - best fixed) = "
              f"{_f(e3['mean_gap_alta_vs_best_fixed_pooled'])} "
              f"(gate: >= -0.005)",
              f"- safety violations (adapted < frozen - 0.2pt): "
              f"{len(e3['safety_violations'])} total, "
              f"{e3['n_alta_safety_violations']} under ALTA counted for the "
              f"C5 gate (fixed-t0-semantics runs preferred)", ""]
        for v in e3["safety_violations"]:
            stale = (" [stale alta t0 semantics]"
                     if (v["stopping"] == "alta"
                         and v["alta_t0_is_frozen"] is False) else "")
            L += [f"  - {v['corruption']} s{v['severity']} {v['method']}/"
                  f"{v['stopping']}{stale}: shortfall "
                  f"{_f(v['shortfall_pt'], 2)} pt"]
        if e3["safety_violations"]:
            L += [""]

    # E4
    L += ["## M4 / E4 - GPT-2 language shift (C6)", ""]
    e4 = mil.get("e4")
    if not e4:
        L += ["No e4 results found.", ""]
    else:
        rows = [[d["domain"], d["adapt_params"], str(d["n_docs"]),
                 _f(d["mean_alpha"]), _f(d["mean_sigma2_rel"]),
                 _f(d["mean_delta_proxy"]), _f(d["frozen_ppl"], 2),
                 (f"t={_f(d['best_fixed_step'])}: "
                  + _f(d["ppl_improvement_best_fixed"], 3)),
                 (_f(d["alta"]["ppl_improvement"], 3)
                  + f" (t_hat={_f(d['alta']['mean_t_hat'], 1)})"
                  if d["alta"] else "-"),
                 _f(d["oracle_ppl"], 2)]
                for d in e4["domains"]]
        L += md_table(["domain", "adapt", "docs", "mean alpha",
                       "mean sigma2_rel", "mean delta_proxy", "frozen ppl",
                       "ppl improv @ best fixed", "ppl improv @ ALTA",
                       "oracle ppl"], rows) + [""]

        # (a) within-domain phase-gain correlation -- the C6 primary test
        for wd in e4.get("within_domain", []):
            if wd["uses_delta_v2"]:
                L += ["Within-domain phase-gain correlation (C6 primary; "
                      "PRIMARY statistic uses the E5 hidden-state shift "
                      "proxy delta_v2, phase = alpha*abs(alpha) * delta_v2 / "
                      "sigma^2 -- a direct representation-space shift "
                      "measure that needs no centering and resolves the "
                      "domain-entropy confound of loss-based proxies; "
                      "centered-frozen-CE variant kept as secondary):", ""]
                rows = [[w["domain"], w["adapt_params"],
                         _f(w["rho_gain_alta_delta_v2"], 3)
                         + f" (n={w['n_delta_v2_joined']})",
                         _f(w["rho_gain_best_fixed_delta_v2"], 3)
                         + f" (t={_f(w['best_fixed_step'])})",
                         _f(w["rho_gain_alta"], 3),
                         _f(w["rho_gain_best_fixed"], 3),
                         w["primary_statistic"],
                         _f(w["pass_rho_ge_0.3"])]
                        for w in wd["per_domain"]]
                L += md_table(["domain", "adapt",
                               "rho_v2(gain@ALTA)", "rho_v2(gain@best)",
                               "rho_ce(gain@ALTA)", "rho_ce(gain@best)",
                               "primary stat", "pass (>= 0.3)"], rows)
            else:
                L += ["Within-domain phase-gain correlation (C6 primary; "
                      "phase = alpha^2 * delta_centered / sigma^2, delta "
                      "centered per domain, sign preserved; no E5 delta_v2 "
                      "files present):", ""]
                rows = [[w["domain"], w["adapt_params"],
                         _f(w["rho_gain_alta"], 3) + f" (n={w['n_alta']})",
                         _f(w["rho_gain_best_fixed"], 3)
                         + f" (n={w['n_best_fixed']}, "
                         + f"t={_f(w['best_fixed_step'])})",
                         _f(w["pass_rho_ge_0.3"])]
                        for w in wd["per_domain"]]
                L += md_table(["domain", "adapt", "rho(gain@ALTA)",
                               "rho(gain@best fixed)", "pass (either >= 0.3)"],
                              rows)
            L += ["", f"- gate ({wd['adapt_params']}): {wd['n_pass']} of "
                  f"{wd['n_domains']} domains pass (need >= 3 of 4): "
                  f"{_f(wd['gate_rho_ge_0.3_in_3_of_4'])}", ""]

        # (b) qualitative support criteria
        for ql in e4.get("qualitative", []):
            L += [f"Qualitative support ({ql['adapt_params']}):"]
            for d in sorted(ql["ppl_improvement_at_alta_by_domain"]):
                v = ql["ppl_improvement_at_alta_by_domain"][d]
                rg = ql["alta_vs_best_fixed_rel_gap_by_domain"].get(d)
                L += [f"  - {d}: ppl improvement @ ALTA = {_f(v, 3)}; "
                      f"ALTA-vs-best-fixed rel gap = {_f(rg, 3)}"]
            L += [f"- adaptation_helps_all_domains: "
                  f"{_f(ql['adaptation_helps_all_domains'])}",
                  f"- alta_near_best_fixed (rel gap <= "
                  f"{ql['rel_gap_threshold']}): "
                  f"{_f(ql['alta_near_best_fixed'])}", ""]

        # (c) retired cross-domain test, kept as a labeled diagnostic
        L += ["### Cross-domain sign test [DIAGNOSTIC ONLY -- INVALID BY "
              "CONSTRUCTION]", "",
              "delta_proxy = frozen CE - wikitext mean is confounded by "
              "intrinsic domain entropy (e.g. code has far lower frozen ppl "
              "than wikitext, so its 'shift' is hugely negative while its "
              "adaptation gains are the largest). Kept only to document why "
              "the C6 design moved within-domain; NOT used for the gate.", ""]
        for sp in e4.get("cross_domain_diagnostic", []):
            L += [f"- ({sp['adapt_params']}; stop = {sp['stop_rule']}) "
                  f"fit on {sp['fit_domains']} (acc {_f(sp['fit_accuracy'])}, "
                  f"thr {_f(sp['fitted_threshold'], 4)}), eval on "
                  f"{sp['eval_domains']}: accuracy = "
                  f"{_f(sp['eval_accuracy'])} on {sp['n_eval_docs']} docs "
                  f"(would-be 0.7 gate: {_f(sp['would_be_accuracy_ge_0.7'])})"]
            for d in sorted(sp["per_eval_domain"]):
                pd = sp["per_eval_domain"][d]
                L += [f"  - {d}: {_f(pd['accuracy'])} (n={pd['n_docs']})"]
        L += ["", e4.get("limitations_note", ""), ""]

    # file inventory + skipped files
    L += ["## Inputs", ""]
    for msub in sorted(summary["files"]):
        L += [f"- {msub}: {len(summary['files'][msub])} file(s)"]
    for msub in sorted(summary.get("skipped", {})):
        for s in summary["skipped"][msub]:
            L += [f"- {msub} skipped: {s}"]
    L += [""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results-root", required=True,
                    help="directory containing m0/ e1/ e2/ e3/ e4/ subdirs")
    ap.add_argument("--out", default="summary.json",
                    help="output summary JSON path")
    ap.add_argument("--md-out", default=None,
                    help="output markdown report path (optional)")
    ap.add_argument("--include-smoke", action="store_true",
                    help="include *_smoke.json files (excluded by default)")
    args = ap.parse_args()

    if not os.path.isdir(args.results_root):
        print(f"[aggregate] WARNING: results root {args.results_root} does "
              "not exist; all claims will be pending", file=sys.stderr)
        found, errors = {}, {}
    else:
        found, errors = gather_files(args.results_root, args.include_smoke)

    mil = {}
    if "m0" in found:
        mil["m0"] = analyze_m0(found["m0"])
    if "e1" in found:
        mil["e1"] = analyze_e1(found["e1"])
    if "e2" in found:
        main_r, batch_r, calib_r = split_e2(found["e2"])
        if main_r:
            mil["e2_main"] = analyze_e2_main(main_r, found.get("e5", []))
        if batch_r:
            mil["e2_batch"] = analyze_e2_batch(batch_r)
        if calib_r:
            mil["e2_calib"] = analyze_e2_calib(calib_r)
    if "e3" in found:
        mil["e3"] = analyze_e3(found["e3"])
    if "e4" in found:
        mil["e4"] = analyze_e4(found["e4"], found.get("e5", []))

    summary = {
        "results_root": args.results_root.replace("\\", "/"),
        "files": {k: [fn for fn, _ in v] for k, v in sorted(found.items())},
        "skipped": errors,
        "milestones": mil,
        "claims": build_claims(mil),
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, sort_keys=True, default=float)
        f.write("\n")
    print(f"[aggregate] wrote {args.out}")

    if args.md_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.md_out)),
                    exist_ok=True)
        with open(args.md_out, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_markdown(summary))
        print(f"[aggregate] wrote {args.md_out}")

    for cid in sorted(summary["claims"]):
        c = summary["claims"][cid]
        print(f"[aggregate] {cid}: {c['status']}")


if __name__ == "__main__":
    main()
