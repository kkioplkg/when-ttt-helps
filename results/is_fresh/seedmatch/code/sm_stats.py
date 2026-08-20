#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Statistics helpers for the seed-matched experiment.

`rank` and `spearman` are PORTED VERBATIM from `is_fresh/f8_e2_crossfit.py`
(and the identical copy in `f14_deltafeat_check.py`) so that every number this
package prints is computed by the same tie-handling and NaN-masking rules as
the published ones.  `sm_equivalence.py` proves the port by recomputing f14's
published outputs with these functions and requiring exact agreement.

The paired-bootstrap helper is NOT ported, because the published scripts have
no paired analogue: they bootstrap one arm at a time.  The design review's
correction is implemented here instead -- one corruption resample is drawn per
replicate and applied, with multiplicities, to BOTH arms.
"""
import numpy as np


def rank(a):
    """Average ranks with tie handling. Ported from f8_e2_crossfit.py:_rank."""
    a = np.asarray(a, float)
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    vals, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(vals))
    np.add.at(sums, inv, ranks)
    return sums[inv] / cnt[inv]


def spearman(x, y):
    """Ported from f8_e2_crossfit.py:spearman. Returns None where it returns None."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return None
    rx, ry = rank(x), rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def describe(vals, name=""):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if v.size == 0:
        return {"name": name, "n": 0}
    return {
        "name": name, "n": int(v.size),
        "mean": float(v.mean()), "median": float(np.median(v)),
        "sd": float(v.std(ddof=1)) if v.size > 1 else 0.0,
        "q10": float(np.percentile(v, 10)), "q25": float(np.percentile(v, 25)),
        "q75": float(np.percentile(v, 75)), "q90": float(np.percentile(v, 90)),
        "min": float(v.min()), "max": float(v.max()),
        "frac_positive": float((v > 0).mean()),
        "mean_abs": float(np.abs(v).mean()),
    }


def paired_cluster_bootstrap(rows, stat_fn, n_boot=1000, seed=20260801,
                             cluster_key="corruption"):
    """Interval for a PAIRED statistic under a COMMON cluster resample.

    `rows` are per-unit records carrying everything both arms need.  Each
    replicate draws ONE resample of the clusters with replacement and passes
    the SAME resampled row list -- multiplicities included -- to `stat_fn`,
    which returns the paired difference.  Both arms therefore see identical
    resampled benchmarks in every replicate, which is what preserves the
    pairing; bootstrapping the arms separately would not.

    The interval is robustness with respect to CORRUPTION COMPOSITION,
    conditional on the realized networks.  It is not uncertainty over network
    draws and must never be described as such.
    """
    by = {}
    for r in rows:
        by.setdefault(r[cluster_key], []).append(r)
    keys = sorted(by)
    if len(keys) < 3:
        return None
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        sub = [r for i in pick for r in by[keys[i]]]
        v = stat_fn(sub)
        if v is not None and np.isfinite(v):
            vals.append(float(v))
    if len(vals) < 50:
        return None
    v = np.asarray(vals)
    return {"lo": float(np.percentile(v, 2.5)),
            "hi": float(np.percentile(v, 97.5)),
            "mean": float(v.mean()), "n_boot": len(vals),
            "cluster": cluster_key, "n_clusters": len(keys),
            "interpretation": ("robustness w.r.t. corruption composition, "
                               "conditional on the realized networks; NOT "
                               "uncertainty over network draws")}


def loco(rows, stat_fn, cluster_key="corruption"):
    """Leave-one-cluster-out values of a paired statistic.

    Reported alongside the bootstrap because with only 15 corruption clusters a
    bootstrap interval alone can conceal a leverage problem: if deleting one
    corruption flips the sign or supplies most of the effect, that is the fact
    a reader needs and the interval hides it.
    """
    keys = sorted({r[cluster_key] for r in rows})
    out = {}
    for k in keys:
        sub = [r for r in rows if r[cluster_key] != k]
        v = stat_fn(sub)
        out[k] = None if v is None else float(v)
    vv = [v for v in out.values() if v is not None]
    full = stat_fn(rows)
    return {"per_cluster": out,
            "full": None if full is None else float(full),
            "min": float(np.min(vv)) if vv else None,
            "max": float(np.max(vv)) if vv else None,
            "max_abs_deviation_from_full": (
                float(np.max(np.abs(np.asarray(vv) - full)))
                if vv and full is not None else None),
            "sign_flips": (int(sum(1 for v in vv if full is not None
                                   and v * full < 0)) if full is not None else None)}


def weighted_panel(values, cell_ids):
    """Equal-cell-weighted mean, SD and empirical CDF over a reference panel.

    Every measurement network is scored on exactly the same (corruption,
    severity, idx) tuples, but cells differ in size, so cells are weighted
    equally rather than observations.  Standardisation is at network x dataset
    level and deliberately NOT within cell: standardising within cell would
    delete the between-cell signal the downstream analysis exists to exploit.
    """
    values = np.asarray(values, float)
    cells = np.asarray(cell_ids)
    uniq = np.unique(cells)
    w = np.zeros(len(values))
    for c in uniq:
        msk = cells == c
        w[msk] = 1.0 / (len(uniq) * msk.sum())
    mu = float((w * values).sum())
    var = float((w * (values - mu) ** 2).sum())
    sd = float(np.sqrt(max(var, 0.0)))
    order = np.argsort(values, kind="stable")
    return {"mu": mu, "sd": sd,
            "grid": values[order].tolist(), "cdf": np.cumsum(w[order]).tolist()}


def panel_q(panel, x):
    """Weighted empirical CDF value F_m(x): the rank-calibrated coordinate.

    Removes ANY strictly monotone per-network recalibration, not merely an
    affine one, which is what a genuinely rank-based objection is entitled to.
    """
    g = np.asarray(panel["grid"], float)
    c = np.asarray(panel["cdf"], float)
    return np.interp(np.asarray(x, float), g, c, left=0.0, right=1.0)
