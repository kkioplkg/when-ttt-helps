"""F27 -- E2 identity-level overlap of the commissioning/evaluation cross-fit.

WHAT THE PAPER CLAIMS (Section 7.2 and Appendix C.2): the E2 cross-fit split is
exact at the level of episode *records*, but not at the level of image
*identity*, because each (dataset, method, corruption, severity) cell pools its
episodes over source-model seeds, so one image can be visited by two seeds and
the two visits can land on opposite sides of the split.  The manuscript reports
how many identities that affects and how much the headline correlations move
when every such identity is deleted from *both* shares.

CLASSIFICATION: MEASURED, cross-fit-faithful.  This script is the record of
record for those sentences.  It reproduces `f8_e2_crossfit.py`'s split
*exactly* -- same episode loader, same cell ordering, same commissioning
fraction, same `default_rng(seed + 1)` stream -- and then, per split seed and
per method:

  * counts the image identities that appear in both shares of a cell;
  * counts the episode rows those identities account for;
  * recomputes the headline Spearman rho after deleting every cross-share
    identity from BOTH shares, every surviving row keeping the side the
    original permutation gave it.

The deletion is deliberately two-sided: dropping the duplicate from one side
only would leave the retained copy correlated with the deleted one through the
shared image, which is the very dependence being probed.

No new model runs and no new adaptation code: this re-analyses the ORIGINAL E2
raw episode records (results/e2/*_main_*.json) and the ORIGINAL E5 feature-shift
files, exactly as F8 does.

SEEDS: the five fresh split seeds 20260801..20260805 (`common.SEEDS`), the same
five F8 uses.  Nothing here is random beyond that stream.

OUTPUT: results/is_fresh/f27_e2_identity.json.  Bound in `r9_reconcile.py`
under the "E2 identity" labels.

Usage:  python f27_e2_identity.py
"""
import argparse
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import common as C            # noqa: E402
import f8_e2_crossfit as F8   # noqa: E402

# F8's own default; the value used for every published cross-fit number.
COMMISSION = 0.5

# (statistic, method) arms.  The first four are the headline correlations
# quoted in Section 7.2 / Appendix C.2; the last two are the deterministic
# baselines, included so the sensitivity is reported for every cross-fit arm
# rather than only for the ones with the largest shift.
ARMS = (("phase_feat", "ttt_mask"), ("phase_feat", "ttt_rot"),
        ("phase_loss", "ttt_mask"), ("phase_loss", "ttt_rot"),
        ("phase_feat", "tent"), ("phase_feat", "pl"))


