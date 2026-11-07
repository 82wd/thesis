"""Training-only cross-modal alignment of full spatial self-similarity."""
import math

import torch
from torch import nn
from torch.nn import functional as F


class SpatialSelfSimilarityAlignment(nn.Module):
    """Align within-modality cosine matrices, separately for template/search.

    Inputs are [B, template_tokens + search_tokens, C]. Every regional patch
    is paired with every patch in that region, including itself. MSE averages
    over batch and both spatial axes. No anchors or trainable parameters.
    """

    def __init__(self, dim, template_weight=0.5, search_weight=0.5):
        super().__init__()
        if (not all(math.isfinite(w) and w >= 0 for w in (template_weight, search_weight))
                or template_weight + search_weight <= 0):
            raise ValueError("SS region weights must be finite, nonnegative and not both zero")
        self.dim = dim
        self.template_weight = template_weight
        self.search_weight = search_weight

    def similarity(self, tokens):
        # Casting alone is insufficient: AMP would cast matmul back to FP16.
        with torch.autocast(device_type=tokens.device.type, enabled=False):
            normalized = F.normalize(tokens.float(), dim=-1, eps=1e-6)
            return normalized @ normalized.transpose(-2, -1)

    def forward(self, rgb, auxiliary, template_length):
        if rgb.ndim != 3 or rgb.shape != auxiliary.shape or rgb.shape[-1] != self.dim:
            raise ValueError("SS expects two matching [B,N,C] tensors")
        if not 0 < template_length < rgb.shape[1]:
            raise ValueError("SS needs nonempty template and search regions")
        with torch.autocast(device_type=rgb.device.type, enabled=False):
            loss_z = F.mse_loss(self.similarity(rgb[:, :template_length]),
                               self.similarity(auxiliary[:, :template_length]))
            loss_s = F.mse_loss(self.similarity(rgb[:, template_length:]),
                               self.similarity(auxiliary[:, template_length:]))
        return {"ss_loss": self.template_weight * loss_z + self.search_weight * loss_s,
                "ss_template": loss_z, "ss_search": loss_s}
