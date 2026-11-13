from decision import *
import importlib.util
import subprocess
import hashlib
import fcntl
mode=sys.argv[1]
out=root/mode
out.mkdir(exist_ok=True)
lock=(out/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.chdir(out)
torch.set_num_threads(2);torch.cuda.set_per_process_memory_fraction(.18)
report=json.loads((root/'fit.json').read_text())
weights={'feature_rgb_low':[1.,0.],'feature_ir_low':[0.,1.],'equal':[.5,.5],'rgb_low':[1.,0.],'ir_low':[0.,1.],'learned':report['weights']}[mode]
w=torch.tensor(weights,device='cuda')
p=params()
record=json.loads((archive/'checkpoint_used.json').read_text())
assert subprocess.check_output(['sha256sum',p.checkpoint]).decode().split()[0]==record['sha256']
manifest=dict(checkpoint=record,weights=weights,method=mode)
file=out/'manifest.json'
if file.exists():assert json.loads(file.read_text())==manifest
file.write_text(json.dumps(manifest))
spec=importlib.util.spec_from_file_location('runner',base/'SEATrack/RGBT_workspace/test_rgbt_mgpus.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
runner.rgbt_prompt_params.parameters=lambda *args:p
if mode.startswith('feature_'):
    from feature_eval import FeatureTracker
    runner.SEATrack=lambda params:FeatureTracker(params,mode,w)
else:
    runner.SEATrack=lambda params:DecisionTracker(params,mode,w)
save=np.savetxt
def atomic(path,boxes):
    assert np.isfinite(boxes).all()
    save(path+'.tmp',boxes);os.replace(path+'.tmp',path)
runner.np.savetxt=atomic
for ds,folder,n in [('LasHeR','lasher/testingset',245),('RGBT234','rgbt234',234)]:
    data=base/'datasets'/folder
    names=sorted(x.name for x in data.iterdir() if x.is_dir())
    ref=archive/'RGBT_workspace/ss'/ds
    assert len(names)==n and set(names)=={x.stem for x in ref.glob('*.txt')}
    # The order only changes availability of the two diagnostic trajectories.
    names.sort(key=lambda x:(x not in ('whitesuvturn','1blackteacher'),x))
    for i,name in enumerate(names,1):
        runner.run_sequence(name,str(data),ds,'rgbt',num_gpu=1,epoch=60,script_name='seatrack',variants=mode,hmoe_rank='4',amglora_rank='8')
        track=out/'RGBT_workspace'/mode/ds/(name+'.txt')
        assert np.loadtxt(track,ndmin=2).shape==np.loadtxt(ref/(name+'.txt'),ndmin=2).shape
        print('PROGRESS',ds,i,n,name,flush=True)
    sc=base/('pairwise_ss_20261103/evaluate_lasher.py' if ds=='LasHeR' else 'evaluate_rgbt234.py')
    subprocess.run([sys.executable,str(sc),'--data-root' if ds=='LasHeR' else '--dataset',str(data),'--results',str(track.parent),'--output',str(out/(ds+'.json'))],check=True)
print('EVALUATION_COMPLETE',flush=True)
