"""Isolated startup with effective batch 32, strict failures and smoke evidence."""
import json
import os
from pathlib import Path
import sys

def main():
    root = Path(__file__).resolve().parent
    sys.path[:0] = [str(root/'code'), str(root/'code/lib/train')]
    os.chdir(root/'code')
    import torch
    from lib.models.layers.attn import MergedLinear
    import lib.train.train_script as ts
    from lib.train.trainers.base_trainer import BaseTrainer

    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(0.28)
    smoke = '--smoke' in sys.argv
    old_settings = ts.update_settings
    def settings(state, cfg):
        old_settings(state, cfg)
        state.accumulation_steps = 8
        state.env.tensorboard_dir = str(root/('smoke_tensorboard' if smoke else 'tensorboard'))
    ts.update_settings = settings
    old_loaders = ts.build_dataloaders
    def loaders(cfg, state):
        result = old_loaders(cfg, state)
        for loader in result:
            if not loader.training:
                loader.num_workers = 0
                loader.timeout = 0
                loader.prefetch_factor = None
        return result
    ts.build_dataloaders = loaders
    old_load = BaseTrainer.load_checkpoint
    def load(self, *args, **kwargs):
        result = old_load(self, *args, **kwargs)
        if result:
            # This run saves only after validation (every fifth epoch), with LoRA merged.
            for module in self.actor.net.modules():
                if isinstance(module, MergedLinear):
                    module.merged = True
            self.actor.net.train()
        return result
    BaseTrainer.load_checkpoint = load
    old_train = BaseTrainer.train
    def train(self, *args, **kwargs):
        cfg = self.actor.cfg
        assert cfg.MODEL.REGISTER.ENABLED and not cfg.MODEL.SS.ENABLED and not cfg.MODEL.FREQUENCY.ENABLED
        p = self.actor.net.backbone.register_tokens
        assert p.requires_grad and any(p is q for g in self.optimizer.param_groups for q in g['params'])
        before = p.detach().clone()
        kwargs['fail_safe'] = False
        result = old_train(self, *args, **kwargs)
        if smoke:
            assert torch.isfinite(p).all() and not torch.equal(p, before)
            report = dict(register_max_update=(p-before).abs().max().item(),
                          peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2,
                          peak_reserved_mib=torch.cuda.max_memory_reserved()/1024**2,
                          epoch=self.epoch)
            (root/'smoke_result.json').write_text(json.dumps(report, indent=2))
            print('REGISTER_SMOKE_COMPLETE', report, flush=True)
        return result
    BaseTrainer.train = train
    from lib.train.run_training import run_training
    run_training('seatrack', 'rgbt_register_smoke' if smoke else 'rgbt_register',
        cudnn_benchmark=False, local_rank=-1, save_dir=str(root/('smoke' if smoke else 'full')),
        base_seed=0, use_lmdb=False, use_wandb=False)
    print('REGISTER_SMOKE_EXIT' if smoke else 'REGISTER_TRAIN_COMPLETE', flush=True)


if __name__ == "__main__":
    main()
