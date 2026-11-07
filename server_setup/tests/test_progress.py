import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / 'pairwise_ss_20261103/progress.py'
spec = importlib.util.spec_from_file_location('progress', SCRIPT)
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)

TRAIN = '[train: 2, 160 / 14992] FPS: 18.0 (20.0) , TotalTime: 0.222 , Loss/total: 1.20000 , IoU: 0.70000 , Loss/ss: 0.02000 , Loss/ss_template: 0.01000 , Loss/ss_search: 0.03000 , Loss/ss_weighted: 0.00200\n'
VAL = '[val: 2, 4 / 4] FPS: 20.0 (21.0) , TotalTime: 0.200 , Loss/total: 1.10000 , IoU: 0.71000 , Loss/ss: 0.01800 , Loss/ss_weighted: 0.00180\n'


class DashboardTests(unittest.TestCase):
    def test_iou_does_not_match_giou_suffix(self):
        self.assertAlmostEqual(progress.metric('Loss/giou: 0.27473 , IoU: 0.74968', 'IoU'), .74968)
        self.assertIsNone(progress.metric('Loss/giou: 0.27473', 'IoU'))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / 'full_test'
        self.run.mkdir()
        (self.run / 'train.log').write_text(TRAIN)

    def test_parse_metrics_and_validation_phase(self):
        data = progress.parse(TRAIN + VAL)
        self.assertEqual(data['last']['phase'], 'val')
        self.assertEqual(data['train']['epoch'], 2)
        self.assertAlmostEqual(data['train']['metrics']['Loss/ss'], .02)
        self.assertAlmostEqual(data['train']['metrics']['Loss/ss_weighted'], .002)
        self.assertFalse(data['error_after_progress'])
        view = progress.screen(self.run, 60, 'rgbt_ss', '1', now=(self.run/'train.log').stat().st_mtime)
        self.assertIn('第 2/60 轮', view)
        self.assertIn('10/937 次', view)
        self.assertIn('1.68%', view)

    def test_progress_100_is_not_completion(self):
        (self.run/'train.log').write_text(TRAIN.replace('2, 160', '60, 14992'))
        view = progress.screen(self.run, 60, 'rgbt_ss', '1')
        self.assertIn('100.00%', view)
        self.assertNotIn('已完成（', view)
        (self.run/'exitcode.txt').write_text('0\n')
        (self.run/'train.log').write_text(TRAIN + 'Finished training!\n')
        self.assertNotIn('已完成（', progress.screen(self.run, 60, 'rgbt_ss', '1'))
        checkpoint = self.run/'checkpoints/rgbt_ss/SEATrack_ep0060.pth.tar'
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_bytes(b'nonempty test placeholder, not loaded')
        self.assertIn('已完成（', progress.screen(self.run, 60, 'rgbt_ss', '1'))

    def test_failures_and_nonfinite_values(self):
        (self.run/'train.log').write_text(TRAIN + 'Training crashed at epoch 2\nTraceback (most recent call last):\nRuntimeError: example\n')
        self.assertIn('日志出现错误', progress.screen(self.run, 60, 'rgbt_ss', '1'))
        (self.run/'exitcode.txt').write_text('1')
        self.assertIn('失败 / 已退出', progress.screen(self.run, 60, 'rgbt_ss', '1'))
        (self.run/'exitcode.txt').unlink()
        (self.run/'train.log').write_text(TRAIN.replace('Loss/ss: 0.02000', 'Loss/ss: nan'))
        self.assertIn('非有限指标', progress.screen(self.run, 60, 'rgbt_ss', '1'))

    def test_read_only_and_stale_logs(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.run.rglob('*') if p.is_file()}
        view = progress.screen(self.run, 60, 'rgbt_ss', '1', now=(self.run/'train.log').stat().st_mtime+7200)
        self.assertIn('时间估算：暂无', view)
        after = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.run.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_auto_selection_excludes_smoke_and_rejects_ambiguity(self):
        (self.root/'smoke_fake').mkdir()
        self.assertEqual(progress.select_run(self.root, None), self.run)
        (self.root/'full_second').mkdir()
        with self.assertRaisesRegex(ValueError, '多个正式实验'):
            progress.select_run(self.root, None)
        self.assertEqual(progress.select_run(self.root, self.run), self.run.resolve())
        self.assertIsNone(progress.select_run(self.root/'absent', None))

    def test_config_epoch_and_gpu_timeout(self):
        cfg = self.root/'code/experiments/seatrack/rgbt_ss.yaml'
        cfg.parent.mkdir(parents=True)
        cfg.write_text('MODEL:\n  X: 2\nTRAIN:\n  EPOCH: 12\n  NUM_WORKER: 10\nTEST:\n  EPOCH: 60\n')
        self.assertEqual(progress.training_epochs(self.root, 'rgbt_ss'), 12)
        with patch.object(progress.subprocess, 'run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 3)):
            self.assertIn('查询不可用', progress.gpu_status(1))

    def test_initialization_and_empty_exitcode(self):
        (self.run/'train.log').write_text('No matching checkpoint file found\n')
        (self.run/'exitcode.txt').write_text('')
        view = progress.screen(self.run, 60, 'rgbt_ss', '1')
        self.assertIn('等待首条训练记录', view)
        self.assertNotIn('失败 / 已退出', view)


if __name__ == '__main__':
    unittest.main()
