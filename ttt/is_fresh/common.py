"""Shared helpers for the IS-retarget fresh-measurement suite (is_fresh).

Design rules enforced across every script in this package:

1. NOTHING is scored with the paper's own closed forms. Closed forms are
   imported only as a *reference curve* for a documented reproduction check
   whose tolerance is stated in the script; they never define a headline
   number.
2. Every random number comes from a seed in the 20260801+ range. The seeds
   used by the original pipeline (0, 1, 2, 42, 43, 100+, 999+) are never
   reused.
3. Wherever a step / threshold / stopping time is chosen from noisy data, it
   is chosen on one disjoint block of replicates (or cells) and *scored* on
   another. Nothing is selected and evaluated on the same sample.
4. Every headline number is reported as mean +- range over >= 5 independent
   seeds.

The stochastic machinery (`simulate_scalar`) and the ALTA implementation are
imported unchanged from the original pipeline
(`experiments/ttt/e1_synthetic/run_e1.py`, `experiments/ttt/core/alta.py`).
"""
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_TTT = os.path.dirname(_HERE)                      # <root>/ttt
for _p in (_TTT, os.path.join(_TTT, "e1_synthetic")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_e1 as ORIG            # noqa: E402  (original E1 pipeline code)
from core.alta import ALTAConfig, alta_run  # noqa: E402,F401

# ---- fresh seeds (20260801+; disjoint from every seed in the original code)
SEEDS = [20260801, 20260802, 20260803, 20260804, 20260805]
SEEDS7 = SEEDS + [20260806, 20260807]

# ---- model constants, kept identical to the original E1 protocol so the
#      fresh numbers are drop-in replacements for the published ones
ETA = ORIG.ETA          # 0.05
SIGMA = ORIG.SIGMA      # 1.0
T = ORIG.T              # 400
ALPHAS = list(ORIG.ALPHAS)
RATIOS = list(ORIG.RATIOS)

simulate_scalar = ORIG.simulate_scalar
excess_risk = ORIG.excess_risk
mean_u = ORIG.mean_u
var_u = ORIG.var_u
t_star_theory = ORIG.t_star_theory

RESULTS_DIR = os.path.abspath(
    os.path.join(_TTT, "..", "results", "is_fresh"))

# Repository root: <REPO>/experiments/ttt/is_fresh/common.py.  Result records
# must never carry a build-machine absolute path -- an extracted archive would
# then contain strings that resolve nowhere and appear to demand editing.
# Provenance fields are written through `rel()` instead.
REPO_DIR = os.path.abspath(os.path.join(_TTT, ".."))


def rel(path):
    """Repository-relative POSIX form of `path`, for provenance fields.

    Falls back to the basename-anchored tail if `path` lies outside the
    repository, so the function can never leak a machine-specific prefix.
    """
    p = os.path.abspath(path)
    try:
        r = os.path.relpath(p, REPO_DIR)
    except ValueError:                      # different drive on Windows
        return os.path.basename(p)
    r = r.replace("\\", "/")
    return os.path.basename(p) if r.startswith("../") else r


def save(obj, name):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=_default)
    # The console line is archived as a run log, so it must not carry the
    # build machine's absolute prefix either; `rel()` is the same guard the
    # provenance fields use.
    print(f"[is_fresh] wrote {rel(path)}", flush=True)
    return path


def _default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def fit_sign_threshold(phase, label):
    """1-D threshold rule pred = (phase > thr), scanning every split point.

    Identical decision rule to the original `run_e1.part_b.fit_thr`, so the
    fresh number is comparable to the published one; the difference is that
    `label` here is a MEASURED sign, not a closed-form one.
    Returns (best_accuracy, threshold).
    """
    ph = np.asarray(phase, float)
    lb = np.asarray(label, int)
    order = np.argsort(ph, kind="stable")
    ph_s, lb_s = ph[order], lb[order]
    n = len(ph_s)
    # pred for split k: first k predicted 0, rest predicted 1
    # correct = (#zeros in first k) + (#ones in last n-k)
    ones_suffix = np.concatenate([np.cumsum(lb_s[::-1])[::-1], [0]])
    zeros_prefix = np.concatenate([[0], np.cumsum(1 - lb_s)])
    correct = zeros_prefix + ones_suffix
    k = int(np.argmax(correct))
    acc = float(correct[k]) / n
    thr = float(ph_s[k - 1]) if k > 0 else 0.0
    return acc, thr


def eval_sign_threshold(phase, label, thr):
    ph = np.asarray(phase, float)
    lb = np.asarray(label, int)
    pred = (ph > thr).astype(int)
    return float((pred == lb).mean()), int(len(ph))


def mean_range(vals):
    """{'mean':..,'min':..,'max':..,'n':..,'values':[..]} over seeds."""
    v = [float(x) for x in vals if x is not None and np.isfinite(float(x))]
    if not v:
        return None
    return {"mean": float(np.mean(v)), "min": float(np.min(v)),
            "max": float(np.max(v)), "n": len(v), "values": v}


def se_of_mean_square(x):
    """Standard error of mean(x**2) for a 1-D replicate sample."""
    x2 = np.asarray(x, float) ** 2
    return float(x2.std(ddof=1) / np.sqrt(len(x2)))
