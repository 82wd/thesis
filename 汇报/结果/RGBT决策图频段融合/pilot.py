from decision import *
from datetime import datetime,timezone,timedelta
import importlib.util
spec=importlib.util.spec_from_file_location('metrics',base/'pairwise_ss_20261103/evaluate_lasher.py')
metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
records={}
for name,frame in [('1blackteacher',165),('whitesuvturn',23)]:
    saved=root/'learned/RGBT_workspace/learned/LasHeR'/(name+'.txt')
    if not saved.exists():continue
    gt=metrics.load_boxes(base/'datasets/lasher/testingset'/name/'visible.txt')[0]
    branch={}
    for kind,path in [('original',archive/'RGBT_workspace/ss/LasHeR'/(name+'.txt')),('learned',saved)]:
        boxes=metrics.load_boxes(path)[0];assert len(gt)==len(boxes)
        curves,_=metrics.sequence_curves(boxes,gt)
        wh=np.maximum(0,np.minimum(boxes[:,:2]+boxes[:,2:],gt[:,:2]+gt[:,2:])-np.maximum(boxes[:,:2],gt[:,:2]))
        area=wh.prod(1);iou=area/np.maximum(gt[:,2:].prod(1)+boxes[:,2:].prod(1)-area,1e-12)
        branch[kind]=dict(frames=len(gt),SR=float(curves['success'].mean()),key_iou=float(iou[frame-1]))
    records[name]=branch
print(json.dumps(dict(time=datetime.now(timezone(timedelta(hours=8))).strftime('%m-%d %H:%M'),sequences=len(list((root/'learned/RGBT_workspace/learned/LasHeR').glob('*.txt'))),cases=records)))
