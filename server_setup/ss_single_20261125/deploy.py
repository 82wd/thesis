"""Run on server with the SEATrack Python; creates a new isolated sequential queue."""
from pathlib import Path
import shutil
import subprocess
import json
import hashlib
import yaml

base = Path('/nas/liziyan103/seatrack/training_runs')
source = base / '20261116_ss_search'
root = base / '20261125_ss_single'
root.mkdir(exist_ok=False)
shutil.copytree(source / 'code', root / 'code', symlinks=True,
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
local = root / 'code/lib/train/admin/local.py'
local.write_text(local.read_text().replace(str(source), str(root)))
manifest = {'source': str(source / 'code'), 'layers': [3,5,7,9,11],
            'seed': 0, 'effective_ss_weight': 0.05, 'configs': {}}
for layer in manifest['layers']:
    name = f'rgbt_ss_search_l{layer}'
    path = root / f'code/experiments/seatrack/{name}.yaml'
    cfg = yaml.safe_load(path.read_text())
    assert cfg['MODEL']['SS']['LAYERS'] == [layer]
    assert cfg['MODEL']['SS']['TEMPLATE_WEIGHT'] == 0
    assert cfg['MODEL']['SS']['SEARCH_WEIGHT'] * cfg['TRAIN']['SS_WEIGHT'] == 0.05
    assert cfg['TRAIN']['BATCH_SIZE'] == 32 and cfg['TRAIN']['EPOCH'] == 60
    assert Path(cfg['MODEL']['PRETRAIN_FILE']).is_file()
    manifest['configs'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    cfg['TRAIN'].update(EPOCH=2, VAL_EPOCH_INTERVAL=1, SAVE_EPOCH_INTERVAL=1, PRINT_INTERVAL=1)
    cfg['DATA']['TRAIN']['SAMPLE_PER_EPOCH'] = 64
    cfg['DATA']['VAL']['SAMPLE_PER_EPOCH'] = 32
    (path.parent / f'{name}_smoke.yaml').write_text(yaml.safe_dump(cfg))
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
queue = r'''
from pathlib import Path
import subprocess, os, time, fcntl
r = Path(__file__).resolve().parent
lock = (r/'queue.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
py = '/nas/liziyan103/anaconda3/envs/seatrack/bin/python'
def status(s):
    (r/'status').write_text(s)
    print(time.strftime('%Y-%m-%d %H:%M:%S'), s, flush=True)
def idle_gpu():
    rows = subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).splitlines()
    used = subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
    for row in rows:
        index, uuid, free, util = [v.strip() for v in row.split(',')]
        if uuid not in used and int(free)>22000 and int(util)<10:
            return index
def train(config, dest, gpu, epoch):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu, LOCAL_RANK='-1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONUNBUFFERED='1')
    with (r/f'{config}.log').open('x') as f:
        rc = subprocess.run([py,'lib/train/run_training.py','--script','seatrack','--config',config,'--save_dir',str(dest),'--seed','0'],cwd=r/'code',env=env,stdout=f,stderr=subprocess.STDOUT).returncode
    checkpoints = list(dest.rglob(f'*ep{epoch:04d}.pth.tar'))
    log = (r/f'{config}.log').read_text(errors='replace')
    if rc or not any(p.stat().st_size>0 for p in checkpoints) or 'Finished training!' not in log:
        raise RuntimeError(f'{config} failed: exit={rc}, checkpoints={checkpoints}')
try:
    status('TESTING')
    with (r/'tests.log').open('w') as f:
        subprocess.run([py,'-m','unittest','discover','-s','tests','-v'],cwd=r/'code',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2'),stdout=f,stderr=subprocess.STDOUT,check=True)
    for layer in [3,5,7,9,11]:
        name = f'rgbt_ss_search_l{layer}'
        status(f'WAITING_GPU layer={layer}; requires no compute processes, >22000MiB free, <10% utilization')
        while True:
            gpu = idle_gpu()
            if gpu is not None:
                time.sleep(10)
                if idle_gpu() == gpu: break
            time.sleep(30)
        status(f'SMOKE layer={layer} GPU={gpu}')
        train(name+'_smoke',r/f'l{layer}/smoke',gpu,2)
        status(f'TRAINING layer={layer} GPU={gpu}')
        train(name,r/f'l{layer}/full',gpu,60)
        (r/f'l{layer}/TRAIN_COMPLETE').write_text('ep60 present; final full benchmark pending')
    status('ALL_TRAIN_COMPLETE; full benchmark pending')
except Exception as e:
    status('FAILED '+repr(e))
    raise
'''
(root/'queue.py').write_text(queue)
subprocess.run(['tmux','new-session','-d','-s','ss_single_20261125',
                f'/nas/liziyan103/anaconda3/envs/seatrack/bin/python -u {root}/queue.py > {root}/queue.log 2>&1'],check=True)
print(root)
