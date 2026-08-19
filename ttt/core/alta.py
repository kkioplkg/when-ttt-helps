"""ALTA: Aligned Local Test-time Adaptation — Lepski-type adaptive stopping.

Implements THEORY_CORE.md §5. Model-agnostic: the caller supplies K step
functions; step_fns[k]() advances replica k by one SSL-SGD step and returns the
current prediction (logits / scalar vector) at x*.

Deployment semantics: ALTA's OUTPUT is the
recorded mean-replica prediction at the stopping step t_hat (`pred_at_t_hat`),
taken from the trajectory history — no parameter rollback is needed in the
episodic protocol (the model is reset after each test point anyway). t_hat = 0
("do not adapt", output = pred0) is a valid outcome.

Defaults (single source of truth, mirrored in THEORY_CORE.md §6):
K = 3 replicas, kappa = 1.5, window w = 3.
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class ALTAConfig:
    K: int = 3
    kappa: float = 1.5
    window: int = 3
    T_max: int = 50


@dataclass
class ALTATrace:
    mean_preds: list = field(default_factory=list)   # index t: p̄_t, t = 0..t_stop
    dispersion: list = field(default_factory=list)   # index t: ŝ(t), ŝ(0) = 0
    drift: list = field(default_factory=list)        # EMA drift, index from t=1
    t_hat: int = -1
    pred_at_t_hat: np.ndarray = None


def alta_run(step_fns, cfg: ALTAConfig, pred0: np.ndarray = None):
    """ALTA v3 — offline Lepski scan (provable form, Theorem 5).

    1. Run K replicas for T_max steps, recording mean prediction p_t and
       replica dispersion s(t) for every t.
    2. t is ADMISSIBLE iff for every u > t:
           ||p_u - p_t|| <= kappa * (s(u) + s(t)) + eps,   eps = 1e-12
       (all later trajectory positions are within the noise confidence band of
       position t — i.e. no detectable signal drift remains after t).
       The eps is a floating-point tolerance so that an inequality satisfied
       exactly is not lost to rounding; it is written into the rule here, and
       into the supplement's specification of it, because a docstring giving
       the literal inequality while the code below adds eps documents a
       different selector from the one that produced the published runs.
    3. t_hat = smallest admissible t; output = recorded mean prediction at
       t_hat. t_hat = 0 ("do not adapt") requires pred0.

    Runs the full horizon (compute is K*T_max regardless); the point of ALTA is
    label-free SELECTION, not compute saving. Forward-scan early-stop variants
    fire prematurely in the damped (alpha -> 1) regime — verified empirically.
    """
    assert len(step_fns) == cfg.K
    tr = ALTATrace()
    offset = 0
    if pred0 is not None:
        tr.mean_preds.append(np.asarray(pred0, dtype=float))
        tr.dispersion.append(0.0)
    else:
        offset = 1
    for t in range(1, cfg.T_max + 1):
        preds = np.stack([np.asarray(fn(), dtype=float) for fn in step_fns])
        mean_p = preds.mean(axis=0)
        s_t = float(np.sqrt(((preds - mean_p) ** 2).sum(axis=1).mean()))
        tr.mean_preds.append(mean_p)
        tr.dispersion.append(s_t)
        if len(tr.mean_preds) >= 2:
            tr.drift.append(float(np.linalg.norm(mean_p - tr.mean_preds[-2])))
    P = np.stack(tr.mean_preds)            # (n, out_dim), index i = step i+offset
    S = np.asarray(tr.dispersion)
    n = len(P)
    t_hat_idx = n - 1
    for i in range(n):
        diffs = np.linalg.norm(P[i + 1:] - P[i], axis=1)
        bands = cfg.kappa * (S[i + 1:] + S[i])
        if np.all(diffs <= bands + 1e-12):
            t_hat_idx = i
            break
    tr.t_hat = t_hat_idx + offset
    tr.pred_at_t_hat = P[t_hat_idx]
    return tr


def snr_stop(grad_cos_seq, tau=0.1, window=3):
    """Cheap K=1 fallback: stop when cos(g_t, EMA(g)) stays below tau."""
    ema = None
    consec = 0
    for t, c in enumerate(grad_cos_seq, start=1):
        ema = c if ema is None else 0.7 * ema + 0.3 * c
        if ema < tau:
            consec += 1
            if consec >= window:
                return max(t - window, 0)
        else:
            consec = 0
    return len(grad_cos_seq)
