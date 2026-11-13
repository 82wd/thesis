import runpy
import sys
import decision
from decision import torch

class FeatureTracker(decision.SEATrack):
    def __init__(self,p,mode,weights):
        super().__init__(p)
        branches=[]
        self.network.backbone.norm.register_forward_hook(lambda m,a,y: branches.append(y[:,-256:]))
        def fuse(m,a,out):
            rgb,ir=branches
            branches.clear()
            assert torch.equal(rgb+ir,out[0])
            n,c=rgb.shape[-2:]
            def spectrum(x):
                return torch.fft.rfft2(x.transpose(1,2).reshape(1,c,16,16))
            x,y=spectrum(rgb),spectrum(ir)
            low=torch.fft.fftfreq(16,device=x.device)[:,None]**2+torch.fft.rfftfreq(16,device=x.device)[None,:]**2<=.25**2
            selected=torch.where(low,x,y) if mode=='feature_rgb_low' else torch.where(low,y,x)
            return torch.fft.irfft2(selected,s=(16,16)).flatten(2).transpose(1,2),out[1]
        self.network.backbone.register_forward_hook(fuse)
