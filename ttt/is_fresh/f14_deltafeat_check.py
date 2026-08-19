"""F14 -- is delta_feat monotone in the actual shift level?

THE PROBLEM
The feature-distance variable is an unvalidated proxy for delta^2.  Calling it
an estimate "up to an unknown monotone transform" assumes precisely the
monotonic relationship required to interpret its Spearman correlation.  Absent
that validation it is only a heuristic representation-distance diagnostic, and
it has to be checked against an offline labelled risk quantity.

That validation is possible from records that already exist, because CIFAR-10-C
ships an ORDERED, externally-defined shift level -- the corruption severity
1..5 -- and the E2 episode records carry a LABELLED offline risk quantity for
every episode: the frozen model's cross-entropy on the true label, and whether
the frozen prediction is correct.  Neither was used to build delta_feat
(delta_feat is the cosine distance of a test image's feature to the clean-test
feature mean; no labels enter it), so both are legitimate external yardsticks.

WHAT THIS SCRIPT MEASURES (no new runs; original records only)
  results/e5/delta_feat_{dataset}_{arch}.json    per (corruption, severity, idx)
  results/e2/*_main_*.json                       per-episode frozen_loss,
                                                 frozen_correct, delta_proxy

  (A) SEVERITY MONOTONICITY.  Within each (dataset, arch, corruption), the
      Spearman rank correlation between severity and the per-severity mean
      delta_feat, plus a strict-monotonicity flag (mean delta_feat increasing
      at all five severities) and the episode-level Spearman over all
      severities pooled.  A proxy that is monotone in shift must rank the five
      severities of a corruption correctly; if it does not, "up to an unknown
      monotone transform" is not available as a defence.

  (B) LABELLED-RISK MONOTONICITY.  Spearman between delta_feat and the frozen
      model's labelled excess risk, at two levels:
        cell level     mean delta_feat vs mean frozen cross-entropy over the
                       (dataset, method, corruption, severity) cell, and vs
                       the frozen error rate of that cell;
        episode level  per-episode delta_feat vs per-episode frozen loss,
                       computed WITHIN each cell so that between-cell
                       difficulty cannot manufacture the correlation.
      The within-cell version is the demanding one: it asks whether, among
      images that share a corruption and a severity, the ones further from the
      clean feature mean are the ones the frozen model actually does worse on.

  (C) A REFERENCE BASELINE: the same two correlations for
      the LOSS proxy delta_proxy = frozen_loss - clean_ref, which is monotone
      in the labelled risk by construction (it IS a monotone function of the
      frozen loss).  It is reported so the delta_feat numbers are read against
      something whose value is known a priori rather than against nothing.

OUTPUTS a per-corruption table, per-arch aggregates, and three headline counts:
how many (dataset, arch, corruption) triples have delta_feat strictly
increasing in severity, how many have severity-Spearman = +1, and the
distribution of within-cell delta_feat/frozen-loss correlations.

REPRODUCTION CHECK (asserted)
The loss proxy delta_proxy must correlate with the frozen loss at Spearman
+1.000 within every cell (it is frozen_loss minus a per-run constant).  If that
identity does not come out of the join, the records are not being paired
correctly and no other number in this file can be trusted.
"""
import argparse
import glob
import json
import os
import re

import numpy as np

import common as C

