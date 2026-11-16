# 频段融合实验：SEATrack，不使用 SS

本实现对应《师兄想法.md》的第二个方向：先验证非学习、即插即用的特征频段融合。它与 SS 消融独立。新配置明确关闭 `MODEL.SS.ENABLED`，并设 `TRAIN.SS_WEIGHT=0`；已有 SS 实现与配置保留，方便追溯和以后组合。

## 融合位置与计算

在 `lib/models/seatrack/vit_ci.py` 中，取两路最后一层归一化、恢复空间顺序后的 **search tokens**，替换原先的 `x_rgb + x_dte`。模板不直接参与此融合。这里的两条分支已经经过 backbone 跨模态交互，不代表完全独立的原始模态特征。

`lib/models/layers/frequency_fusion.py` 将 `[B,H*W,C]` 还原为 `[B,C,H,W]`，逐通道计算二维实数 FFT。低频为径向频率 `sqrt(fx² + fy²) <= cutoff`，高频为补集；频率单位是每 token 网格的周期数，默认截止值 0.25。保留完整复数系数（幅值和相位），不只混合幅值。

```text
A = FFT2(F_rgb), B = FFT2(F_ir)
w = low_rgb_weight（低频）或 high_rgb_weight（高频）
F_fused = gain × IFFT2(w × A + (1-w) × B)
```

输出形状、预测头、Hann 窗和框解码保持不变。FFT 在 FP32 中计算，结果转回输入 dtype；空间尺寸由搜索图和 patch stride 推导，不写死 16×16。只允许直接 token 布局、无 CLS、CE 保留率为 1，避免对缺失空间位置作频谱解释。

本模块没有可学习参数，也不增加 checkpoint 的 state_dict 键；梯度仍可经 FFT 回传至已有可训练参数。**本次没有实现学习频段权重或决策图融合。**

## 四组配置

位于 `experiments/seatrack/`，均复制原 `rgbt.yaml` 的训练设置，并关闭 SS：

| 配置名 | 融合 | RGB 低/高频权重 | gain |
|---|---|---|---|
| `rgbt_freq_baseline` | 关闭频段模块，原始相加 | 不使用 | 不使用 |
| `rgbt_freq_equal` | 等权对照 | 0.5 / 0.5 | 2 |
| `rgbt_freq_rgb_low` | RGB 低频＋红外高频 | 1 / 0 | 2 |
| `rgbt_freq_ir_low` | 红外低频＋RGB 高频 | 0 / 1 | 2 |

等权、gain=2 时专门直接返回两路相加，使原版对照逐元素一致。一般频域路径存在浮点舍入误差。

默认 gain=2 是为了与原先“相加”而非“平均”的系数约定一致；**不保证硬频段选择后的 RMS 与原相加相同**。因此结果同时涉及频段选择与幅值变化。可另复制配置设 gain=1 做幅值敏感性实验，但不能只报告有利设置，或用测试集选择 cutoff/gain。硬截止还可能造成振铃，这是实验假设的一部分。

## 先用同一份无 SS 基线权重评测

关闭 SS 不能撤销 checkpoint 中已经学习到的 SS 影响。四组都应加载同一份确认未加 SS 的 RGB-T 权重，并记录 SHA-256、epoch、配置和数据名单；本代码只能检查权重路径存在，不能自动判定它是否经过 SS 训练。

`lib/test/parameter/seatrack.py` 已支持以上四个名称：从环境变量 `SEATRACK_CHECKPOINT` 显式读取权重，缺失时直接报错；任务保持 `rgbt`，沿用 RGB-T 的 LoRA 加载约定。每次读取使用独立配置副本，避免同一进程中评测不同配置时互相污染。

先配置 `lib/test/evaluation/local.py` 的项目路径，并检查 `RGBT_workspace/test_rgbt_mgpus.py` 的数据集路径。从 `SEATrack-main` 运行，例如：

```bash
export SEATRACK_CHECKPOINT=/absolute/path/to/non_ss/SEATrack_ep0060.pth.tar
CUDA_VISIBLE_DEVICES=0 python RGBT_workspace/test_rgbt_mgpus.py \
  --script_name seatrack --yaml_name rgbt_freq_baseline \
  --dataset_name LasHeR --mode sequential --num_gpus 1 \
  --variants freq_baseline
```

随后分别替换 `--yaml_name` 和 `--variants` 为其他三组名称。每组使用新的独立 variants 目录：原评测器会跳过已有同名轨迹，复用目录可能混入旧结果。此命令生成轨迹，最终指标需用同一评测脚本计分。先确认 baseline/equal 完整轨迹一致，再解释两个频段选择组的结果。

不要直接使用默认 `train.sh`：它仍是上游多任务入口。本次未部署服务器、未启动训练和全量评测。

## 如果后续需要训练

建议先完成上述固定权重试验。重新训练是另一个问题，应为原版和频段组设置一致初始化、seed、有效 batch size、采样量与更新次数，不可直接与训练预算不同的历史 SS 实验比较。

```bash
CUDA_VISIBLE_DEVICES=0 LOCAL_RANK=-1 python lib/train/run_training.py \
  --script seatrack --config rgbt_freq_rgb_low \
  --save_dir ./output/freq_rgb_low_seed0 --seed 0
```

运行前配置训练数据路径和 OSTrack 初始化文件；使用全新的输出目录，训练器会自动恢复该目录已有 checkpoint。无参数的频段模块本身不会被优化器学习，只有现有训练配置允许的参数被训练。代码保留支持 SS 的能力，但本次四组配置不启用它。

## 测试

```bash
python -m unittest discover -s tests -v
```

新增 `tests/test_frequency_fusion.py` 检查：等权与原始相加精确一致、常数/棋盘信号的频段选择、奇数非方形网格与完整复数 FFT 参考结果一致、梯度有限且非零、AMP dtype、参数校验、骨干 checkpoint 严格加载、关闭 SS 及评测配置隔离。

测试结果不代表跟踪精度提升；完整 benchmark 结果需另记入实验日志。

### 本次验证结果

2026-11-16，在本地隔离环境 Python 3.9 / PyTorch 2.8.0、CPU 上运行全部测试：**15 项通过**（6 项频段融合测试、9 项原有 SS 测试）。骨干兼容检查使用测试构建的同结构 state_dict，未在本地加载服务器真实基线文件。语法、Git 差异空白及 README 链接检查通过。尚未做 CUDA 试跑、真实轨迹一致性检查或完整 benchmark 评测。
