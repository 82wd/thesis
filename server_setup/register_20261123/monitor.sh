#!/bin/bash
# Read-only dashboard; never starts or restarts training.
set -euo pipefail
RUN_ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$RUN_ROOT/training_monitor.py" \
  --root "$RUN_ROOT" --run-dir "$RUN_ROOT" --log "$RUN_ROOT/train.log" \
  --config rgbt_register --epochs 60 --session register_20261123 \
  --gpu 4 --interval 10 --stale-seconds 300 "$@"
