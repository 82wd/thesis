import sys,os,subprocess
from pathlib import Path
root=Path('/nas/liziyan103/seatrack/training_runs/20261112_ss_half-weight')
sys.path[:0]=[str(root/'code'),str(root/'code/lib/train')];os.chdir(root/'code')
import torch
torch.set_num_threads(2)
import lib.train.train_script as ts
original_loaders=ts.build_dataloaders
def safe_loaders(cfg, settings):
 loaders=original_loaders(cfg, settings)
 for loader in loaders:
  if not loader.training:
   loader.num_workers=0
   loader.prefetch_factor=None
   if "--validate-only" in sys.argv: loader.dataset.samples_per_epoch=16
 return loaders
ts.build_dataloaders=safe_loaders
ck=root/'full/checkpoints/rgbt_ss/SEATrack_ep0024.pth.tar'
c=torch.load(ck,map_location='cpu');assert c['epoch']==24 and c['optimizer']['state'];print('RESUME_FROM',ck,'optimizer restored',flush=True);del c
from lib.train.trainers.base_trainer import BaseTrainer
old=BaseTrainer.train
def strict_train(self,*args,**kw):
 if '--validate-only' in sys.argv:
  self.load_checkpoint()
  for loader in self.loaders:
   if not loader.training: self.cycle_dataset(loader)
  print('VALIDATION_PREFLIGHT_COMPLETE',flush=True)
  return
 kw['fail_safe']=False
 return old(self,*args,**kw)
BaseTrainer.train=strict_train
from lib.train.run_training import run_training
run_training('seatrack','rgbt_ss',cudnn_benchmark=False,local_rank=-1,save_dir=str(root/'full'),base_seed=0,use_lmdb=False,use_wandb=False)
if '--validate-only' in sys.argv: sys.exit(0)
c=torch.load(root/'full/checkpoints/rgbt_ss/SEATrack_ep0060.pth.tar',map_location='cpu');assert c['epoch']==60;del c
subprocess.run([sys.executable,str(root/'full/pairwise_eval60.py')],check=True)
print('HALF_TRAIN_AND_EVAL_COMPLETE',flush=True)
