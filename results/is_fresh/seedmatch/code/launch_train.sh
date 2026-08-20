#!/usr/bin/env bash
# Launch the six source trainings as SIX CONCURRENT single-job lanes.
#
# Why concurrent: profiling on this host (seedmatch/profile_epoch.py) showed an
# epoch of `train_source.py --arch resnet26ttt` spends 69% of its wall clock
# waiting on the dataloader and leaves the GPU idle for most of it -- 0% GPU
# utilisation in 22 of 25 samples.  The published runs took ~49 min for 200
# epochs on an RTX 2080 Ti; serially this host needs ~148 min, which would put
# six retrainings alone at ~14.8 GPU-h and blow the budget.  Concurrency costs
# nothing scientific -- it is pure scheduling, and does not touch any run's
# recipe, seed, worker count or data order -- and measured throughput rises
# 1.48x at 2-way and 1.69x at 3-way.
#
# num_workers stays at the published default of 8.  Raising it to 16 was
# measured and is WORSE on this host (75.6 s/epoch against 44.4 s), so the
# published config is also the fastest one; no deviation is needed.
set -u
# TTT_ROOT is the repository root -- in the release, the root of the
# extracted archive.  It has NO DEFAULT here on purpose: the run that
# produced the shipped records set it to the compute host's own checkout,
# and baking that literal into a published script leaves a path that
# resolves nowhere for the reader who runs it.  Export TTT_ROOT first.
TTT_ROOT="${TTT_ROOT:?export TTT_ROOT=<repository root>}"
STAGE="$TTT_ROOT/experiments/results/is_fresh_incoming_gpu3"
LANES="$STAGE/lanes"
SM="$TTT_ROOT/experiments/ttt/seedmatch"

mkdir -p "$LANES" "$STAGE/logs/done"

# one single-job lane file per network, from the verified job list
while IFS=$'\t' read -r JOBID CMD; do
  case "$JOBID" in train_*) ;; *) continue ;; esac
  printf '%s\t%s\n' "$JOBID" "$CMD" > "$LANES/lane_$JOBID.txt"
done < "$LANES/jobs_train.txt"

n=0
for f in "$LANES"/lane_train_*.txt; do
  lane=$(basename "$f" .txt)
  if [ -f "$STAGE/logs/$lane.finished" ]; then
    echo "skip $lane (already finished)"
    continue
  fi
  setsid nohup bash "$SM/runner.sh" "$lane" "$f" > /dev/null 2>&1 < /dev/null &
  n=$((n+1))
  echo "launched $lane"
  sleep 2
done
echo "launched $n training lanes at $(date -Is)"
