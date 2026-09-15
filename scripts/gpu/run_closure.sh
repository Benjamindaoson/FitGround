#!/usr/bin/env bash
# FINAL CLOSURE GPU driver. Does not kill tmux mllm-dl.
set -euo pipefail
source /root/workspace/projects/FitGround/scripts/gpu/flux_env.sh
export PYTHONPATH=/root/workspace/projects/FitGround/src:/root/workspace/projects/FitGround/scripts/gpu:${PYTHONPATH:-}
export PYTHONUNBUFFERED=1
cd /tmp
LOG=/root/workspace/projects/FitGround/artifacts/hero/closure.log
mkdir -p /root/workspace/projects/FitGround/artifacts/hero
exec >>"$LOG" 2>&1
echo "CLOSURE_START $(date -u)"
python /root/workspace/projects/FitGround/scripts/gpu/shoulder_scan.py
python /root/workspace/projects/FitGround/scripts/gpu/expand_visual_physics.py --max-states 28 --max-sim-steps 220
python /root/workspace/projects/FitGround/scripts/gpu/finalize_closure.py
if [ -f /root/workspace/projects/FitGround/artifacts/hero/mllm_status.json ]; then
  python /root/workspace/projects/FitGround/scripts/gpu/run_mllm_eval.py --max-cases 16 || true
  python /root/workspace/projects/FitGround/scripts/gpu/finalize_closure.py
fi
echo "CLOSURE_END $(date -u)"
