#!/usr/bin/env bash
# Train every P1 binary source model, one at a time (single GPU lane).
set -u
PY=${PYTHON:?set PYTHON to the env interpreter}
ROOT=${EXPROOT:?set EXPROOT to <repo>/experiments}
CD=$ROOT/ttt/closure
DATA=$ROOT/data
CKPT=$ROOT/ckpt/closure
LOG=${LOGDIR:?set LOGDIR}
mkdir -p "$LOG" "$CKPT"
cd "$CD"
for pair in auto_frog plane_ship cat_dog; do
  for seed in 20260901 20260902 20260903; do
    $PY train_binary.py --pair $pair --seed $seed --arch resnet26gn --epochs 60       --data-root "$DATA" --ckpt-dir "$CKPT"       --heartbeat "$LOG/hb_train.json" >> "$LOG/train_binary.log" 2>&1
  done
done
# architecture robustness arm: one pair, one seed, BatchNorm net
$PY train_binary.py --pair cat_dog --seed 20260901 --arch wrn2810 --epochs 40   --data-root "$DATA" --ckpt-dir "$CKPT"   --heartbeat "$LOG/hb_train.json" >> "$LOG/train_binary.log" 2>&1
echo "ALL_TRAIN_DONE" >> "$LOG/train_binary.log"
