# 2026-11-23 寄存器服务器训练

目标：在无 SS、无频域的独立快照上训练 11.18 寄存器模型。代码来自 `experiment/register-guidance-1118` 的 `d0f2a45`。

服务器目录：`/nas/liziyan103/seatrack/training_runs/20261123_register`。
Python：`/nas/liziyan103/anaconda3/envs/seatrack/bin/python`。
启动：`tmux new-session -d -s register_20261123 'bash /nas/liziyan103/seatrack/training_runs/20261123_register/run.sh'`。
**仅当该会话和实验训练进程均不存在时才能启动，禁止重复启动。**

- `prepare.py`：只能在全新实验目录执行。接收 Git 快照于 `code/`，继承半权重实验中已验证的数据帧索引与梯度累积实现，并记录继承来源、部署文件和初始化权重 SHA256。数据与权重不复制。
- `train.py`：microbatch=4、累积8次，有效 batch=32；训练／验证各60000样本/轮，训练1875次更新/轮，60轮，seed=0。训练 workers=2、验证 workers=0 且 timeout=0、CPU线程2。验证和保存权重均每5轮；异常直接退出。恢复时按验证后保存的 LoRA 合并状态恢复。
- `run.sh`：GPU 4，至少8GB空闲显存才启动；PyTorch 进程显存分配上限设为该卡总量的28%。先执行独立 smoke（64训练样本、16验证样本、2次优化器更新），确认寄存器更新与完成标志后，再进入 full。两者输出隔离；正式训练不加载 smoke 权重。
- 初始化沿用 `rgbt.yaml` 的 OSTrack checkpoint，绝不加载 SS checkpoint。配置只启用寄存器，训练指导系数0。`rgbt_register_guidance` 留作相同权重的后续推理配置。
- 这次只启动训练；全量跟踪评测未自动接入。RG系数需要验证集选择，不能把训练完成视作精度验证完成。

主要文件：`manifest.json`、`status`、`launcher.log`、`smoke.log`、`smoke_result.json`、`train.log`，正式权重位于 `full/checkpoints/rgbt_register/`。

查询（只读）：

```bash
/Users/lzy/.local/bin/nwpu-ssh -o BatchMode=yes 'cat /nas/liziyan103/seatrack/training_runs/20261123_register/status; tail -n 5 /nas/liziyan103/seatrack/training_runs/20261123_register/train.log; tmux list-windows -t register_20261123'
```

`TRAINING` 仅表示已进入启动流程；必须结合实时日志推进和进程判断是否正在训练。`TRAIN_COMPLETE` 也需核对 ep60 checkpoint。

启动预检查曾依次发现并修复参数顺序、多进程入口路径／主函数保护、单进程验证 timeout 三处启动适配问题；失败日志和对应输出均保留为服务器 `*.attempt1/2/3*`，不是正式训练结果。
