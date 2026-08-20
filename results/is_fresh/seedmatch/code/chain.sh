#!/usr/bin/env bash
# Remote finalizer: drives the whole Stage-1 chain to completion without the
# launching session.
#
#   Stage A wave 1   3 x cifar10  source trainings  (already running when this
#                                                    is first launched)
#   Stage A wave 2   3 x cifar100 source trainings
#   Stage C'         6 crossed measurement passes (d_{i,m}, L_{i,m})
#   Analysis         sm_analysis.py + sm_transport.py
#
# CONCURRENCY IS 3, NOT 6, AND THAT IS A MEASURED CHOICE.  Per-epoch wall time
# on this host, measured with seedmatch/profile_epoch.py and with a real
# 1-epoch train_source run under load:
#     1-way  44.4 s/epoch      6 nets => ~14.8 h
#     2-way  60.0 s/epoch      6 nets => ~10.0 h
#     3-way  79.0 s/epoch      6 nets => ~ 8.8 h   <-- optimum
#     6-way ~210  s/epoch      6 nets => ~11.7 h   (oversubscribed)
# Two waves of three also means CIFAR-10 -- 75 of the 105 analysis cells and
# 83% of the cross-seed-exposed episodes -- is complete and analysable at the
# halfway point rather than everything being half-done.
#
# Resumable: every stage is guarded by the runner's per-job done-markers and by
# output-file existence, so re-launching this script continues rather than
# repeats.  Heartbeat at $STAGE/logs/chain.heartbeat.
set -u

# TTT_ROOT is the repository root -- in the release, the root of the
# extracted archive.  It has NO DEFAULT here on purpose: the run that
# produced the shipped records set it to the compute host's own checkout,
# and baking that literal into a published script leaves a path that
# resolves nowhere for the reader who runs it.  Export TTT_ROOT first.
TTT_ROOT="${TTT_ROOT:?export TTT_ROOT=<repository root>}"
PY="$TTT_ROOT/miniconda3/bin/python"
CODE="$TTT_ROOT/experiments/ttt"
DATA="$TTT_ROOT/experiments/data"
CKPT="$TTT_ROOT/experiments/ckpt/seedmatch"
STAGE="$TTT_ROOT/experiments/results/is_fresh_incoming_gpu3"
LANES="$STAGE/lanes"
LOGS="$STAGE/logs"
SM="$CODE/seedmatch"
MANIFEST="$STAGE/episode_manifest.json"

mkdir -p "$LOGS/done" "$STAGE/crossed"
CLOG="$LOGS/chain.log"
say() { echo "[chain $(date -Is)] $*" | tee -a "$CLOG"; }

# ---- run from an immutable snapshot --------------------------------------
# bash reads a script LAZILY, by byte offset.  Editing chain.sh while it is
# running -- which happened once in this run, when Stage B was appended while
# the chain sat in its wait loop -- can resume execution at an offset that now
# points into different text.  The chain therefore copies itself once and execs
# the copy, so later edits to the source can never disturb a live run; picking
# them up is then an explicit restart, which is what it should be.
SNAP="$LOGS/chain.running.sh"
if [ "${CHAIN_SNAPSHOT:-0}" != "1" ]; then
  cp "$0" "$SNAP"
  export CHAIN_SNAPSHOT=1
  exec bash "$SNAP" "$@"
fi

# ---- single-instance lock -------------------------------------------------
# NOT `pgrep -f chain.sh`: the launching ssh command line contains the literal
# path "seedmatch/chain.sh" itself, so pgrep -f matches the launcher and even
# the [c]hain bracket trick fails -- the pattern is a regex, but the launcher's
# own text still matches it.  A pidfile holding a PID we can test with kill -0
# is unambiguous.
PIDFILE="$LOGS/chain.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  echo "[chain] already running as PID $(cat "$PIDFILE"); exiting"
  exit 0
fi
echo $$ > "$PIDFILE"

( while true; do date -Is > "$LOGS/chain.heartbeat"; sleep 20; done ) &
TICKER=$!
trap 'kill $TICKER 2>/dev/null; rm -f "$PIDFILE"' EXIT

say "start pid=$$"

wait_for_markers() {   # wait_for_markers <label> <marker...>
  local label="$1"; shift
  local missing=1
  while [ $missing -eq 1 ]; do
    missing=0
    for m in "$@"; do
      [ -f "$LOGS/done/$m.done" ] || missing=1
    done
    [ $missing -eq 1 ] && sleep 60
  done
  say "$label complete"
}

# ---------------------------------------------------------------- Stage A.1
say "waiting for the cifar10 training wave"
wait_for_markers "cifar10 training wave" train_cifar10_s0 train_cifar10_s1 train_cifar10_s2

# ---------------------------------------------------------------- Stage A.2
say "launching the cifar100 training wave (3-way)"
for s in 0 1 2; do
  lane="lane_train_cifar100_s$s"
  if [ -f "$LOGS/done/train_cifar100_s$s.done" ]; then
    say "skip $lane (done)"; continue
  fi
  setsid nohup bash "$SM/runner.sh" "$lane" "$LANES/$lane.txt" > /dev/null 2>&1 < /dev/null &
  say "launched $lane"
  sleep 2
