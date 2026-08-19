#!/usr/bin/env bash
# T2.1 + T2.5 lane.  Strictly after the P2 lane -- one GPU, one lane at a time.
# T2.5 additionally needs the 10-class source models the P2 lane trains.
set -u
PY=${PYTHON:?set PYTHON to the env interpreter}
ROOT=${EXPROOT:?set EXPROOT to <repo>/experiments}
DATA=$ROOT/data
OUT=$ROOT/results/closure
LOG=${LOGDIR:?set LOGDIR}
cd $ROOT/ttt/closure

while ! grep -q P2_LANE_DONE $LOG/p2_lane.log 2>/dev/null; do sleep 120; done
echo "=== extras lane starting $(date -Is) ===" >> $LOG/extras_lane.log

echo "=== T2.1 batch scope (N>1 collinearity loss) ===" >> $LOG/extras_lane.log
for pair in auto_frog plane_ship cat_dog; do for seed in 20260901 20260902 20260903; do
  $PY scope_batch.py --pair $pair --seed $seed --batches 25 --dtype float64     --data-root $DATA --ckpt-dir $ROOT/ckpt/closure --out-dir $OUT     --heartbeat $LOG/hb_extras.json >> $LOG/extras_lane.log 2>&1
done; done
echo "T2_1_DONE" >> $LOG/extras_lane.log

echo "=== T2.5 A2 neighbourhood shell search ===" >> $LOG/extras_lane.log
for obj in tent ttt_rot; do for seed in 20260921 20260922 20260923; do
  $PY shell_a2.py --seed $seed --objective $obj --instances 40 --n-dir 8     --data-root $DATA --ckpt-dir $ROOT/ckpt/closure --out-dir $OUT     --heartbeat $LOG/hb_extras.json >> $LOG/extras_lane.log 2>&1
done; done
echo "T2_5_DONE" >> $LOG/extras_lane.log

echo "=== final analysis + full verification ===" >> $LOG/extras_lane.log
$PY analyze_p1.py --in-dir $OUT --out $OUT/P1_ANALYSIS.json >> $LOG/extras_lane.log 2>&1
$PY analyze_p2.py --in-dir $OUT --out $OUT/P2_ANALYSIS.json >> $LOG/extras_lane.log 2>&1
$PY analyze_boundary.py --in-dir $OUT --out $OUT/T15_BOUNDARY.json >> $LOG/extras_lane.log 2>&1
$PY analyze_extras.py --in-dir $OUT --out $OUT/T2_EXTRAS.json >> $LOG/extras_lane.log 2>&1
$PY verify_closure.py --in-dir $OUT --out $OUT/VERIFY_FINAL.json   --data-root $DATA --ckpt-dir $ROOT/ckpt/closure --reproduce-n 200   >> $LOG/extras_lane.log 2>&1
echo "EXTRAS_LANE_DONE" >> $LOG/extras_lane.log
