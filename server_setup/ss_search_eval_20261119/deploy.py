from pathlib import Path
import hashlib, json, subprocess, shlex
base=Path('/nas/liziyan103/seatrack')
exp=base/'training_runs/20261116_ss_search'
out=exp/'eval_ep0060_20261119'
out.mkdir(exist_ok=True)
session='ss_search_eval60_20261119'
if subprocess.run(['tmux','has-session','-t',session],capture_output=True).returncode==0:
 print('EXISTING_SESSION',session);raise SystemExit(0)
source=base/'training_runs/20261112_ss_template-only/full/pairwise_eval60.py'
s=source.read_text().replace("training_runs/20261112_ss_template-only","training_runs/20261116_ss_search").replace("run = exp / 'full'","run = exp / 'output'").replace("out = run / 'eval_ep0060'","out = exp / 'eval_ep0060_20261119'").replace('checkpoints/rgbt_ss/','checkpoints/rgbt_ss_search/').replace('experiments/seatrack/rgbt_ss.yaml','experiments/seatrack/rgbt_ss_search.yaml')
# Preserve the known A/B evaluation protocol, with immutable runner snapshot.
runner=base/'SEATrack/RGBT_workspace/test_rgbt_mgpus.py'
snap=out/'runner_snapshot.py'
if not snap.exists(): snap.write_bytes(runner.read_bytes())
s=s.replace("runnerpath = base / 'SEATrack/RGBT_workspace/test_rgbt_mgpus.py'","runnerpath = out / 'runner_snapshot.py'")
s=s.replace("runner.rgbt_prompt_params.parameters = params", "runner.rgbt_prompt_params.parameters = params\nassert cfg.MODEL.SS.TEMPLATE_WEIGHT == 0.0 and cfg.MODEL.SS.SEARCH_WEIGHT == 0.5\nassert list(cfg.MODEL.SS.LAYERS) == [3,5,7,9,11]\nprint('CONFIG_VERIFIED', cfg.MODEL.SS, flush=True)\nprint('TRACKER_SOURCE', sys.modules['lib.test.tracker.seatrack'].__file__, flush=True)")
s=s.replace("print('PROGRESS',ds,i,count,flush=True)","result_path = out/'RGBT_workspace/ss'/ds/(name+'.txt')\n        boxes = np.loadtxt(result_path)\n        rgb, ir, gt, _ = runner.genConfig(str(data/name), ds)\n        assert len(rgb) == len(ir) == len(gt) == len(boxes), name\n        assert boxes.shape[1] == 4 and np.isfinite(boxes).all(), name\n        print('PROGRESS',ds,i,count,'frames',len(boxes),flush=True)")
script=out/'evaluate_search_only.py'
if script.exists(): assert script.read_text()==s,'Existing evaluation script differs'
else: script.write_text(s)
provenance={'source_harness':str(source),'source_harness_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(snap.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((exp/'code/experiments/seatrack/rgbt_ss_search.yaml').read_bytes()).hexdigest(),'gpu':1,'datasets':{'LasHeR':245,'RGBT234':234}}
(out/'launch_manifest.json').write_text(json.dumps(provenance,indent=2))
launcher=out/'run_eval.sh'
launcher.write_text('#!/bin/bash\nset -uo pipefail\nexport CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1\ncd '+shlex.quote(str(out))+'\nprintf "RUNNING\\n" > status\n/nas/liziyan103/anaconda3/envs/seatrack/bin/python '+shlex.quote(str(script))+' >> eval.log 2>&1\nrc=$?\nprintf "FINISHED exit=%s\\n" "$rc" > status\nexit "$rc"\n')
subprocess.run(['tmux','new-session','-d','-s',session,'bash '+shlex.quote(str(launcher))],check=True)
print('STARTED',session,str(out))
