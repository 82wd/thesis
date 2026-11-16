"""Parameter-free radial frequency fusion of spatial search tokens."""
import math

import torch
from torch import nn


class FrequencyFusion(nn.Module):
    """Mix complex spectra per channel; weights denote RGB contribution.

    gain=2 with weights=(.5,.5) corresponds to the original RGB + X sum.
    No parameters or persistent buffers: baseline checkpoints remain compatible.
    """

    def __init__(self, cutoff=0.25, low_rgb_weight=1., high_rgb_weight=0., gain=2.):
        super().__init__()
        if not math.isfinite(cutoff) or not 0 < cutoff <= math.sqrt(.5):
            raise ValueError('Frequency cutoff must be in (0, sqrt(0.5)] cycles/token')
        if not all(math.isfinite(w) and 0 <= w <= 1 for w in (low_rgb_weight, high_rgb_weight)):
            raise ValueError('Frequency RGB weights must be in [0, 1]')
        if not math.isfinite(gain) or gain <= 0:
            raise ValueError('Frequency gain must be positive and finite')
        self.cutoff = cutoff
        self.low_rgb_weight = low_rgb_weight
        self.high_rgb_weight = high_rgb_weight
        self.gain = gain

    def forward(self, rgb, auxiliary, grid_size):
        h, w = grid_size
        if (rgb.ndim != 3 or rgb.shape != auxiliary.shape or
                h <= 0 or w <= 0 or rgb.shape[1] != h * w):
            raise ValueError('Frequency fusion expects matching [B,H*W,C] tokens')
        if rgb.device != auxiliary.device or rgb.dtype != auxiliary.dtype:
            raise ValueError('Frequency inputs must share dtype and device')
        if not rgb.is_floating_point():
            raise ValueError('Frequency inputs must be floating point')
        # Preserve exact baseline arithmetic for the equal-weight sum control.
        if self.low_rgb_weight == self.high_rgb_weight == .5 and self.gain == 2:
            return rgb + auxiliary
        b, _, c = rgb.shape
        # FFT in FP32 also supports non-power-of-two grids under AMP.
        with torch.autocast(device_type=rgb.device.type, enabled=False):
            a = rgb.float().transpose(1, 2).reshape(b, c, h, w)
            x = auxiliary.float().transpose(1, 2).reshape(b, c, h, w)
            fy = torch.fft.fftfreq(h, device=rgb.device)[:, None]
            fx = torch.fft.rfftfreq(w, device=rgb.device)[None, :]
            low = fy.square() + fx.square() <= self.cutoff ** 2
            alpha = torch.where(low, self.low_rgb_weight, self.high_rgb_weight)
            spectrum = alpha * torch.fft.rfft2(a) + (1 - alpha) * torch.fft.rfft2(x)
            fused = self.gain * torch.fft.irfft2(spectrum, s=(h, w))
        return fused.flatten(2).transpose(1, 2).to(rgb.dtype)
