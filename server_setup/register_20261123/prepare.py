"""Prepare only the new isolated register run; refuse to overwrite artifacts."""
from pathlib import Path
import hashlib
import json
import shutil
import yaml

root = Path(__file__).resolve().parent
code = root / 'code'
source = Path('/nas/liziyan103/seatrack/training_runs/20261112_ss_half-weight/code')
assert not (root / 'manifest.json').exists(), 'Already prepared'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
original = {str(p.relative_to(code)): sha(p) for p in code.rglob('*') if p.is_file()}
inherited = {}
for name in ['lib/train/trainers/accumulation.py', 'lib/train/trainers/ltr_trainer.py',
             'lib/train/dataset/lasher.py', 'lib/train/admin/local.py']:
    src = source / name
    inherited[name] = {'source': str(src), 'sha256': sha(src)}
    shutil.copy2(src, code / name)
assert '_frame_cache' in (code/'lib/train/dataset/lasher.py').read_text()
p = code/'lib/train/trainers/ltr_trainer.py'
s = p.read_text()
assert 'accumulator.backward(loss)' in s
s = s.replace("print('Effective batch: 64; microbatch: 4; accumulation: 16; updates/epoch:', len(loader)//accumulation_steps, flush=True)",
              "print('Effective batch:', loader.batch_size * accumulation_steps, 'microbatch:', loader.batch_size, 'accumulation:', accumulation_steps, 'updates/epoch:', len(loader)//accumulation_steps, flush=True)")
p.write_text(s)
p = code/'lib/train/admin/local.py'
s = p.read_text()
import re
s = re.sub(r"self.workspace_dir = '[^']*'", f"self.workspace_dir = '{root}/full'", s)
s = re.sub(r"self.tensorboard_dir = '[^']*'", f"self.tensorboard_dir = '{root}/tensorboard'", s)
p.write_text(s)
pretrain = Path('/nas/liziyan103/seatrack/SEATrack/SEATrack-main/pretrained/vitb_256_mae_ce_32x4_ep300/OSTrack_ep0300.pth.tar')
assert pretrain.is_file()
config = yaml.safe_load((code/'experiments/seatrack/rgbt_register.yaml').read_text())
config['MODEL']['PRETRAIN_FILE'] = str(pretrain)
config['TRAIN'].update(BATCH_SIZE=4, NUM_WORKER=2, PRINT_INTERVAL=80, SAVE_EPOCH_INTERVAL=5)
assert config['DATA']['TRAIN']['SAMPLE_PER_EPOCH'] % 32 == 0
for name in ['rgbt_register', 'rgbt_register_guidance']:
    config['MODEL']['REGISTER']['GUIDANCE_SCALE'] = float(name.endswith('guidance'))
    (code/f'experiments/seatrack/{name}.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
config['MODEL']['REGISTER']['GUIDANCE_SCALE'] = 0.0
config['TRAIN'].update(EPOCH=1, PRINT_INTERVAL=1, VAL_EPOCH_INTERVAL=1, SAVE_EPOCH_INTERVAL=1)
config['DATA']['TRAIN']['SAMPLE_PER_EPOCH'] = 64
config['DATA']['VAL']['SAMPLE_PER_EPOCH'] = 16
(code/'experiments/seatrack/rgbt_register_smoke.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
data = Path('/nas/liziyan103/seatrack/datasets/lasher/trainingset')
for split in ['train', 'val']:
    names = (code/f'lib/train/data_specs/lasher_{split}.txt').read_text().splitlines()
    missing = [n for n in names if not (data/n/'visible.txt').is_file()]
    assert not missing, (split, missing)
    print('DATA_SPLIT', split, len(names), flush=True)
manifest = dict(source_commit='d0f2a45', branch='experiment/register-guidance-1118',
    source_files=original, inherited=inherited, pretrain=str(pretrain), pretrain_sha256=sha(pretrain),
    microbatch=4, accumulation_steps=8, effective_batch=32, seed=0,
    validation_workers=0, train_samples=60000, val_samples=60000,
    epochs=60, updates_per_epoch=1875,
    deployed_files={str(p.relative_to(code)): sha(p) for p in code.rglob('*') if p.is_file()})
(root/'manifest.json').write_text(json.dumps(manifest, indent=2))
print('PREPARED', root, flush=True)
