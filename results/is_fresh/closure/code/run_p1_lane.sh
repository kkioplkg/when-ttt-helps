#!/usr/bin/env bash
# P1 lane: one GPU, sequential.  Order follows DESIGN v2 s5 -- highest-value
# evidence first, so a truncated run still lands the sharpest result.
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
PAIRS="auto_frog plane_ship cat_dog"
SEEDS="20260901 20260902 20260903"

echo "=== T1.4 q-sweep (float64) ===" >> $LOG/p1_lane.log
for pair in $PAIRS; do for seed in $SEEDS; do
  $PY sweep_q.py --pair $pair --seed $seed --instances 25     --cells clean,gaussian_noise:3,contrast:5 --dtype float64     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p1.json >> $LOG/p1_lane.log 2>&1
done; done
echo "T1.4_DONE" >> $LOG/p1_lane.log

echo "=== T1.1/T1.2 primary float32 ===" >> $LOG/p1_lane.log
for pair in $PAIRS; do for seed in $SEEDS; do
  $PY measure_p1.py --pair $pair --seed $seed --subset norm --instances 200     --temperatures 1.0,2.0,4.0 --dtype float32     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p1.json >> $LOG/p1_lane.log 2>&1
done; done
echo "P1_FLOAT32_DONE" >> $LOG/p1_lane.log

echo "=== T1.1/T1.2 float64 (25% subsample; T1.2 primary precision) ===" >> $LOG/p1_lane.log
for pair in $PAIRS; do for seed in $SEEDS; do
  $PY measure_p1.py --pair $pair --seed $seed --subset norm --instances 200     --temperatures 1.0,2.0,4.0 --dtype float64 --subsample-frac 0.25     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p1.json >> $LOG/p1_lane.log 2>&1
done; done
echo "P1_FLOAT64_DONE" >> $LOG/p1_lane.log

echo "=== architecture robustness arm: WRN-28-10 BN(eval) ===" >> $LOG/p1_lane.log
$PY measure_p1.py --pair cat_dog --seed 20260901 --arch wrn2810 --subset norm   --instances 100 --temperatures 1.0 --dtype float32   --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT   --heartbeat $LOG/hb_p1.json >> $LOG/p1_lane.log 2>&1

echo "=== subset-invariance smoke (all / encoder) ===" >> $LOG/p1_lane.log
for sub in all encoder; do
  $PY measure_p1.py --pair cat_dog --seed 20260901 --subset $sub     --instances 25 --temperatures 1.0 --dtype float64     --data-root $DATA --ckpt-dir $CKPT --out-dir $OUT     --heartbeat $LOG/hb_p1.json >> $LOG/p1_lane.log 2>&1
done
echo "P1_LANE_DONE" >> $LOG/p1_lane.log
