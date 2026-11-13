from pathlib import Path
import json
import numpy as np
root=Path(__file__).resolve().parent
base=Path('/nas/liziyan103/seatrack')
old=base/'training_runs/20261103_pairwise_ss/full_zCqHZl/eval_ep0060'
def read(path):return json.loads(path.read_text())
def vec(l,r):
    assert l['sequences']==245 and r['sequence_count']==234
    return np.array([100*l['scores'][x] for x in ('PR','NPR','SR')]+[r['rounded_reference_protocol'][x+'_percent'] for x in ('MPR','MSR')])
ref=vec(read(old/'LasHeR_ss.json'),read(old/'RGBT234_ss.json'))
result={'original_ss':ref.tolist()}
for mode in ('learned','equal','rgb_low','ir_low','feature_rgb_low','feature_ir_low'):
    l=read(root/mode/'LasHeR.json')
    r=read(root/mode/'RGBT234.json')
    lo=read(old/'LasHeR_ss.json');ro=read(old/'RGBT234_ss.json')
    assert {x['name']:(x['frames'],x['annotation_sha256']) for x in l['per_sequence']}=={x['name']:(x['frames'],x['annotation_sha256']) for x in lo['per_sequence']}
    def stamps(report):return {k:(v['frames'],v['sha256']['visible'],v['sha256']['infrared']) for k,v in report['sequences'].items()}
    assert stamps(r)==stamps(ro)
    v=vec(l,r)
    result[mode]=dict(percent=v.tolist(),delta_pp=(v-ref).tolist())
(root/'comparison.json').write_text(json.dumps(result,indent=2))
