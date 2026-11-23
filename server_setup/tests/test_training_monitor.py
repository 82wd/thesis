import importlib.util
from pathlib import Path
import tempfile
import unittest
import os

spec = importlib.util.spec_from_file_location('monitor', Path(__file__).parents[1] / 'training_monitor.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

ROW = '[train: 1, 50 / 1875] FPS: 58.3 , TotalTime: 0.55 , Loss/total: 1.5 , Loss/giou: 0.37 , IoU: 0.67 , Loss/ss: 0.01\n'


class MonitorTests(unittest.TestCase):
    def test_metric_boundary(self):
        self.assertEqual(monitor.parse(ROW)['train']['metrics']['IoU'], 0.67)

    def test_stale_suppresses_eta_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            log = run / 'train.log'
            log.write_text(ROW)
            os.utime(log, (1000, 1000))
            before = log.read_bytes(), log.stat().st_mtime
            output = monitor.screen(run, 60, 'rgbt_ss_search', 'test', now=1401)
            self.assertIn('疑似停滞', output)
            self.assertIn('时间估算：暂无', output)
            self.assertEqual(before, (log.read_bytes(), log.stat().st_mtime))

    def test_completion_requires_exit_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / 'train.log').write_text(ROW + 'Finished training!\n')
            (run / 'status').write_text('FINISHED exit=0, final_checkpoint=True')
            self.assertNotIn('已完成（', monitor.screen(run, 60, 'cfg', 'test'))
            checkpoints = run / 'output/checkpoints/cfg'
            checkpoints.mkdir(parents=True)
            (checkpoints / 'SEATrack_ep0060.pth.tar').write_bytes(b'placeholder')
            self.assertIn('已完成（', monitor.screen(run, 60, 'cfg', 'test'))

    def test_register_run_layout_and_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            row = ROW.rstrip() + ' , Register/register_norm: 150.1 , Register/patch_norm: 270.2\n'
            (run / 'train.log').write_text(row + 'Finished training!\nREGISTER_TRAIN_COMPLETE\n')
            (run / 'status').write_text('TRAIN_COMPLETE\n')
            self.assertNotIn('已完成（', monitor.screen(run, 60, 'rgbt_register', 'test'))
            checkpoints = run / 'full/checkpoints/rgbt_register'
            checkpoints.mkdir(parents=True)
            (checkpoints / 'SEATrack_ep0060.pth.tar').write_bytes(b'placeholder')
            output = monitor.screen(run, 60, 'rgbt_register', 'test')
            self.assertIn('已完成（', output)
            self.assertIn('寄存器范数 150.10000', output)
            self.assertIn('patch 范数 270.20000', output)

    def test_register_failure_status_suppresses_eta(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / 'train.log').write_text(ROW)
            (run / 'status').write_text('FAILED exit=1\n')
            output = monitor.screen(run, 60, 'rgbt_register', 'test')
            self.assertIn('失败 / 已退出', output)
            self.assertIn('时间估算：暂无', output)

    def test_crash_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / 'train.log').write_text(ROW + 'Training crashed at epoch 2\nFinished training!\n')
            output = monitor.screen(run, 60, 'cfg', 'test')
            self.assertIn('日志出现错误', output)
            self.assertIn('时间估算：暂无', output)


if __name__ == '__main__':
    unittest.main()
