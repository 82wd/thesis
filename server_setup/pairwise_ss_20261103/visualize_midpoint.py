"""Read-only epoch-matched tracking and fixed-crop SS diagnostics (Python 3.8)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from copy import deepcopy


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--code', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--ss', type=Path, required=True)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--gpu', type=int, required=True)
    p.add_argument('--frames', type=int, default=300)
    p.add_argument('--sequences', nargs='+')
    p.add_argument('--epoch', type=int, default=20)
    args = p.parse_args()
    if args.frames < 2 or args.epoch != 20:
        p.error('This audited runner supports epoch 20 (validation checkpoint) and >=2 frames.')
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    os.environ['MPLBACKEND'] = 'Agg'
    sys.path.insert(0, str(args.code.resolve()))
    import cv2
    import numpy as np
    import torch
    import torch.nn.functional as F
    import matplotlib.pyplot as plt
    from lib.config.seatrack.config import cfg, update_config_from_file
    from lib.test.utils import TrackerParams
    from lib.test.tracker.seatrack import SEATrack
    from lib.train.dataset.depth_utils import get_x_frame
    from lib.train.data.processing_utils import sample_target

    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(0.22)
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.backends.cudnn.benchmark = False
    names = sorted(x.name for x in args.data.iterdir() if x.is_dir())
    selected = args.sequences or random.Random(20261104).sample(names, 3)
    if any(n not in names for n in selected):
        raise ValueError('Unknown sequence')
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = dict(epoch=20, gpu=args.gpu, sequences=selected, max_frames=args.frames,
                    selection='explicit' if args.sequences else 'seed20261104 sample of sorted test folders',
                    diagnostic='GT-centered fixed search crops; NOT tracking predictions',
                    lora='epoch20 saved after validation; merged checkpoint convention',
                    code=str(args.code), script_sha256=sha(__file__), checkpoints={})
    trackers = {}
    for label, checkpoint, config in [('Baseline', args.baseline, 'rgbt_ss_baseline'), ('SS', args.ss, 'rgbt_ss')]:
        meta = torch.load(str(checkpoint), map_location='cpu')
        if meta.get('epoch') != 20:
            raise ValueError('Checkpoint epoch is not 20: ' + str(checkpoint))
        del meta
        config_path = args.code / 'experiments/seatrack' / (config + '.yaml')
        update_config_from_file(str(config_path))
        if cfg.TRAIN.VAL_EPOCH_INTERVAL != 5 or any(r != 1 for r in cfg.MODEL.BACKBONE.CE_KEEP_RATIO):
            raise ValueError('Unexpected validation interval or pruned tokens')
        params = TrackerParams()
        params.cfg = deepcopy(cfg)
        params.checkpoint = str(checkpoint)
        params.task = 'rgbt'
        params.debug = 0
        params.save_all_boxes = False
        for region in ('template', 'search'):
            setattr(params, region + '_factor', getattr(cfg.TEST, region.upper() + '_FACTOR'))
            setattr(params, region + '_size', getattr(cfg.TEST, region.upper() + '_SIZE'))
        trackers[label] = SEATrack(params)
        manifest['checkpoints'][label] = dict(path=str(checkpoint), sha256=sha(checkpoint),
                                             config=str(config_path), config_sha256=sha(config_path))
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    metrics = []

    def box(im, xywh, color):
        if np.isfinite(xywh).all() and min(xywh[2:]) > 0:
            x, y, w, h = np.rint(xywh).astype(int)
            cv2.rectangle(im, (x, y), (x+w, y+h), color, 2)

    def panel(rgb, thermal, gt, preds, name, frame):
        im = rgb.copy()
        box(im, gt, (0, 220, 0))
        box(im, preds['Baseline'], (255, 100, 0))
        box(im, preds['SS'], (0, 60, 255))
        # Predictions are in visible-image coordinates; do not reuse on thermal.
        ir = cv2.resize(thermal, (im.shape[1], im.shape[0]))
        combined = np.hstack([im, ir])
        combined = cv2.resize(combined, (1200, int(combined.shape[0]*1200/combined.shape[1])))
        header = np.zeros((64, 1200, 3), dtype=np.uint8)
        cv2.putText(header, '%s | frame %d | epoch 20' % (name, frame), (10, 23), 0, .6, (255,255,255), 1)
        for text, x, color in [('GT',10,(0,220,0)), ('Baseline',100,(255,100,0)), ('SS',250,(0,60,255)), ('Thermal context (no predicted boxes)',610,(255,255,255))]:
            cv2.putText(header, text, (x, 51), 0, .55, color, 1)
        return np.vstack([header, combined])

    def diagnostic(image, gt, folder, frame):
        matrices = {}
        for label, tracker in trackers.items():
            hooks = []
            def capture(layer):
                def hook(module, inputs):
                    streams = inputs[0]
                    for region, part in [('template', slice(0,64)), ('search', slice(64,320))]:
                        gram = []
                        for stream in streams:
                            v = F.normalize(stream[:, part].detach().float(), dim=-1)
                            gram.append((v @ v.transpose(-1,-2))[0].cpu().numpy())
                        matrices[(label, layer, region)] = gram
                return hook
            for layer in [3,5,7,9,11]:
                hooks.append(tracker.network.backbone.blocks[layer].register_forward_pre_hook(capture(layer)))
            try:
                crop, _, _ = sample_target(image, gt.tolist(), tracker.params.search_factor, output_sz=tracker.params.search_size)
                with torch.no_grad():
                    tracker.network(template=tracker.z_tensor, search=tracker.preprocessor.process(crop), ce_template_mask=tracker.box_mask_z)
            finally:
                for hook in hooks:
                    hook.remove()
            if label == 'Baseline':
                cv2.imwrite(str(folder / ('crop_%04d.jpg' % frame)), cv2.cvtColor(crop[:,:,:3], cv2.COLOR_RGB2BGR))
        arrays = {}
        for layer in [3,5,7,9,11]:
            for region in ['template','search']:
                fig, axes = plt.subplots(2,3,figsize=(11,7), constrained_layout=True)
                for row, label in enumerate(['Baseline','SS']):
                    a,b = matrices[(label,layer,region)]
                    diff = np.abs(a-b)
                    off = ~np.eye(len(a),dtype=bool)
                    metrics.append(dict(sequence=folder.name, frame=frame, layer_input=layer, region=region, model=label,
                                        mse=float(np.mean((a-b)**2)), rgb_offdiag_mean=float(a[off].mean()),
                                        thermal_offdiag_mean=float(b[off].mean()), rgb_offdiag_std=float(a[off].std()),
                                        thermal_offdiag_std=float(b[off].std())))
                    for col,(title,matrix) in enumerate([('RGB',a),('Thermal',b),('Absolute difference',diff)]):
                        m=axes[row,col].imshow(matrix,vmin=0 if col==2 else -1,vmax=2 if col==2 else 1,cmap='magma' if col==2 else 'coolwarm')
                        axes[row,col].set_title(label+' / '+title)
                        fig.colorbar(m,ax=axes[row,col],shrink=.7)
                        arrays['%s_L%d_%s_%s' % (label,layer,region,title.replace(' ','_'))]=matrix
                fig.suptitle('%s frame %d | epoch20 | block INPUT %d | %s\nIdentical GT-centered crop; feature diagnostic, not tracking accuracy' % (folder.name,frame,layer,region))
                fig.savefig(str(folder / ('ss_f%04d_L%d_%s.png' % (frame,layer,region))),dpi=120)
                plt.close(fig)
        np.savez_compressed(str(folder / ('matrices_%04d.npz' % frame)), **arrays)

    for name in selected:
        folder = args.output / name
        folder.mkdir()
        source = args.data / name
        rgb_paths = sorted((source/'visible').glob('*.jpg'))
        ir_paths = sorted((source/'infrared').glob('*.jpg'))
        gt = np.loadtxt(str(source/'visible.txt'),delimiter=',',ndmin=2)
        if not(len(rgb_paths)==len(ir_paths)==len(gt)) or gt.shape[1]!=4 or not np.isfinite(gt).all():
            raise ValueError('Frame alignment/GT invalid: '+name)
        if min(gt[0,2:]) <= 0:
            raise ValueError('Invalid initialization: '+name)
        n=min(args.frames,len(gt))
        frames=set(np.linspace(0,n-1,6,dtype=int).tolist())
        diag_frames=set(np.linspace(1,n-1,2,dtype=int).tolist())
        rows=[]
        predictions={label:[] for label in trackers}
        video=None
        try:
            for i in range(n):
                image=get_x_frame(str(rgb_paths[i]),str(ir_paths[i]),dtype=getattr(cfg.DATA,'XTYPE','rgbrgb'))
                preds={}
                for label,tracker in trackers.items():
                    if i==0:
                        tracker.initialize(image, {'init_bbox':gt[0].tolist()})
                        preds[label]=gt[0].copy()
                    else:
                        preds[label]=np.asarray(tracker.track(image, 'LasHeR', name)['target_bbox'])
                    if not np.isfinite(preds[label]).all() or min(preds[label][2:])<=0:
                        raise ValueError('Invalid prediction')
                    predictions[label].append(preds[label])
                display=panel(cv2.imread(str(rgb_paths[i])),cv2.imread(str(ir_paths[i])),gt[i],preds,name,i+1)
                if video is None:
                    video=cv2.VideoWriter(str(folder/'tracking.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),20,(display.shape[1],display.shape[0]))
                    if not video.isOpened():
                        raise RuntimeError('Cannot open video writer')
                video.write(display)
                if i in frames:
                    cv2.imwrite(str(folder/('frame_%04d.jpg'%(i+1))),display)
                    rows.append(display)
                if i in diag_frames and min(gt[i,2:])>0:
                    diagnostic(image,gt[i],folder,i+1)
                if (i+1)%50==0:
                    print('%s %d/%d'%(name,i+1,n),flush=True)
        finally:
            if video is not None:
                video.release()
        cv2.imwrite(str(folder/'contact_sheet.jpg'),np.vstack(rows))
        for label,values in predictions.items():
            np.savetxt(str(folder/(label+'.txt')),values,fmt='%.6f')
        (folder/'frames.json').write_text(json.dumps(dict(total_sequence_frames=len(gt),processed=n,display_frames=[i+1 for i in sorted(frames)],diagnostic_frames=[i+1 for i in sorted(diag_frames)],gt_sha256=sha(source/'visible.txt')),indent=2))
        (args.output/'diagnostics.json').write_text(json.dumps(metrics,indent=2))
        print('FINISHED '+name,flush=True)
    (args.output/'COMPLETE.txt').write_text('Qualitative subset only; not a full benchmark. Playback 20 FPS is not measured inference speed.\n')
    print('OUTPUT '+str(args.output),flush=True)


if __name__=='__main__':
    main()
