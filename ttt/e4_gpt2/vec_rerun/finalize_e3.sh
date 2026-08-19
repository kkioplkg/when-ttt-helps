#!/usr/bin/env bash
# Wait for the 12-job E3 grid, then verify and summarise -- on the box.
#
# This exists so the tail of the pipeline does not depend on a supervising
# session staying alive: the grid takes ~6 h, and a dropped ssh session or a
# reaped waiter must not leave finished vectors unverified. Everything below is
# idempotent, so it can be re-run at any point.

set -u
R="${TTT_ROOT:?set TTT_ROOT to the project root on the run host}"
PY=$R/miniconda3/bin/python
OUT=$R/experiments/results/e3_vec
RET=$R/experiments/results/e4_retained
DONEFLAG=$OUT/FINALIZED

echo "[finalize] $(date -Is) waiting for 12 jobs"
while true; do
  N=$(ls $OUT/*_vectors.npz 2>/dev/null | wc -l)
  RUNNING=$(pgrep -f -c 'run_e4_vec\.py' || true)
  RUNNING=${RUNNING:-0}
  if [ "$N" -ge 12 ]; then
    echo "[finalize] $(date -Is) all 12 present"
    break
  fi
  # If nothing is running and nothing is left to schedule, stop waiting
  # forever -- verify whatever landed and let the report say so.
  if [ "$RUNNING" -eq 0 ]; then
    STALLED=$((${STALLED:-0} + 1))
    if [ "$STALLED" -ge 5 ]; then
      echo "[finalize] $(date -Is) no runners for 10 min with $N/12 done; verifying partial grid"
      break
    fi
  else
    STALLED=0
  fi
  sleep 120
done

echo "[finalize] $(date -Is) verifying"
$PY $R/experiments/ttt/verify_vectors.py \
    --new-dir "$OUT" --retained-dir "$RET" \
    --out "$OUT/verify_report.json"

echo "[finalize] $(date -Is) summarising"
$PY $R/experiments/ttt/make_verify_summary.py \
    --report "$OUT/verify_report.json" \
    --out "$OUT/VERIFY_SUMMARY.md"

# Compare the regenerated wikitext delta-proxy references against the retained
# ones; these are the values every non-wikitext domain's delta_proxy is measured
# from, so a drift here would silently move a whole column of the E3 tables.
$PY - <<'PY'
import json, os, glob
R = os.environ["TTT_ROOT"]
out = {}
for p in sorted(glob.glob(f"{R}/experiments/results/e3_vec/wikitext_ref_s*.json")):
    tag = os.path.basename(p)
    new = json.load(open(p))
    old_p = f"{R}/experiments/results/e4_retained/{tag}"
    if not os.path.exists(old_p):
        continue
    old = json.load(open(old_p))
    a, b = new["mean_frozen_cont_ce"], old["mean_frozen_cont_ce"]
    out[tag] = {"new": a, "retained": b, "abs_diff": abs(a - b),
                "n_docs_new": new["n_docs"], "n_docs_retained": old["n_docs"]}
    print(f"[finalize] {tag}: new={a:.12f} retained={b:.12f} diff={abs(a-b):.3e}")
json.dump(out, open(f"{R}/experiments/results/e3_vec/wikitext_ref_check.json", "w"), indent=1)
PY

echo "[finalize] $(date -Is) sizes"
du -sh "$OUT"
ls -la "$OUT"/*_vectors.npz | wc -l

date -Is > "$DONEFLAG"
echo "[finalize] $(date -Is) DONE"
