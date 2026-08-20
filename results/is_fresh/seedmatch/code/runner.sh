#!/usr/bin/env bash
# Sequential job lane with per-job done-markers, heartbeat and resume.
#
#   runner.sh <lane-name> <jobfile>
#
# Each line of <jobfile> is  <job-id>\t<command>.  A job whose done-marker
# exists is skipped, so re-launching the lane resumes rather than repeats.
# The heartbeat file is touched every 20 s by a background ticker for as long
# as the lane is alive, so a stalled lane is distinguishable from a finished
# one without reading logs.
set -u

# TTT_ROOT is the repository root -- in the release, the root of the
# extracted archive.  It has NO DEFAULT here on purpose: the run that
# produced the shipped records set it to the compute host's own checkout,
# and baking that literal into a published script leaves a path that
# resolves nowhere for the reader who runs it.  Export TTT_ROOT first.
TTT_ROOT="${TTT_ROOT:?export TTT_ROOT=<repository root>}"
STAGE="$TTT_ROOT/experiments/results/is_fresh_incoming_gpu3"
LANE="$1"
JOBFILE="$2"
LOGDIR="$STAGE/logs"
MARKDIR="$STAGE/logs/done"
mkdir -p "$LOGDIR" "$MARKDIR"

HB="$LOGDIR/$LANE.heartbeat"
LOG="$LOGDIR/$LANE.log"

( while true; do
    date -Is > "$HB"
    sleep 20
  done ) &
TICKER=$!
trap 'kill $TICKER 2>/dev/null' EXIT

echo "[$LANE] start $(date -Is) pid=$$ jobfile=$JOBFILE" | tee -a "$LOG"

rc_total=0
while IFS=$'\t' read -r JOBID CMD; do
  [ -z "${JOBID:-}" ] && continue
  case "$JOBID" in \#*) continue ;; esac
  MARK="$MARKDIR/$JOBID.done"
  if [ -f "$MARK" ]; then
    echo "[$LANE] SKIP $JOBID (done $(cat "$MARK"))" | tee -a "$LOG"
    continue
  fi
  echo "[$LANE] RUN  $JOBID $(date -Is)" | tee -a "$LOG"
  t0=$(date +%s)
  bash -c "$CMD" >> "$LOGDIR/$JOBID.out" 2>&1
  rc=$?
  t1=$(date +%s)
  if [ $rc -eq 0 ]; then
    echo "$(date -Is) elapsed_s=$((t1-t0))" > "$MARK"
    echo "[$LANE] OK   $JOBID in $((t1-t0))s" | tee -a "$LOG"
  else
    rc_total=$rc
    echo "[$LANE] FAIL $JOBID rc=$rc after $((t1-t0))s -- lane continues" | tee -a "$LOG"
    echo "$(date -Is) rc=$rc elapsed_s=$((t1-t0))" > "$LOGDIR/$JOBID.failed"
  fi
done < "$JOBFILE"

echo "[$LANE] done $(date -Is) worst_rc=$rc_total" | tee -a "$LOG"
date -Is > "$LOGDIR/$LANE.finished"
exit $rc_total