E2_DIR = os.path.join(os.path.dirname(C.RESULTS_DIR), "e2")
E5_DIR = os.path.join(os.path.dirname(C.RESULTS_DIR), "e5")
METHOD_ARCH = {"ttt_rot": "resnet26ttt", "ttt_mask": "resnet26ttt",
               "tent": "wrn2810", "pl": "wrn2810"}


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return None

    def rk(a):
        o = np.argsort(a, kind="stable")
        r = np.empty(len(a), float)
        r[o] = np.arange(1, len(a) + 1, dtype=float)
        _, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
        s = np.zeros(len(cnt))
        np.add.at(s, inv, r)
        return s[inv] / cnt[inv]

    rx, ry = rk(x), rk(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def load_delta_feat():
    out = {}
    for p in sorted(glob.glob(os.path.join(E5_DIR, "delta_feat_*.json"))):
        m = re.match(r"delta_feat_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.json$",
                     os.path.basename(p))
        o = json.loads(open(p, encoding="utf-8").read())
        key = (o.get("dataset", m.group(1)), o.get("arch", m.group(2)))
        out[key] = o["records"]
    return out


def load_e2_episodes():
    """[(dataset, method, corruption, severity, idx, frozen_loss,
         frozen_correct, delta_proxy), ...] from the bn-eval `main` runs."""
    rows = []
    for fn in sorted(os.listdir(E2_DIR)):
        if not fn.endswith(".json"):
            continue
        o = json.loads(open(os.path.join(E2_DIR, fn), encoding="utf-8").read())
        argv = o.get("meta", {}).get("argv", {})
        if argv.get("mode", "main") != "main":
            continue
        ds, meth = argv["dataset"], argv["method"]
        for cell in o.get("results", []):
            corr, sev = cell["corruption"], int(cell["severity"])
            for e in cell.get("episodes", []):
                if e.get("idx") is None:
                    continue
                rows.append({
                    "src": fn,
                    "dataset": ds, "method": meth, "arch": METHOD_ARCH[meth],
                    "corruption": corr, "severity": sev, "idx": int(e["idx"]),
                    "frozen_loss": float(e["frozen_loss"]),
                    "frozen_correct": int(e.get("frozen_correct", 0)),
                    "delta_proxy": (float(e["delta_proxy"])
                                    if e.get("delta_proxy") is not None
                                    else np.nan)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()

    dfeat = load_delta_feat()
    eps = load_e2_episodes()
    assert dfeat and eps, "delta_feat or E2 episode records missing"

    # ---------------------------------------------------------------- (A)
    per_corruption = []
    for (ds, arch), recs in sorted(dfeat.items()):
        by = {}
        for r in recs:
            by.setdefault(r["corruption"], {}).setdefault(
                int(r["severity"]), []).append(float(r["delta_feat"]))
        for corr in sorted(by):
            sevs = sorted(by[corr])
            means = [float(np.mean(by[corr][s])) for s in sevs]
            meds = [float(np.median(by[corr][s])) for s in sevs]
            allv = [v for s in sevs for v in by[corr][s]]
            alls = [s for s in sevs for _ in by[corr][s]]
            per_corruption.append({
                "dataset": ds, "arch": arch, "corruption": corr,
                "severities": sevs,
                "mean_delta_feat_by_severity": means,
                "median_delta_feat_by_severity": meds,
                "rho_severity_vs_mean": spearman(sevs, means),
                "rho_severity_vs_episode": spearman(alls, allv),
                "strictly_increasing_mean": bool(
                    all(b > a for a, b in zip(means, means[1:]))),
                "n_episodes": len(allv),
            })

    n_tot = len(per_corruption)
    n_strict = sum(1 for r in per_corruption if r["strictly_increasing_mean"])
    n_rho1 = sum(1 for r in per_corruption
                 if r["rho_severity_vs_mean"] is not None
                 and r["rho_severity_vs_mean"] > 0.999)
    rho_ep = [r["rho_severity_vs_episode"] for r in per_corruption
              if r["rho_severity_vs_episode"] is not None]

    # ---------------------------------------------------------------- (B)
    fmap = {(ds, arch): {(r["corruption"], int(r["severity"]), int(r["idx"])):
                         float(r["delta_feat"]) for r in recs}
            for (ds, arch), recs in dfeat.items()}
    cells = {}
    for e in eps:
        d = fmap.get((e["dataset"], e["arch"]), {}).get(
            (e["corruption"], e["severity"], e["idx"]))
        if d is None:
            continue
        key = (e["dataset"], e["method"], e["corruption"], e["severity"])
        cells.setdefault(key, []).append({**e, "delta_feat": d})

    # ---- reproduction check, grouped by SOURCE RUN.  delta_proxy subtracts a
    # per-run constant (clean_ref), so it is rank-identical to frozen_loss
    # within one run's cell but not across runs pooled into the same cell.
    within_loss_proxy, repro_bad = [], []
    runcells = {}
    for key, rows in cells.items():
        for r in rows:
            runcells.setdefault((r["src"],) + key, []).append(r)
    for rkey, rows in sorted(runcells.items()):
        rp = spearman([r["delta_proxy"] for r in rows],
                      [r["frozen_loss"] for r in rows])
        if rp is None:
            continue
        within_loss_proxy.append(rp)
        if rp < 0.999:
            repro_bad.append((rkey, rp))

    within_feat, cell_rows = [], []
    for key, rows in sorted(cells.items()):
        df = [r["delta_feat"] for r in rows]
        fl = [r["frozen_loss"] for r in rows]
        rf = spearman(df, fl)
        if rf is not None:
            within_feat.append(rf)
        cell_rows.append({
            "dataset": key[0], "method": key[1], "corruption": key[2],
            "severity": key[3], "n": len(rows),
            "mean_delta_feat": float(np.mean(df)),
            "mean_frozen_loss": float(np.mean(fl)),
            "frozen_error_rate": float(
                1.0 - np.mean([r["frozen_correct"] for r in rows])),
            "within_cell_rho_delta_feat_vs_frozen_loss": rf,
        })

    assert not repro_bad, (
        "delta_proxy is not a monotone function of frozen_loss within "
        f"{len(repro_bad)} single-run cells (e.g. {repro_bad[0]}); the "
        "episode join is wrong and no correlation in this file is "
        "interpretable")

    by_method = {}
    for r in cell_rows:
        by_method.setdefault(r["method"], []).append(r)
    cell_level = {}
    for meth, rs in sorted(by_method.items()):
        cell_level[meth] = {
            "n_cells": len(rs),
            "arch": METHOD_ARCH[meth],
            "rho_mean_delta_feat_vs_mean_frozen_loss": spearman(
                [r["mean_delta_feat"] for r in rs],
                [r["mean_frozen_loss"] for r in rs]),
            "rho_mean_delta_feat_vs_frozen_error_rate": spearman(
                [r["mean_delta_feat"] for r in rs],
                [r["frozen_error_rate"] for r in rs]),
            "rho_mean_delta_feat_vs_severity": spearman(
                [r["mean_delta_feat"] for r in rs],
                [r["severity"] for r in rs]),
            "median_within_cell_rho": float(np.median(
                [r["within_cell_rho_delta_feat_vs_frozen_loss"] for r in rs
                 if r["within_cell_rho_delta_feat_vs_frozen_loss"] is not None])),
        }

    wf = np.asarray(within_feat, float)
    out = {
        "script": "f14_deltafeat_check.py",
        "finding": ("delta_feat is an unvalidated proxy "
                    "for delta^2"),
        "source_records": ["experiments/results/e5/delta_feat_*.json",
                           "experiments/results/e2/*_main_*.json"],
        "external_yardsticks": [
            "CIFAR-10/100-C corruption severity 1..5 (ordered, externally "
            "defined, no labels or model output used to build it)",
            "frozen-model labelled cross-entropy and error rate (labels used "
            "only for this validation, never inside delta_feat)"],
        "A_severity_monotonicity": {
            "n_triples_dataset_arch_corruption": n_tot,
            "n_strictly_increasing_mean": n_strict,
            "frac_strictly_increasing": float(n_strict / n_tot),
            "n_rho_severity_equals_one": n_rho1,
            "frac_rho_severity_equals_one": float(n_rho1 / n_tot),
            "episode_level_rho_severity": {
                "median": float(np.median(rho_ep)),
                "min": float(np.min(rho_ep)), "max": float(np.max(rho_ep)),
                "n": len(rho_ep)},
            "per_corruption": per_corruption,
        },
        "B_labelled_risk": {
            "cell_level_by_method": cell_level,
            "within_cell_rho_delta_feat_vs_frozen_loss": {
                "n_cells": int(wf.size),
                "median": float(np.median(wf)),
                "mean": float(wf.mean()),
                "q10": float(np.percentile(wf, 10)),
                "q90": float(np.percentile(wf, 90)),
                "frac_positive": float((wf > 0).mean()),
                "frac_above_0.3": float((wf > 0.3).mean())},
        },
        "C_loss_proxy_reference": {
            "within_cell_rho_delta_proxy_vs_frozen_loss_median": float(
                np.median(within_loss_proxy)),
            "note": ("+1 by construction: delta_proxy = frozen_loss - "
                     "clean_ref, a per-run constant.  This is the reproduction "
                     "check, and it is also the reason the loss proxy cannot "
                     "be distinguished from document/image difficulty.")},
        "cells": cell_rows,
    }
    C.save(out, "f14_deltafeat_check.json")

    print(f"[f14] severity monotonicity: {n_strict}/{n_tot} "
          f"(dataset, arch, corruption) triples have mean delta_feat strictly "
          f"increasing across severities 1-5; rho(severity, mean)=+1 in "
          f"{n_rho1}/{n_tot}")
    print(f"[f14] episode-level rho(severity, delta_feat): median "
          f"{np.median(rho_ep):+.3f} (min {np.min(rho_ep):+.3f}, max "
          f"{np.max(rho_ep):+.3f})")
    print(f"[f14] within-cell rho(delta_feat, frozen labelled loss): median "
          f"{np.median(wf):+.3f}, {100*(wf > 0).mean():.0f}% positive, "
          f"{100*(wf > 0.3).mean():.0f}% above +0.3 ({wf.size} cells)")
    for meth, v in cell_level.items():
        print(f"[f14]   {meth:9s} ({v['arch']:11s}) cell-level rho vs frozen "
              f"loss {v['rho_mean_delta_feat_vs_mean_frozen_loss']:+.3f}, vs "
              f"error rate {v['rho_mean_delta_feat_vs_frozen_error_rate']:+.3f},"
              f" vs severity {v['rho_mean_delta_feat_vs_severity']:+.3f}")
    print("[f14] DONE", flush=True)


if __name__ == "__main__":
    main()
