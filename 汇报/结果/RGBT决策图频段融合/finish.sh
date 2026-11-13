set -eu
cd "$(dirname "$0")"
while ! grep -qs EVALUATION_COMPLETE ir_low.log; do tmux has-session -t rgbt_decision_frequency || exit 1; sleep 60; done
export CUDA_VISIBLE_DEVICES=6
py=/nas/liziyan103/anaconda3/envs/seatrack/bin/python
for mode in feature_rgb_low feature_ir_low; do "$py" -u eval.py "$mode" >"$mode.log" 2>&1; done
"$py" summary.py
