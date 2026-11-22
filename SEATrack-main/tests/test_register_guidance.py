"""CPU regression checks for the independent 11.18 register experiment."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast
import os
import tempfile
import unittest

import torch
from lib.config.seatrack.config import cfg, update_config_from_file
from lib.models.seatrack.vit_ci import VisionTransformerCE
from lib.models.seatrack.seatrack import build_seatrack
from lib.test.parameter.seatrack import parameters

ROOT = Path(__file__).resolve().parents[1]


def make_model(enabled=True, layer=0, scale=0.0, **changes):
    reg = deepcopy(cfg.MODEL.REGISTER)
    reg.update(ENABLED=enabled, INSERT_LAYER=layer, GUIDANCE_SCALE=scale, **changes)
    return VisionTransformerCE(img_size=64, patch_size=16, embed_dim=768, depth=2,
        num_heads=12, search_size=(64, 64), template_size=(32, 32), new_patch_size=16,
        ce_loc=[], ce_keep_ratio=[], register_cfg=reg)


class RegisterTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        torch.set_num_threads(1)
        self.z, self.x = torch.randn(1, 6, 32, 32), torch.randn(1, 6, 64, 64)

    def test_removed_branch_matches_baseline_and_strict_roundtrip(self):
        baseline, reg = make_model(False).eval(), make_model().eval()
        missing, unexpected = reg.load_state_dict(baseline.state_dict(), strict=False)
        self.assertEqual(missing, ['register_tokens'])
        self.assertEqual(unexpected, [])
        with torch.no_grad():
            expected, _ = baseline(self.z, self.x)
            removed, _ = reg.forward_features(self.z, self.x, use_registers=False)
            torch.testing.assert_close(removed, expected, rtol=0, atol=0)
            full, aux = reg(self.z, self.x)
            self.assertEqual(full.shape, (1, 16, 768))
            self.assertFalse(torch.equal(full, removed))
            self.assertTrue(torch.isfinite(full).all())
            self.assertIn('register_norm', aux)
            self.assertNotIn('ss_loss', aux)
            restored = make_model().eval()
            restored.load_state_dict(reg.state_dict(), strict=True)
            torch.testing.assert_close(restored(self.z, self.x)[0], full)

    def test_guidance_equation_and_eval_only(self):
        reg = make_model(layer=1, scale=1.5).eval()
        with torch.no_grad():
            full, _ = reg.forward_features(self.z, self.x)
            removed, _ = reg.forward_features(self.z, self.x, use_registers=False)
            with patch.object(reg, 'forward_features', wraps=reg.forward_features) as spy:
                guided, _ = reg(self.z, self.x)
                self.assertEqual(spy.call_count, 2)
            torch.testing.assert_close(guided, full + 1.5 * (full - removed))
            reg.register_guidance_scale = 0
            with patch.object(reg, 'forward_features', wraps=reg.forward_features) as spy:
                torch.testing.assert_close(reg(self.z, self.x)[0], full)
                self.assertEqual(spy.call_count, 1)
        reg.train()
        reg.register_guidance_scale = 1.5
        with patch.object(reg, 'forward_features', wraps=reg.forward_features) as spy:
            reg(self.z, self.x)
            self.assertEqual(spy.call_count, 1)

    def test_real_optimizer_trains_register_and_excludes_it_from_hmoe(self):
        # Load the real optimizer function without unrelated dataset/LMDB imports.
        tree = ast.parse((ROOT/'lib/train/base_functions.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'get_optimizer_scheduler')
        scope = {'torch': torch, 'is_main_process': lambda: True}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<optimizer>', 'exec'), scope)
        reg = make_model().train()
        optimizer, _ = scope['get_optimizer_scheduler'](reg, deepcopy(cfg))
        self.assertTrue(reg.register_tokens.requires_grad)
        self.assertFalse(reg.patch_embed.proj.weight.requires_grad)
        self.assertTrue(any(p is reg.register_tokens for group in optimizer.param_groups for p in group['params']))
        shapes = []
        handle = reg.blocks[1].attn_moe.register_forward_pre_hook(lambda m, args: shapes.append(args[0].shape[1]))
        before = reg.register_tokens.detach().clone()
        features, _ = reg(self.z, self.x)
        features[..., 0].square().mean().backward()
        handle.remove()
        self.assertEqual(shapes, [8, 32])  # two modalities, no register slots
        self.assertTrue(torch.isfinite(reg.register_tokens.grad).all())
        self.assertGreater(reg.register_tokens.grad.abs().sum().item(), 0)
        optimizer.step()
        self.assertFalse(torch.equal(before, reg.register_tokens))

    def test_default_twelve_layer_factory_and_center_head(self):
        config = deepcopy(cfg)
        update_config_from_file(ROOT/'experiments/seatrack/rgbt_register_guidance.yaml', config)
        model = build_seatrack(config, training=False).eval()
        with torch.no_grad():
            out = model(torch.randn(1, 6, 128, 128), torch.randn(1, 6, 256, 256))
        self.assertEqual(out['backbone_feat'].shape, (1, 256, 768))
        self.assertEqual(out['score_map'].shape, (1, 1, 16, 16))
        self.assertEqual(out['pred_boxes'].shape, (1, 1, 4))
        self.assertTrue(torch.isfinite(out['pred_boxes']).all())
        self.assertEqual(model.backbone.register_tokens.numel(), 3072)

    def test_configs_checkpoint_routing_and_guards(self):
        for name in ['rgbt_register', 'rgbt_register_guidance']:
            config = deepcopy(cfg)
            update_config_from_file(ROOT/f'experiments/seatrack/{name}.yaml', config)
            self.assertFalse(config.MODEL.SS.ENABLED)
            self.assertFalse(config.MODEL.FREQUENCY.ENABLED)
            self.assertEqual(config.TRAIN.SS_WEIGHT, 0)
            with tempfile.NamedTemporaryFile() as f, patch(
                    'lib.test.parameter.seatrack.env_settings',
                    return_value=SimpleNamespace(prj_dir=str(ROOT), save_dir='/unused')):
                with patch.dict(os.environ, {'SEATRACK_CHECKPOINT': f.name}):
                    params = parameters(name)
                    self.assertEqual(params.task, 'rgbt')
                    self.assertEqual(params.checkpoint, f.name)
                with patch.dict(os.environ, {'SEATRACK_CHECKPOINT': ''}):
                    with self.assertRaises(ValueError):
                        parameters(name)
            config.MODEL.SS.ENABLED = True
            with self.assertRaises(ValueError):
                build_seatrack(config, training=False)
        for kw in [{'NUM_TOKENS': 0}, {'layer': 2}, {'scale': -1}, {'scale': float('nan')}]:
            with self.assertRaises(ValueError):
                make_model(**kw)
        reg = make_model().eval()
        with self.assertRaises(ValueError):
            reg(self.z, self.x, ce_keep_rate=.7)
        reg.add_cls_token = True
        with self.assertRaises(ValueError):
            reg(self.z, self.x)


if __name__ == '__main__':
    unittest.main()
