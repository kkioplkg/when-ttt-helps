#!/usr/bin/env bash
# P2 lane.  Waits for the P1 lane to finish -- one GPU, one lane at a time.
set -u
PY=${PYTHON:?set PYTHON to the env interpreter}
ROOT=${EXPROOT:?set EXPROOT to <repo>/experiments}
CD=$ROOT/ttt/closure
DATA=$ROOT/data
CKPT=$ROOT/ckpt/closure
OUT=$ROOT/results/closure
LOG=${LOGDIR:?set LOGDIR}
mkdir -p "$OUT" "$LOG"
cd "$CD"
SEEDS="20260921 20260922 20260923"

while ! grep -q P1_LANE_DONE $LOG/p1_lane.log 2>/dev/null; do sleep 60; done
echo "=== P1 finished; P2 lane starting $(date -Is) ===" >> $LOG/p2_lane.log

echo "=== 10-class source models (3 seeds) ===" >> $LOG/p2_lane.log
for seed in $SEEDS; do
  $PY train_source10.py --seed $seed --epochs 100 --data-root $DATA     --ckpt-dir $CKPT --heartbeat $LOG/hb_p2.json >> $LOG/p2_lane.log 2>&1
done
echo "P2_TRAIN_DONE" >> $LOG/p2_lane.log

echo "=== T2.2/T2.3/T2.4 primary: plain SGD, no momentum ===" >> $LOG/p2_lane.log
for obj in tent ttt_rot; do for seed in $SEEDS; do
  $PY measure_p2.py --seed $seed --objective $obj --momentum 0.0     --instances 100 --lr 1e-3 --steps 20     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p2.json >> $LOG/p2_lane.log 2>&1
done; done
echo "P2_PRIMARY_DONE" >> $LOG/p2_lane.log

echo "=== T3.2 practice-trajectory stress test: momentum 0.9 (NOT envelope) ===" >> $LOG/p2_lane.log
for obj in tent ttt_rot; do
  $PY measure_p2.py --seed 20260921 --objective $obj --momentum 0.9     --instances 50 --lr 1e-3 --steps 20     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p2.json >> $LOG/p2_lane.log 2>&1
done
echo "P2_LANE_DONE" >> $LOG/p2_lane.log
