#!/usr/bin/env bash
set -u
PY=${PYTHON:?set PYTHON to the env interpreter}
ROOT=${EXPROOT:?set EXPROOT to <repo>/experiments}
OUT=$ROOT/results/closure
LOG=${LOGDIR:?set LOGDIR}
cd $ROOT/ttt/closure
for pair in auto_frog plane_ship cat_dog; do for seed in 20260901 20260902 20260903; do
  for dt in float32 float64; do
    $PY sweep_boundary.py --pair $pair --seed $seed --instances 40 --dtype $dt       --data-root $ROOT/data --ckpt-dir $ROOT/ckpt/closure --out-dir $OUT       --heartbeat $LOG/hb_bnd.json >> $LOG/bnd_lane.log 2>&1
  done
done; done
echo BND_LANE_DONE >> $LOG/bnd_lane.log
