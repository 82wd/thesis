import json
import math
import os
from pathlib import Path
import random
import re
import sys

import numpy as np
import torch
import torch.nn.functional as F

root = Path(__file__).resolve().parent
base = Path('/nas/liziyan103/seatrack')
old = base/'training_runs/20261103_pairwise_ss'
code = old/'code'
archive = old/'full_zCqHZl/eval_ep0060'
sys.path.insert(0,str(code))
from lib.test.tracker.seatrack import SEATrack
from lib.config.seatrack.config import cfg, update_config_from_file
from lib.test.utils import TrackerParams
from lib.train.dataset.depth_utils import get_x_frame

def params(*args):
    update_config_from_file(str(code/'experiments/seatrack/rgbt_ss.yaml'))
    p=TrackerParams()
    p.cfg,p.task,p.debug,p.save_all_boxes=cfg,'rgbt',0,False
    p.checkpoint=json.loads((archive/'checkpoint_used.json').read_text())['checkpoint']
    for key in ['template_factor','template_size','search_factor','search_size']:
        setattr(p,key,getattr(cfg.TEST,key.upper()))
    return p

def mix(logits,weights):
    # logits shape [N,2,H,W]. RGB weight in each band, IR gets its complement.
    h,w=logits.shape[-2:]
    radial=torch.fft.fftfreq(h,device=logits.device)[:,None]**2+torch.fft.rfftfreq(w,device=logits.device)[None,:]**2
    alpha=torch.where(radial<=.25**2,weights[0],weights[1])
    rgb,ir=torch.fft.rfft2(logits).unbind(1)
    return torch.fft.irfft2(alpha*rgb+(1-alpha)*ir,s=(h,w)).unsqueeze(1)

class DecisionTracker(SEATrack):
    def __init__(self,p,method='collect',weights=None):
        super().__init__(p)
        self.method=method
        self.weights=weights
        self.branches=[]
        self.network.backbone.norm.register_forward_hook(self.capture)
        self.network.box_head.register_forward_hook(self.replace)

    def capture(self,module,args,out):
        self.branches.append(out[:,-256:])

    def replace(self,head,args,out):
        rgb,ir=self.branches
        self.branches.clear()
        shape=args[0].shape
        assert torch.equal((rgb+ir).transpose(1,2).reshape(shape),args[0])
        if self.method=='original':return
        # Shared frozen center classifier. Keep the fused size/offset maps.
        x=torch.cat((rgb,ir)).transpose(1,2).reshape(2,*shape[1:])
        x=head.conv5_ctr(head.conv4_ctr(head.conv3_ctr(head.conv2_ctr(head.conv1_ctr(x)))))
        self.logits=x.transpose(0,1)
        if self.method=='collect':return
        center=mix(self.logits,self.weights).sigmoid().clamp(1e-4,1-1e-4)
        return center,head.cal_bbox(center,out[2],out[3]),out[2],out[3]

def gather(model,split,count):
    spec=code/'lib/train/data_specs'
    names=(spec/('lasher_'+split+'.txt')).read_text().splitlines()
    allowed=set(names)
    if split=='train':allowed-=set((spec/'lasher_val.txt').read_text().splitlines())
    allowed-=set((spec/'lasher_test.txt').read_text().splitlines())
    allowed-=set(p.name for p in (base/'datasets/lasher/testingset').iterdir() if p.is_dir())
    rng=random.Random(20261112)
    names=sorted(allowed);rng.shuffle(names)
    samples=[];used=[]
    for name in names:
        d=base/'datasets/lasher/trainingset'/name
        if not (d/'visible.txt').is_file():continue
        gt=np.loadtxt(d/'visible.txt',delimiter=',',ndmin=2)
        files=[{int(re.search(r'(\d+)\.jpg$',q.name).group(1)):q for q in (d/k).glob('*.jpg')} for k in ('visible','infrared')]
        # Dataset reader uses annotation row index as numeric file ID.
        valid=[j for j in range(len(gt)) if j in files[0] and j in files[1] and min(gt[j,2:])>2 and np.isfinite(gt[j]).all()]
        ids=set(valid)
        pairs=[j for j in valid if j-1 in ids and j>valid[0]+5]
        if len(pairs)<8:continue
        def image(j):return get_x_frame(*[str(f[j]) for f in files],dtype='rgbrgb')
        model.initialize(image(valid[0]),{'init_bbox':gt[valid[0]].astype(np.float32).tolist()})
        group=[]
        for j in rng.sample(pairs,min(24,len(pairs))):
            prev=gt[j-1].copy()
            prev[:2]+=np.array([rng.uniform(-.5,.5),rng.uniform(-.5,.5)])*prev[2:]
            side=math.ceil(math.sqrt(prev[2]*prev[3])*4)
            origin=np.round(prev[:2]+.5*prev[2:]-.5*side)
            cell=np.floor((gt[j,:2]+.5*gt[j,2:]-origin)*16/side).astype(int)
            if min(cell)<0 or max(cell)>15:continue
            model.state=prev.tolist()
            model.track(image(j))
            group.append((model.logits.cpu(),int(cell[1]*16+cell[0]),name,j))
            if len(group)==8:break
        if len(group)==8:
            samples.extend(group);used.append(name)
        if len(used)==count:break
    assert len(used)==count,(split,len(used))
    return torch.cat([r[0] for r in samples]),torch.tensor([r[1] for r in samples]),[(r[2],r[3]) for r in samples]

def fit():
    torch.manual_seed(0)
    m=DecisionTracker(params())
    tr,ty,tids=gather(m,'train',48)
    va,vy,vids=gather(m,'val',16)
    assert not ({n for n,_ in tids}&{n for n,_ in vids})
    theta=torch.nn.Parameter(torch.zeros(2))
    opt=torch.optim.Adam([theta],lr=.06)
    def loss(x,y,w):return F.cross_entropy(mix(x,w).flatten(1),y)
    for i in range(150):
        opt.zero_grad()
        cost=loss(tr,ty,theta.sigmoid());cost.backward()
        assert torch.isfinite(theta.grad).all()
        if i==0:initial_grad=theta.grad.tolist();assert theta.grad.norm()>0
        opt.step()
    weights=theta.detach().sigmoid()
    report=dict(weights=weights.tolist(),initial_grad=initial_grad,train=tids,val=vids,score={})
    for mode,w in [('equal',[.5,.5]),('rgb_low',[1.,0.]),('ir_low',[0.,1.]),('learned',weights.tolist())]:
        w=torch.tensor(w)
        report['score'][mode]=[float(loss(tr,ty,w)),float(loss(va,vy,w))]
    assert torch.allclose(mix(va[:2],torch.tensor([.5,.5])),va[:2].mean(1,keepdim=True),atol=1e-5)
    (root/'fit.tmp').write_text(json.dumps(report,indent=2))
    os.replace(root/'fit.tmp',root/'fit.json')
    print('FIT_COMPLETE',weights.tolist(),report['score'],flush=True)

if __name__=='__main__':
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(.18)
    fit()
