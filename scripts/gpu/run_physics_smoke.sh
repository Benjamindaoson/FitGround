#!/bin/bash
set -x
source /root/workspace/projects/FitGround/scripts/gpu/flux_env.sh
cd /tmp
python /root/workspace/projects/FitGround/scripts/gpu/garmentcode_worker.py \
  --intended-delta-cm 0.001 \
  --tag physics_smoke_tiny \
  --output-dir /root/workspace/projects/FitGround/artifacts/gpu/physics_smoke \
  --seed 0 --physics --render --max-sim-steps 250
echo PHYSICS_SMOKE_EXIT=$?
