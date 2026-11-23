#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES=4 LOCAL_RANK=-1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
PY=/nas/liziyan103/anaconda3/envs/seatrack/bin/python
trap 'printf "FAILED exit=%s\n" "$?" > status' ERR
check_memory() {
    local free_mib
    free_mib=$(nvidia-smi -i 4 --query-gpu=memory.free --format=csv,noheader,nounits)
    if (( free_mib < 8000 )); then
        printf 'Insufficient GPU 4 free memory: %s MiB\n' "$free_mib"
        return 1
    fi
}
check_memory
printf 'SMOKE\n' > status
"$PY" "$PWD/train.py" --smoke > smoke.log 2>&1
test -f smoke_result.json
check_memory
printf 'TRAINING\n' > status
"$PY" "$PWD/train.py" > train.log 2>&1
printf 'TRAIN_COMPLETE\n' > status