done
wait_for_markers "cifar100 training wave" train_cifar100_s0 train_cifar100_s1 train_cifar100_s2

# ------------------------------------------------------------------ Stage C'
say "crossed measurement matrix: 2 datasets x 3 measurement networks"
for ds in cifar10 cifar100; do
  for m in 0 1 2; do
    out="$STAGE/crossed/crossed_${ds}_s${m}.json"
    if [ -s "$out" ]; then say "skip crossed_${ds}_s${m} (exists)"; continue; fi
    say "crossed $ds through network s$m"
    (cd "$CODE" && "$PY" -m seedmatch.sm_crossed \
        --dataset "$ds" --measure-seed "$m" \
        --manifest "$MANIFEST" --data-root "$DATA" --ckpt-dir "$CKPT" \
        --m0-dir "$STAGE/m0" --out-dir "$STAGE/crossed") \
      >> "$LOGS/crossed_${ds}_s${m}.out" 2>&1
    rc=$?
    say "crossed $ds s$m rc=$rc"
    [ $rc -ne 0 ] && say "ABORTING: crossed measurement failed" && exit 2
  done
done

# ------------------------------------------------------------------ analysis
say "analysis"
(cd "$SM" && "$PY" sm_analysis.py \
    --cross-dir "$STAGE/crossed" --manifest "$MANIFEST" \
    --out "$STAGE/sm_analysis.json") >> "$LOGS/analysis.out" 2>&1
say "sm_analysis rc=$?"

(cd "$SM" && "$PY" sm_transport.py \
    --cross-dir "$STAGE/crossed" \
    --e5-dir "$STAGE/published/e5" --e2-dir "$STAGE/published/e2" \
    --out "$STAGE/sm_transport.json") >> "$LOGS/analysis.out" 2>&1
say "sm_transport rc=$?"

date -Is > "$STAGE/STAGE1_DONE"
say "STAGE 1 COMPLETE (crossed matrix + concordance/severity/transport endpoints)"

# ================================================================= Stage B
# APPROVED SCOPE: EXPOSED-ONLY -- the six runs whose source seed is not 0.
# Seed-0 episodes were never cross-measured, so re-running them buys no
# mechanism information; they only contribute the structural point mass at
# zero that dilutes the full-grid protocol effect.  The remaining four runs
# (the seed-0 ones, which alone would license Delta_protocol) are NOT launched
# here and require a fresh decision.
#
# All six carry ALTA off, which is exactly what their published counterparts
# carried -- so this lane reproduces the published settings with zero
# deviation rather than merely defensibly.
say "Stage B (exposed-only): recon heads first"
if [ -s "$LANES/jobs_recon.txt" ]; then
  bash "$SM/runner.sh" lane_recon "$LANES/jobs_recon.txt" >> "$LOGS/recon.out" 2>&1
  say "recon heads rc=$?"
fi

say "Stage B: 6 exposed adaptation runs, 3 lanes of 2"
: > "$LANES/lane_grid_a.txt"; : > "$LANES/lane_grid_b.txt"; : > "$LANES/lane_grid_c.txt"
while IFS=$'\t' read -r JOBID CMD; do
  [ -z "${JOBID:-}" ] && continue
  case "$JOBID" in
    grid_cifar10_ttt_rot_*)  printf '%s\t%s\n' "$JOBID" "$CMD" >> "$LANES/lane_grid_a.txt" ;;
    grid_cifar10_ttt_mask_*) printf '%s\t%s\n' "$JOBID" "$CMD" >> "$LANES/lane_grid_b.txt" ;;
    *)                       printf '%s\t%s\n' "$JOBID" "$CMD" >> "$LANES/lane_grid_c.txt" ;;
  esac
done < "$LANES/jobs_grid_exposed.txt"

for lane in lane_grid_a lane_grid_b lane_grid_c; do
  setsid nohup bash "$SM/runner.sh" "$lane" "$LANES/$lane.txt" > /dev/null 2>&1 < /dev/null &
  say "launched $lane"
  sleep 2
done
wait_for_markers "Stage B exposed grid" \
  grid_cifar10_ttt_rot_s1 grid_cifar10_ttt_rot_s2 \
  grid_cifar10_ttt_mask_s1 grid_cifar10_ttt_mask_s2 \
  grid_cifar100_ttt_rot_s1 grid_cifar100_ttt_rot_s2

say "Stage B analysis"
(cd "$SM" && "$PY" sm_downstream.py \
    --cross-dir "$STAGE/crossed" --e2-dir "$STAGE/e2" \
    --manifest "$MANIFEST" --out "$STAGE/sm_downstream.json") \
  >> "$LOGS/analysis.out" 2>&1
say "sm_downstream rc=$?"

date -Is > "$STAGE/CHAIN_DONE"
say "CHAIN COMPLETE"
