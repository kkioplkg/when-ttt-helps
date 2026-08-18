#!/usr/bin/env bash
# E3 vector-logging rerun driver.
#
# Runs one (domain, seed) job at a time per lane; several lanes share the GPU
# (GPT-2 small at batch 1 is launch-latency bound, not memory bound).
# Every job is resumable: the runner checkpoints every --ckpt-every documents
# and skips completed documents on restart, so re-running this script after a
# crash or a reboot continues where it stopped.
#
#   ./run_all_e3.sh <lane-file>
# where <lane-file> holds one "domain seed" pair per line.

set -u
R="${TTT_ROOT:?set TTT_ROOT to the project root on the run host}"
PY=$R/miniconda3/bin/python
REV=607a30d783dfa663caf39e06633721c8d4cfcd7e
OUT=$R/experiments/results/e3_vec
LOGS=$R/logs
export HF_HUB_OFFLINE=1
mkdir -p "$OUT" "$LOGS"

while read -r DOMAIN SEED; do
  [ -z "${DOMAIN:-}" ] && continue
  TAG="${DOMAIN}_ln_s${SEED}"
  if [ -s "$OUT/${TAG}_vectors.npz" ]; then
    echo "[driver] $TAG already complete, skipping"
    continue
  fi
  # mkdir is atomic, so several lanes may share one queue file without
  # two of them starting the same job.
  if ! mkdir "$LOGS/${TAG}.lock" 2>/dev/null; then
    echo "[driver] $TAG locked by another lane, skipping"
    continue
  fi
  REF=""
  if [ "$DOMAIN" != "wikitext" ]; then
    REF="--ref-file $R/experiments/results/e4_retained/wikitext_ref_s${SEED}.json"
  fi
  echo "[driver] $(date -Is) starting $TAG"
  cd "$R/experiments/ttt" || exit 1
  $PY e4_gpt2/run_e4_vec.py \
      --domain "$DOMAIN" --seed "$SEED" --n-docs 500 --steps 20 \
      --adapt-params ln \
      --data-dir "$R/experiments/data/e4" \
      --out-dir "$OUT" --dump-vectors "$OUT" \
      --gpt2-revision "$REV" --gpt2-path "$R/gpt2_607a30d" \
      --ckpt-every 25 \
      $REF >> "$LOGS/${TAG}.log" 2>&1
  RC=$?
  echo "[driver] $(date -Is) finished $TAG rc=$RC"
  # release the lock only on failure, so a retry can pick the job up; on
  # success the completed-npz check above is what makes the job idempotent.
  [ $RC -ne 0 ] && rmdir "$LOGS/${TAG}.lock" 2>/dev/null
done < "$1"
