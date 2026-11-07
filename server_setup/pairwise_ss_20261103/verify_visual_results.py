"""Verify saved trajectories, images, videos and SS matrix statistics after generation."""
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
root=Path(sys.argv[1])
assert (root/'COMPLETE.txt').exists()
manifest=json.loads((root/'manifest.json').read_text())
metrics=json.loads((root/'diagnostics.json').read_text())
report={}
for name in manifest['sequences']:
    folder=root/name
    info=json.loads((folder/'frames.json').read_text())
    for label in ['Baseline','SS']:
        boxes=np.loadtxt(str(folder/(label+'.txt')),ndmin=2)
        assert boxes.shape==(info['processed'],4) and np.isfinite(boxes).all() and (boxes[:,2:]>0).all()
    cap=cv2.VideoCapture(str(folder/'tracking.mp4'))
    assert cap.isOpened()
    count=0
    while True:
        ok,frame=cap.read()
        if not ok:
            break
        count+=1
    cap.release()
    assert count==info['processed'],(name,count)
    for path in folder.glob('*.png'):
        assert cv2.imread(str(path)) is not None,str(path)
    for path in folder.glob('*.jpg'):
        assert cv2.imread(str(path)) is not None,str(path)
    records=[m for m in metrics if m['sequence']==name]
    for record in records:
        path=folder/('matrices_%04d.npz'%record['frame'])
        with np.load(str(path)) as data:
            key='%s_L%d_%s_'%(record['model'],record['layer_input'],record['region'])
            a,b=data[key+'RGB'],data[key+'Thermal']
            assert a.shape==b.shape==((64,64) if record['region']=='template' else (256,256))
            assert np.isfinite(a).all() and np.isfinite(b).all()
            assert np.allclose(a,a.T,atol=1e-6) and np.allclose(np.diag(a),1,atol=1e-5)
            assert np.isclose(((a-b)**2).mean(),record['mse'],rtol=1e-5)
    report[name]=dict(decoded_video_frames=count,diagnostic_records=len(records))
(root/'verification.json').write_text(json.dumps(report,indent=2))
hashes={}
for path in sorted(root.rglob('*')):
    if path.is_file() and path.name!='sha256.json':
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                h.update(chunk)
        hashes[str(path.relative_to(root))]=h.hexdigest()
(root/'sha256.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(report,indent=2))
