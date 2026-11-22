"""Read-only ep60 gradient diagnosis; no optimizer steps or checkpoint writes."""
import os,sys,json,random,hashlib
from pathlib import Path
import numpy as np
import torch
ROOT=Path('/nas/liziyan103/seatrack/training_runs/20261116_ss_search')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
sys.path.insert(0,str(ROOT/'code/lib/train'))
os.chdir(ROOT/'code')
torch.set_num_threads(2)
import lib.train.train_script as ts
from lib.train.run_training import run_training
from lib.models.layers.attn import MergedLinear
original_loaders=ts.build_dataloaders
def loaders(cfg,settings):
    cfg.TRAIN.BATCH_SIZE=4;cfg.TRAIN.NUM_WORKER=0
    cfg.DATA.TRAIN.SAMPLE_PER_EPOCH=64;cfg.DATA.VAL.SAMPLE_PER_EPOCH=4
    settings.batchsize=4
    return original_loaders(cfg,settings)
ts.build_dataloaders=loaders
class Probe:
    def __init__(self,actor,loaders,optimizer,settings,*args,**kwargs):
        self.actor,self.loader,self.settings=actor,loaders[0],settings
    def train(self,*args,**kwargs):
        net=self.actor.net
        ck=ROOT/'output/checkpoints/rgbt_ss_search/SEATrack_ep0060.pth.tar'
        state=torch.load(ck,map_location='cpu');assert state['epoch']==60
        net.load_state_dict(state['net'],strict=True);del state
        # Saved after validation: merged LoRA. Match the established tracker convention.
        for m in net.modules():
            if isinstance(m,MergedLinear):m.merged=True
        net.train();self.actor.fix_bns()
        named=[(n,p) for n,p in net.named_parameters() if p.requires_grad]
        params=[p for _,p in named]
        (OUT/'parameter_manifest.json').write_text(json.dumps({'checkpoint':str(ck),'sha256':hashlib.sha256(ck.read_bytes()).hexdigest(),'parameters':[(n,p.numel()) for n,p in named],'mode':'train; head BN fixed; no optimizer.step; batch4; 3 sampling seeds x16 batches'},indent=2))
        rows=[]
        for seed in [101,202,303]:
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
            for i,data in enumerate(self.loader):
                data=data.to('cuda');data['epoch']=60;data['settings']=self.settings
                pred=self.actor.forward_pass(data)
                total,stats=self.actor.compute_losses(pred,data)
                ss=self.actor.cfg.TRAIN.SS_WEIGHT*pred['ss_loss'].mean()
                tracking=total-ss
                gt=torch.autograd.grad(tracking,params,retain_graph=True,allow_unused=True)
                gs=torch.autograd.grad(ss,params,allow_unused=True)
                t2=s2=dot=0.;connected=0
                for a,b in zip(gt,gs):
                    if a is not None:
                        assert torch.isfinite(a).all();t2+=a.double().square().sum().item()
                    if b is not None:
                        assert torch.isfinite(b).all();s2+=b.double().square().sum().item()
                    if a is not None and b is not None:
                        dot+=(a.double()*b.double()).sum().item();connected+=1
                assert t2>0 and s2>0
                row=dict(seed=seed,batch=i,tracking_loss=tracking.item(),weighted_ss=ss.item(),tracking_grad_norm=t2**.5,ss_grad_norm=s2**.5,ratio=(s2/t2)**.5,cosine=dot/(t2*s2)**.5,both_connected=connected)
                rows.append(row);print(json.dumps(row),flush=True)
                (OUT/'gradient_batches.json').write_text(json.dumps(rows,indent=2))
                del pred,total,ss,tracking,gt,gs,data
        summary={k:{'median':float(np.median([r[k] for r in rows])),'min':min(r[k] for r in rows),'max':max(r[k] for r in rows)} for k in ['ratio','cosine','tracking_grad_norm','ss_grad_norm']}
        summary.update(batches=len(rows),samples=len(rows)*4,negative_cosine_batches=sum(r['cosine']<0 for r in rows),scope='ep60 local multi-batch diagnosis; not historical training gradients; before clipping and Adam preconditioning')
        (OUT/'gradient_summary.json').write_text(json.dumps(summary,indent=2));print('PROBE_COMPLETE',summary,flush=True)
ts.LTRTrainer=Probe
run_training('seatrack','rgbt_ss_search',cudnn_benchmark=False,local_rank=-1,save_dir=str(OUT/'scratch'),base_seed=0,use_lmdb=False,use_wandb=False)
