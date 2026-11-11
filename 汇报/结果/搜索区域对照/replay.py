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
out = Path(sys.argv[1])
with out.open('w') as f:
    w = csv.writer(f)
    w.writerow(['sequence','frame','model','previous_box','iou','original_iou','max_box_diff_px'])
    for task in ('rgbe','rgbt'):
        event = task=='rgbe'
        ds = 'VisEvent' if event else 'LasHeR'
        old = base/'SEATrack'/('RGBE_workspace/self_rgbe_ep0045' if event else 'RGBT_workspace/self_rgbt_ep0060')
        run = base/'training_runs/rgbe_pairwise_ss/run_PzOoDM' if event else exp/'full_zCqHZl'
        new = run/('eval_ep0045' if event else 'eval_ep0060')
        conf = run/'rgbe_ss_PzOoDM.yaml' if event else code/'experiments/seatrack/rgbt_ss.yaml'
        models = [tracker(conf, p/'checkpoint_used.json',task,i==1) for i,p in enumerate((old,new))]
        cases = [('dvSave-2021_02_06_17_21_41_personFootball',63),('dvSave-2021_02_06_09_14_18_girl1',60),('dvSave-2021_02_06_08_57_35_machineBrad',152)] if event else [('whitesuvturn',23),('1blackteacher',165)]
        for name, onset in cases:
            folder=base/'datasets'/('visevent/test_subset' if event else 'lasher/testingset')/name
            frames=[sorted((folder/k).glob(pattern)) for k,pattern in ([('vis_imgs','*.bmp'),('event_imgs','*.bmp')] if event else [('visible','*.jpg'),('infrared','*.jpg')])]
            offset=int(np.loadtxt(folder/'absent_label.txt').argmax()) if event else 0
            gt=np.loadtxt(folder/('groundtruth.txt' if event else 'visible.txt'),delimiter=',')[offset:]
            tracks=[np.loadtxt(p/ds/(name+'.txt'),delimiter=',' if event else None) for p in (old,new/('RGBE_workspace' if event else 'RGBT_workspace')/'ss')]
            assert len(gt)==len(tracks[0])==len(tracks[1])
            def image(j):return get_x_frame(str(frames[0][j+offset]),str(frames[1][j+offset]),dtype='rgbrgb')
            for m in models:m.initialize(image(0),{'init_bbox':gt[0].astype(np.float32).tolist()})
            for frame in range(onset-10,onset+16):
                j=frame-1
                if min(gt[j][2:]) <= 0: continue
                im=image(j)
                for i,m in enumerate(models):
                    for key,prev in zip(('baseline','ss','gt'),(tracks[0],tracks[1],gt)):
                        if min(prev[j-1][2:]) <= 0: continue
                        m.state=prev[j-1].tolist()
                        m.frame_id=j-1
                        box=np.array(m.track(im)['target_bbox'])
                        w.writerow([name,frame,['baseline','ss'][i],key,overlap(box,gt[j]),overlap(tracks[i][j],gt[j]),np.max(abs(box-tracks[i][j]))])
            f.flush()
            print(name,'done',flush=True)
