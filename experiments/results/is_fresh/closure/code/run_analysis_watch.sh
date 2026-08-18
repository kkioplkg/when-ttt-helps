#!/usr/bin/env bash
# Runs analysis + independent verification as each lane completes, so results
# land without a human in the loop.
set -u
PY=${PYTHON:?set PYTHON to the env interpreter}
ROOT=${EXPROOT:?set EXPROOT to <repo>/experiments}
CD=$ROOT/ttt/closure
OUT=$ROOT/results/closure
LOG=${LOGDIR:?set LOGDIR}
cd "$CD"

while ! grep -q P1_LANE_DONE $LOG/p1_lane.log 2>/dev/null; do sleep 120; done
echo "=== analysing P1 $(date -Is) ===" >> $LOG/analysis.log
$PY analyze_p1.py --in-dir $OUT --out $OUT/P1_ANALYSIS.json >> $LOG/analysis.log 2>&1
$PY verify_closure.py --in-dir $OUT --out $OUT/VERIFY_P1.json   --data-root $ROOT/data --ckpt-dir $ROOT/ckpt/closure --reproduce-n 200   >> $LOG/analysis.log 2>&1
echo "ANALYSIS_P1_DONE" >> $LOG/analysis.log

while ! grep -q P2_LANE_DONE $LOG/p2_lane.log 2>/dev/null; do sleep 120; done
echo "=== analysing P2 $(date -Is) ===" >> $LOG/analysis.log
$PY analyze_p2.py --in-dir $OUT --out $OUT/P2_ANALYSIS.json >> $LOG/analysis.log 2>&1
$PY verify_closure.py --in-dir $OUT --out $OUT/VERIFY_ALL.json   --data-root $ROOT/data --ckpt-dir $ROOT/ckpt/closure --reproduce-n 200   >> $LOG/analysis.log 2>&1
echo "ANALYSIS_ALL_DONE" >> $LOG/analysis.log
