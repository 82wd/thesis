"""Replay saved predecessor boxes through both trackers on identical frames."""
import copy
import csv
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

base = Path('/nas/liziyan103/seatrack')
exp = base / 'training_runs/20261103_pairwise_ss'
code = exp / 'code'
sys.path.insert(0, str(code))
os.chdir(code)
from lib.config.seatrack.config import cfg, update_config_from_file
from lib.test.utils import TrackerParams
from lib.test.tracker.seatrack import SEATrack
from lib.train.dataset.depth_utils import get_x_frame

def overlap(a, b):
    wh = np.maximum(0, np.minimum(a[:2]+a[2:], b[:2]+b[2:])-np.maximum(a[:2], b[:2]))
    inter = wh.prod()
    return inter/(a[2:].prod()+b[2:].prod()-inter)

def tracker(config, manifest, task, enabled):
    update_config_from_file(str(config))
    p = TrackerParams()
    p.cfg = copy.deepcopy(cfg)
    p.cfg.MODEL.SS.ENABLED = enabled
    p.cfg.MODEL.HMOE_RANK, p.cfg.MODEL.AMGLORA_RANK = 4, 8
    p.task, p.debug, p.save_all_boxes = task, 0, False
    p.checkpoint = json.loads(manifest.read_text())['checkpoint']
    for key in ['template_factor','template_size','search_factor','search_size']:
        setattr(p,key,getattr(p.cfg.TEST,key.upper()))
    return SEATrack(p)

torch.set_num_threads(2)
torch.cuda.set_per_process_memory_fraction(.2)
import math
from lib.train.data.processing_utils import sample_target
from PIL import Image
out=Path(sys.argv[1]).resolve()
old=base/'SEATrack/RGBT_workspace/self_rgbt_ep0060'
new=exp/'full_zCqHZl/eval_ep0060'
conf=code/'experiments/seatrack/rgbt_ss.yaml'
dirs=[old/'LasHeR',new/'RGBT_workspace/ss/LasHeR']
models=[tracker(conf,p/'checkpoint_used.json','rgbt',i==1) for i,p in enumerate((old,new))]
# The archived SS predecessor fixes the crop for every weight and every fusion.
cases=[('1blackteacher',165),('whitesuvturn',23)]
for name in sorted(p.stem for p in dirs[0].glob('*.txt')):
    if name in dict(cases):continue
    folder=base/'datasets/lasher/testingset'/name
    gt=np.loadtxt(folder/'visible.txt',delimiter=',')
    if len(gt)<56:continue
    tracks=[np.loadtxt(d/(name+'.txt')) for d in dirs]
    if all(overlap(pred[j],gt[j])>=.65 for pred in tracks for j in range(44,55)):
        cases.append((name,50))
    if len(cases)==8:break
modes=['original','rgb_low','ir_low','rgb_low_rms','ir_low_rms']
rows=[]; maps={}
y=torch.fft.fftfreq(16,device='cuda')[:,None];x=torch.fft.rfftfreq(16,device='cuda')[None,:]
low=(x.square()+y.square()<=.25**2)
state={}
def capture(module,args,output):
    state['tokens'].append(output[:,-256:])
def fuse(module,args,output):
    full,aux=output
    rgb,ir=state['tokens']
    assert torch.equal(rgb+ir,full)
    mode=state['mode']
    if mode=='original':return
    def transform(t):
        return torch.fft.rfft2(t.transpose(1,2).reshape(1,-1,16,16))
    a,b=transform(rgb),transform(ir)
    z=torch.where(low,a,b) if mode.startswith('rgb_low') else torch.where(low,b,a)
    feat=torch.fft.irfft2(z,s=(16,16)).flatten(2).transpose(1,2)
    if mode.endswith('rms'):
        feat=feat*(full.square().mean()/feat.square().mean().clamp_min(1e-12)).sqrt()
    return feat,aux
def capture_head(module,args,output):
    state['raw']=output[0].detach()
for m in models:
    m.network.backbone.norm.register_forward_hook(capture)
    m.network.backbone.register_forward_hook(fuse)
    m.network.box_head.register_forward_hook(capture_head)
for name,onset in cases:
    folder=base/'datasets/lasher/testingset'/name
    gt=np.loadtxt(folder/'visible.txt',delimiter=',')
    pred=[np.loadtxt(d/(name+'.txt')) for d in dirs]
    files=[sorted((folder/k).glob('*.jpg')) for k in ['visible','infrared']]
    def read(j):return get_x_frame(str(files[0][j]),str(files[1][j]),dtype='rgbrgb')
    for m in models:m.initialize(read(0),{'init_bbox':gt[0].astype(np.float32).tolist()})
    for fr in range(onset-5,onset+6):
        j=fr-1; prev=pred[1][j-1].tolist(); im=read(j)
        side=math.ceil(math.sqrt(prev[2]*prev[3])*4)
        origin=np.round(np.array(prev[:2])+.5*np.array(prev[2:])-.5*side)
        def project(box):return np.r_[(box[:2]-origin)/side,box[2:]/side]
        for idx,m in enumerate(models):
            for mode in modes:
                state.update(mode=mode,tokens=[])
                m.state=prev.copy();m.frame_id=j-1
                box=np.array(m.track(im)['target_bbox'])
                if idx==1 and mode=='original':assert abs(box-pred[1][j]).max()<1e-4,(name,fr,box,pred[1][j])
                response=(m.output_window*state['raw']).squeeze().cpu().numpy()
                assert response.shape==(16,16) and np.isfinite(response).all()
                record=dict(sequence=name,frame=fr,model=['baseline','ss'][idx],mode=mode,iou=float(overlap(box,gt[j])),box=box.tolist())
                if name=='1blackteacher' and fr==165:
                    ref=project(gt[j]); wrong=project(pred[1][j])
                    axis=(np.arange(16)+.5)/16
                    def peak(b):
                        inside=(axis>=b[0])&(axis<b[0]+b[2])
                        vertical=(axis>=b[1])&(axis<b[1]+b[3])
                        return float(response[np.ix_(vertical,inside)].max())
                    record.update(target_peak=peak(ref),other_peak=peak(wrong))
                    maps[f'{idx}_{mode}']=response
                    maps.update(gt=ref,other=wrong)
                    maps[f'box_{idx}_{mode}']=project(box)
                    if idx==1 and mode=='original':
                        patch=sample_target(im,prev,4,output_sz=256)[0]
                        Image.fromarray(patch[:,:,:3]).save(out/'crop.png')
                rows.append(record)
    print(name,'done',flush=True)
np.savez(out/'maps.npz',**maps)
(out/'observations.json').write_text(json.dumps(rows))
