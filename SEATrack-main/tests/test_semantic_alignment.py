"""CPU smoke tests: python -m unittest discover -s tests -v."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from tempfile import TemporaryDirectory

import torch
from torch.nn import functional as F
from lib.config.seatrack.config import cfg, update_config_from_file
from lib.models.layers.semantic_alignment import SpatialSelfSimilarityAlignment
from lib.models.seatrack.vit_ci import VisionTransformerCE
from lib.train.actors.seatrack import SEATrackActor

ROOT = Path(__file__).resolve().parents[1]


def optimizer_for(net, config):
    # Run the actual optimizer function without importing unrelated dataset loaders.
    tree = ast.parse((ROOT / 'lib/train/base_functions.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == 'get_optimizer_scheduler')
    namespace = {'torch': torch, 'is_main_process': lambda: True}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<optimizer>', 'exec'), namespace)
    return namespace['get_optimizer_scheduler'](net, config)[0]


def backbone(config):
    return VisionTransformerCE(img_size=64, patch_size=16, embed_dim=768, depth=4,
                               num_heads=12, search_size=(64, 64), template_size=(32, 32),
                               new_patch_size=16, ce_loc=[], ce_keep_ratio=[],
                               amglora_rank=8, hmoe_rank=4, ss_cfg=config)


class SemanticAlignmentTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        torch.set_num_threads(1)

    def test_pairwise_formula_and_gradients(self):
        module = SpatialSelfSimilarityAlignment(16, template_weight=.3, search_weight=.7)
        self.assertEqual(sum(p.numel() for p in module.parameters()), 0)
        rgb = torch.randn(2, 20, 16, requires_grad=True)
        auxiliary = torch.randn(2, 20, 16, requires_grad=True)
        self.assertEqual(module(rgb, rgb, 4)['ss_loss'].item(), 0)
        result = module(rgb, auxiliary, 4)

        # Independent reference: explicitly enumerate all pairs with cosine.
        def reference(a, b):
            terms = [(F.cosine_similarity(a[:, i], a[:, j], dim=-1)
                      - F.cosine_similarity(b[:, i], b[:, j], dim=-1)).square()
                     for i in range(a.shape[1]) for j in range(a.shape[1])]
            return torch.stack(terms).mean()
        expected_z = reference(rgb[:, :4], auxiliary[:, :4])
        expected_s = reference(rgb[:, 4:], auxiliary[:, 4:])
        torch.testing.assert_close(result['ss_template'], expected_z)
        torch.testing.assert_close(result['ss_search'], expected_s)
        torch.testing.assert_close(result['ss_loss'], .3 * expected_z + .7 * expected_s)
        result['ss_loss'].backward()
        for param in (rgb, auxiliary):
            self.assertIsNotNone(param.grad)
            self.assertTrue(torch.isfinite(param.grad).all())
            self.assertGreater(param.grad.abs().sum().item(), 0)
        zeros = torch.zeros(2, 20, 16, requires_grad=True)
        zero_loss = module(zeros, zeros, 4)['ss_loss']
        self.assertEqual(zero_loss.item(), 0)
        zero_loss.backward()
        self.assertTrue(torch.isfinite(zeros.grad).all())

    def test_hand_calculated_pairs_and_region_isolation(self):
        module = SpatialSelfSimilarityAlignment(2)
        # Template: [[1,0],[0,1]] versus [[1,1],[1,1]], MSE = 1/2.
        # Search is identical in both modalities, MSE = 0.
        rgb = torch.tensor([[[1., 0.], [0., 1.], [1., 0.], [0., 1.]]])
        auxiliary = torch.tensor([[[1., 0.], [1., 0.], [1., 0.], [0., 1.]]])
        result = module(rgb, auxiliary, 2)
        self.assertEqual(result['ss_template'].item(), .5)
        self.assertEqual(result['ss_search'].item(), 0)
        self.assertEqual(result['ss_loss'].item(), .25)

    def test_relations_not_direct_cross_modal_feature_matching(self):
        module = SpatialSelfSimilarityAlignment(8)
        rgb = torch.randn(1, 10, 8)
        # A channel-space rotation changes features but preserves pair relations.
        rotation, _ = torch.linalg.qr(torch.randn(8, 8))
        auxiliary = rgb @ rotation
        self.assertLess(module(rgb, auxiliary, 4)['ss_loss'].item(), 1e-12)
        # Reordering positions in only one modality breaks correspondence.
        auxiliary = auxiliary[:, [1, 0, 2, 3, 4, 5, 6, 7, 8, 9]]
        self.assertGreater(module(rgb, auxiliary, 4)['ss_loss'].item(), 1e-5)

    def test_full_size_matrices_and_autocast(self):
        module = SpatialSelfSimilarityAlignment(768)
        rgb = torch.randn(1, 320, 768, requires_grad=True)
        auxiliary = torch.randn_like(rgb, requires_grad=True)
        expected = module(rgb, auxiliary, 64)['ss_loss']
        with torch.autocast(device_type='cpu', dtype=torch.bfloat16):
            template = module.similarity(rgb[:, :64])
            search = module.similarity(rgb[:, 64:])
            loss = module(rgb, auxiliary, 64)['ss_loss']
        self.assertEqual(template.shape, (1, 64, 64))
        self.assertEqual(search.shape, (1, 256, 256))
        self.assertEqual(search.dtype, torch.float32)
        self.assertEqual(loss.dtype, torch.float32)
        torch.testing.assert_close(loss, expected, rtol=0, atol=0)
        torch.testing.assert_close(search, search.transpose(-2, -1))
        torch.testing.assert_close(search.diagonal(dim1=-2, dim2=-1), torch.ones(1, 256))
        loss.backward()
        self.assertTrue(torch.isfinite(rgb.grad).all())
        self.assertTrue(torch.isfinite(auxiliary.grad).all())

    def test_backbone_peft_and_eval_parity(self):
        config = deepcopy(cfg)
        config.MODEL.SS.ENABLED = True
        config.MODEL.SS.LAYERS = [3]
        net = backbone(config.MODEL.SS)
        optimizer = optimizer_for(net, config)
        self.assertFalse(net.patch_embed.proj.weight.requires_grad)
        self.assertEqual(list(net.ss_alignment.parameters()), [])
        z, x = torch.randn(2, 6, 32, 32), torch.randn(2, 6, 64, 64)
        _, aux = net(z, x)
        aux['ss_loss'].backward()
        upstream = [p.grad for n, p in net.blocks[1].named_parameters() if p.requires_grad]
        self.assertTrue(any(g is not None and g.abs().sum() > 0 for g in upstream))
        optimizer.step()
        net.eval()
        with torch.no_grad():
            baseline_output, aux = net(z, x)
            aligned_output, val_aux = net(z, x, compute_ss=True)
        self.assertNotIn('ss_loss', aux)
        self.assertIn('ss_loss', val_aux)
        torch.testing.assert_close(baseline_output, aligned_output, rtol=0, atol=0)
        self.assertEqual(tuple(baseline_output.shape), (2, 16, 768))
        config.MODEL.SS.ENABLED = False
        original = backbone(config.MODEL.SS).eval()
        original.load_state_dict(net.state_dict(), strict=True)
        with torch.no_grad():
            output, _ = original(z, x)
        torch.testing.assert_close(output, baseline_output, rtol=0, atol=0)

    def test_actor_adds_loss_and_reports_validation(self):
        config = deepcopy(cfg)
        config.MODEL.SS.ENABLED = True
        actor = SEATrackActor(torch.nn.Identity(),
                             {'giou': lambda a, b: (a.sum() * 0 + 2, a.new_ones(a.shape[0])),
                              'l1': F.l1_loss}, {'giou': 2., 'l1': 5., 'focal': 1.},
                             SimpleNamespace(batchsize=2), config)
        ss = torch.tensor(.4, requires_grad=True)
        predictions = {'pred_boxes': torch.tensor([[[.5, .5, .2, .2]]] * 2),
                       'ss_loss': ss, 'ss_template': ss, 'ss_search': ss}
        truth = {'search_anno': torch.tensor([[[.4, .4, .2, .2]] * 2])}
        loss, status = actor.compute_losses(predictions, truth)
        loss.backward()
        self.assertAlmostEqual(ss.grad.item(), config.TRAIN.SS_WEIGHT)
        self.assertAlmostEqual(status['Loss/ss_weighted'], .04, places=6)
        config.MODEL.SS.ENABLED = False
        base_loss = actor.compute_losses(predictions, truth, return_status=False)
        self.assertAlmostEqual((loss - base_loss).item(), .04, places=6)

    def test_legacy_anchor_config_is_rejected(self):
        with TemporaryDirectory() as directory:
            legacy = Path(directory) / 'legacy.yaml'
            legacy.write_text('MODEL:\n  SS:\n    ENABLED: true\n    ANCHOR: mean\n')
            with self.assertRaisesRegex(ValueError, 'ANCHOR'):
                update_config_from_file(legacy, deepcopy(cfg))

    def test_configs_and_guards(self):
        for task in ('rgbt', 'rgbd', 'rgbe'):
            config = deepcopy(cfg)
            update_config_from_file(ROOT / f'experiments/seatrack/{task}_ss.yaml', config)
            self.assertTrue(config.MODEL.SS.ENABLED)
            self.assertEqual(config.TRAIN.SS_WEIGHT, .1)
            self.assertNotIn('ANCHOR', config.MODEL.SS)
        config.MODEL.SS.LAYERS = [0]
        with self.assertRaises(ValueError):
            backbone(config.MODEL.SS)
        with self.assertRaises(ValueError):
            SpatialSelfSimilarityAlignment(16, template_weight=-1)
        with self.assertRaises(ValueError):
            SpatialSelfSimilarityAlignment(16)(torch.zeros(1, 5, 16), torch.zeros(1, 4, 16), 2)
        for length in (0, 5):
            with self.assertRaises(ValueError):
                SpatialSelfSimilarityAlignment(16)(torch.zeros(1, 5, 16), torch.zeros(1, 5, 16), length)
        for weights in ((0, 0), (float('nan'), 1), (1, float('inf'))):
            with self.assertRaises(ValueError):
                SpatialSelfSimilarityAlignment(16, *weights)



if __name__ == '__main__':
    unittest.main()
