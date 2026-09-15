#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/workspace/projects/FitGround
source "$ROOT/scripts/gpu/flux_env.sh"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
LOG="$ROOT/artifacts/training/run_all_training.log"
mkdir -p "$ROOT/artifacts/training"
exec > >(tee -a "$LOG") 2>&1
echo "TRAIN_START $(date -u)"
python "$ROOT/scripts/gpu/build_training_lattice.py"
python "$ROOT/scripts/train/run_all_training.py"
echo "TRAIN_END $(date -u)"