def load_cells_with_idx():
    """F8.load_cells(), but every episode also carries its image identity.

    Kept structurally identical to `f8_e2_crossfit.load_cells` so that the
    per-cell episode ORDER -- which is what the permutation indexes into --
    is bit-for-bit the same.  The only additions are the `idx` and
    `model_seed` fields.
    """
    dfeat = F8.load_delta_feat()
    cells = {}
    for fn in sorted(os.listdir(F8.E2_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(F8.E2_DIR, fn), encoding="utf-8") as f:
            o = json.load(f)
        argv = o.get("meta", {}).get("argv", {})
        if argv.get("mode", "main") != "main":
            continue
        ds, meth = argv["dataset"], argv["method"]
        seed = argv.get("seed")
        fmap = dfeat.get((ds, F8.METHOD_ARCH.get(meth)), {})
        for cell in o.get("results", []):
            corr, sev = cell["corruption"], int(cell["severity"])
            key = (ds, meth, corr, sev)
            for e in cell.get("episodes", []):
                idx = e.get("idx")
                df = (fmap.get((corr, sev, int(idx)))
                      if idx is not None else None)
                rec = F8._episode_stats(e.get("alpha"), e.get("sigma2_rel"),
                                        df, e.get("delta_proxy"))
                rec["frozen_loss"] = e["frozen_loss"]
                rec["steps"] = {int(t): v["loss"]
                                for t, v in e.get("steps", {}).items()}
                rec["idx"] = None if idx is None else int(idx)
                rec["model_seed"] = seed
                cells.setdefault(key, []).append(rec)
    return cells


def split_indices(cells, method, seed, commission):
    """The exact (idx_stat, idx_gain) partition `F8.build_rows` produces.

    F8 draws its per-cell permutations from `default_rng(seed + 1)` while
    iterating `sorted(cells)` and skipping cells of other methods, so the
    stream position depends on the cell order; that order is reproduced here.
    """
    rng = np.random.default_rng(seed + 1)
    out = {}
    for key in sorted(cells):
        if key[1] != method:
            continue
        n = len(cells[key])
        perm = rng.permutation(n)
        k = min(max(int(round(n * commission)), 1), n - 1)
        out[key] = (perm[:k].tolist(), perm[k:].tolist())
    return out


def rho_for(cells, splits, stat_key, how, drop=None):
    """Spearman(phase, gain_final) across the method's cells.

    `drop` maps a cell key to the set of row positions to delete from BOTH
    shares before aggregating; surviving rows keep their assigned share.
    """
    xs, ys = [], []
    for key in sorted(splits):
        idx_stat, idx_gain = splits[key]
        if drop:
            bad = drop.get(key, set())
            idx_stat = [i for i in idx_stat if i not in bad]
            idx_gain = [i for i in idx_gain if i not in bad]
        if not idx_stat or not idx_gain:
            continue
        ph, gf, _gbc, _gbi = F8.cell_stats(cells[key], idx_stat, idx_gain,
                                           stat_key, how)
        xs.append(ph)
        ys.append(gf)
    return F8.spearman(xs, ys)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commission", type=float, default=COMMISSION)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEEDS)
    args = ap.parse_args()

    cells = load_cells_with_idx()
    n_eps = sum(len(v) for v in cells.values())
    print(f"[f27] {len(cells)} cells, {n_eps} episode rows", flush=True)

    report = {}
    for stat_key, meth in ARMS:
        base, kept, overlaps, overlap_rows = [], [], [], []
        for s in args.seeds:
            splits = split_indices(cells, meth, s, args.commission)
            drop = {}
            n_ids = n_rows = 0
            for key, (a, b) in splits.items():
                eps = cells[key]
                ida = {eps[i]["idx"] for i in a if eps[i]["idx"] is not None}
                idb = {eps[i]["idx"] for i in b if eps[i]["idx"] is not None}
                both = ida & idb
                if both:
                    rows = {i for i in range(len(eps))
                            if eps[i]["idx"] in both}
                    drop[key] = rows
                    n_ids += len(both)
                    n_rows += len(rows)
            overlaps.append(n_ids)
            overlap_rows.append(n_rows)
            base.append(rho_for(cells, splits, stat_key, "mean"))
            kept.append(rho_for(cells, splits, stat_key, "mean", drop))
        b, k = float(np.mean(base)), float(np.mean(kept))
        report[f"{meth}/{stat_key}"] = {
            "rho_mean_final": round(b, 5),
            "rho_mean_final_identity_pruned": round(k, 5),
            "abs_shift": round(abs(k - b), 5),
            "cross_share_identities_per_seed": overlaps,
            "cross_share_rows_per_seed": overlap_rows,
        }
        print(f"[f27] {meth:9s} {stat_key:11s}  rho {b:.5f} -> {k:.5f} "
              f"(|d| {abs(k - b):.5f})  ids/seed {min(overlaps)}-"
              f"{max(overlaps)} rows/seed {min(overlap_rows)}-"
              f"{max(overlap_rows)}", flush=True)

    worst = max(v["abs_shift"] for v in report.values())
    id_lo = min(min(v["cross_share_identities_per_seed"])
                for v in report.values())
    id_hi = max(max(v["cross_share_identities_per_seed"])
                for v in report.values())
    row_lo = min(min(v["cross_share_rows_per_seed"]) for v in report.values())
    row_hi = max(max(v["cross_share_rows_per_seed"]) for v in report.values())
    print()
    print(f"[f27] SUMMARY  cross-share image identities per seed: "
          f"{id_lo}-{id_hi}")
    print(f"[f27] SUMMARY  episode records they account for:      "
          f"{row_lo}-{row_hi} of {n_eps}")
    print(f"[f27] SUMMARY  largest |rho shift| after pruning:     {worst:.5f}")

    C.save({"commission": args.commission,
            "seeds": list(args.seeds),
            "n_cells": len(cells),
            "n_episode_records": n_eps,
            "arms": report,
            "identities_per_seed_range": [id_lo, id_hi],
            "rows_per_seed_range": [row_lo, row_hi],
            "max_abs_rho_shift": worst},
           "f27_e2_identity.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
