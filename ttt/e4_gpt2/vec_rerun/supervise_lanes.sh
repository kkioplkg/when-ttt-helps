#!/usr/bin/env bash
# Keep MAXLANES E3 jobs resident on the GPU until the queue is exhausted.
#
# The initial launch split the 12 jobs into fixed lanes, which leaves the
# longest lane running alone at the end while the others sit idle. This just
# tops the pool back up: whenever fewer than MAXLANES `run_e4_vec.py` processes
# are alive and the queue still has an unlocked job, it starts one more lane.
#
# Safe to run alongside the original lanes because `run_all_e3.sh` claims each
# job with an atomic `mkdir` lock and skips jobs whose *_vectors.npz already
# exists, so no job can be started twice.
#
# MAXLANES=3 is a memory bound, not a throughput one: three concurrent GPT-2
# jobs sit at ~7.4 GB of the 3080's 10 GB, and the GPU is already at 100%
# utilisation, so a fourth risks OOM for very little gain.

set -u
R="${TTT_ROOT:?set TTT_ROOT to the project root on the run host}"
QUEUE=$R/queue_rest.txt
MAXLANES=${MAXLANES:-3}
LOGS=$R/logs

while true; do
  # every job either finished or claimed -> nothing left to schedule
  REMAINING=0
  while read -r DOMAIN SEED; do
    [ -z "${DOMAIN:-}" ] && continue
    TAG="${DOMAIN}_ln_s${SEED}"
    if [ ! -s "$R/experiments/results/e3_vec/${TAG}_vectors.npz" ] \
       && [ ! -d "$LOGS/${TAG}.lock" ]; then
      REMAINING=$((REMAINING + 1))
    fi
  done < "$QUEUE"

  RUNNING=$(pgrep -f -c 'run_e4_vec\.py' || true)
  RUNNING=${RUNNING:-0}
  echo "[supervisor] $(date -Is) running=$RUNNING unclaimed=$REMAINING"

  if [ "$REMAINING" -eq 0 ] && [ "$RUNNING" -eq 0 ]; then
    echo "[supervisor] $(date -Is) queue drained, exiting"
    break
  fi

  if [ "$REMAINING" -gt 0 ] && [ "$RUNNING" -lt "$MAXLANES" ]; then
    N=$((MAXLANES - RUNNING))
    for _ in $(seq 1 "$N"); do
      echo "[supervisor] $(date -Is) topping up a lane"
      setsid nohup bash "$R/experiments/ttt/run_all_e3.sh" "$QUEUE" \
        >> "$LOGS/lane_topup.log" 2>&1 < /dev/null &
      sleep 20   # let it claim a lock before deciding again
    done
  fi
  sleep 120
done
