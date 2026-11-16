"""CPU checks for parameter-free spectral fusion and backbone compatibility."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
import os
import tempfile

import torch
from lib.config.seatrack.config import cfg, update_config_from_file
from lib.models.layers.frequency_fusion import FrequencyFusion
from lib.models.seatrack.vit_ci import VisionTransformerCE
from lib.test.parameter.seatrack import parameters
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class FrequencyTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        torch.set_num_threads(1)

    def test_equal_is_exact_sum(self):
        a, b = torch.randn(2, 35, 8), torch.randn(2, 35, 8)
        m = FrequencyFusion(low_rgb_weight=.5, high_rgb_weight=.5)
        self.assertEqual(len(m.state_dict()), 0)
        torch.testing.assert_close(m(a, b, (5, 7)), a + b, rtol=0, atol=0)

    def test_dc_and_checkerboard_band_selection(self):
        dc = torch.ones(1, 64, 1) * 3
        y, x = torch.meshgrid(torch.arange(8), torch.arange(8), indexing='ij')
        high = ((-1.) ** (x + y)).reshape(1, 64, 1)
        # RGB DC survives low band, auxiliary checkerboard survives high band.
        torch.testing.assert_close(FrequencyFusion()(dc, high, (8, 8)), 2 * (dc + high))
        torch.testing.assert_close(FrequencyFusion(low_rgb_weight=0., high_rgb_weight=1.)(
            dc, high, (8, 8)), torch.zeros_like(dc))

    def test_odd_grid_matches_full_complex_fft_and_gradients(self):
        a = torch.randn(2, 35, 3, requires_grad=True)
        b = torch.randn(2, 35, 3, requires_grad=True)
        m = FrequencyFusion(.3, .8, .2, 1.)
        out = m(a, b, (5, 7))
        fy = torch.fft.fftfreq(5)[:, None]
        fx = torch.fft.fftfreq(7)[None, :]
        w = torch.where(fy ** 2 + fx ** 2 <= .3 ** 2, .8, .2)
        aa, bb = [t.transpose(1, 2).reshape(2, 3, 5, 7) for t in (a, b)]
        reference = torch.fft.ifft2(w * torch.fft.fft2(aa) + (1-w)*torch.fft.fft2(bb)).real
        torch.testing.assert_close(out, reference.flatten(2).transpose(1, 2))
        out.square().mean().backward()
        for t in (a, b):
            self.assertTrue(torch.isfinite(t.grad).all())
            self.assertGreater(t.grad.abs().sum().item(), 0)
        with torch.autocast('cpu', dtype=torch.bfloat16):
            mixed = m(a.detach().bfloat16(), b.detach().bfloat16(), (5, 7))
        self.assertEqual(mixed.dtype, torch.bfloat16)
        self.assertTrue(torch.isfinite(mixed).all())

    def test_guards(self):
        for kwargs in [{'cutoff': 0}, {'cutoff': float('nan')}, {'gain': 0},
                       {'low_rgb_weight': -1}, {'high_rgb_weight': 2}]:
            with self.assertRaises(ValueError):
                FrequencyFusion(**kwargs)
        with self.assertRaises(ValueError):
            FrequencyFusion()(torch.zeros(1, 8, 2), torch.zeros(1, 8, 2), (3, 3))

    def test_config_and_backbone_checkpoint_parity(self):
        def net(fc):
            return VisionTransformerCE(img_size=64, patch_size=16, embed_dim=768, depth=2,
                num_heads=12, search_size=(64, 64), template_size=(32, 32),
                new_patch_size=16, ce_loc=[], ce_keep_ratio=[], amglora_rank=8, hmoe_rank=4,
                ss_cfg=config.MODEL.SS, frequency_cfg=fc).eval()
        for name in ['baseline', 'equal', 'rgb_low', 'ir_low']:
            config = deepcopy(cfg)
            update_config_from_file(ROOT/f'experiments/seatrack/rgbt_freq_{name}.yaml', config)
            self.assertFalse(config.MODEL.SS.ENABLED)
            self.assertEqual(config.TRAIN.SS_WEIGHT, 0)
        config.MODEL.FREQUENCY.ENABLED = False
        original = net(config.MODEL.FREQUENCY)
        fc = deepcopy(config.MODEL.FREQUENCY)
        fc.ENABLED = True
        fc.LOW_RGB_WEIGHT = fc.HIGH_RGB_WEIGHT = .5
        equal = net(fc)
        equal.load_state_dict(original.state_dict(), strict=True)
        z, x = torch.randn(1, 6, 32, 32), torch.randn(1, 6, 64, 64)
        with torch.no_grad():
            expected, _ = original(z, x)
            result, aux = equal(z, x)
            torch.testing.assert_close(result, expected, rtol=0, atol=0)
            self.assertNotIn('ss_loss', aux)
            equal.frequency_fusion.low_rgb_weight = 1.
            equal.frequency_fusion.high_rgb_weight = 0.
            fused, aux = equal(z, x)
            self.assertEqual(fused.shape, expected.shape)
            self.assertTrue(torch.isfinite(fused).all())
            self.assertFalse(torch.equal(fused, expected))

    def test_eval_checkpoint_is_explicit_and_config_is_isolated(self):
        with tempfile.NamedTemporaryFile() as f, patch(
                'lib.test.parameter.seatrack.env_settings',
                return_value=SimpleNamespace(prj_dir=str(ROOT), save_dir='/unused')):
            with patch.dict(os.environ, {'SEATRACK_CHECKPOINT': f.name}):
                p = parameters('rgbt_freq_rgb_low')
                self.assertEqual(p.task, 'rgbt')
                self.assertEqual(p.checkpoint, f.name)
                self.assertFalse(p.cfg.MODEL.SS.ENABLED)
                baseline = parameters('rgbt')
                self.assertFalse(baseline.cfg.MODEL.FREQUENCY.ENABLED)
                self.assertTrue(p.cfg.MODEL.FREQUENCY.ENABLED)
            with patch.dict(os.environ, {'SEATRACK_CHECKPOINT': ''}):
                with self.assertRaises(ValueError):
                    parameters('rgbt_freq_ir_low')


if __name__ == '__main__':
    unittest.main()
