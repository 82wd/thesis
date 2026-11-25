from pathlib import Path
import json,subprocess,shlex,hashlib
base=Path('/nas/liziyan103/seatrack'); exp=base/'training_runs/20261123_register'; out=exp/'eval_ep60_20261125';out.mkdir(exist_ok=True)
session='register_eval_20261125'
if subprocess.run(['tmux','has-session','-t',session],capture_output=True).returncode==0:
 print('ALREADY_RUNNING');raise SystemExit(0)
source=base/'training_runs/20261112_ss_template-only/full/pairwise_eval60.py'
s=source.read_text().replace("training_runs/20261112_ss_template-only","training_runs/20261123_register").replace("out = run / 'eval_ep0060'","out = exp / 'eval_ep60_20261125' / os.environ['REGISTER_VARIANT']").replace('checkpoints/rgbt_ss/','checkpoints/rgbt_register/').replace('experiments/seatrack/rgbt_ss.yaml','experiments/seatrack/rgbt_register.yaml')
snap=out/'runner_snapshot.py'
if not snap.exists():snap.write_bytes((base/'SEATrack/RGBT_workspace/test_rgbt_mgpus.py').read_bytes())
s=s.replace("runnerpath = base / 'SEATrack/RGBT_workspace/test_rgbt_mgpus.py'","runnerpath = exp / 'eval_ep60_20261125/runner_snapshot.py'")
s=s.replace('def params(*args):',"cfg.MODEL.REGISTER.GUIDANCE_SCALE = float(os.environ['REGISTER_W'])\nassert cfg.MODEL.REGISTER.ENABLED\nassert not cfg.MODEL.SS.ENABLED\nprint('REGISTER_CONFIG', cfg.MODEL.REGISTER, flush=True)\ndef params(*args):")
# Fail closed rather than silently evaluate incomplete trajectories.
s=s.replace("print('PROGRESS',ds,i,count,flush=True)","boxes = np.loadtxt(out/'RGBT_workspace/ss'/ds/(name+'.txt'))\n        rgb, ir, gt, _ = runner.genConfig(str(data/name), ds)\n        assert len(boxes)==len(rgb)==len(ir)==len(gt) and boxes.shape[1]==4 and np.isfinite(boxes).all(), name\n        print('PROGRESS',ds,i,count,flush=True)")
script=out/'evaluate.py';script.write_text(s)
manifest={'purpose':'predeclared w0 vs w1; no test-set scale selection','checkpoint':str(exp/'full/checkpoints/rgbt_register/SEATrack_ep0060.pth.tar'),'runner_sha256':hashlib.sha256(snap.read_bytes()).hexdigest(),'source_harness':str(source),'gpu':4,'variants':[0,1],'baseline_limit':'historical baseline; training budget comparability must be reported'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
launcher=out/'run.sh';launcher.write_text('''#!/bin/bash
set -eu
export CUDA_VISIBLE_DEVICES=4 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
cd '''+shlex.quote(str(out))+'''
echo RUNNING > status
trap 'echo FAILED > status' ERR
for w in 0 1; do
 export REGISTER_W=$w REGISTER_VARIANT=w$w
 /nas/liziyan103/anaconda3/envs/seatrack/bin/python evaluate.py >> w$w.log 2>&1
done
echo COMPLETE > status
''')
subprocess.run(['tmux','new-session','-d','-s',session,'bash '+shlex.quote(str(launcher))],check=True)
print('STARTED',out)
