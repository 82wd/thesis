set -eu
cd "$(dirname "$0")"
py=/nas/liziyan103/anaconda3/envs/seatrack/bin/python
export CUDA_VISIBLE_DEVICES=6
test -s fit.json || "$py" -u decision.py >fit.log 2>&1
for mode in learned equal rgb_low ir_low; do
 "$py" -u eval.py "$mode" >"$mode.log" 2>&1
done
