# 毕设实验日记

## 2026-11-07（周六）

### RGB-T + SS：核验第 60 轮权重，完成两套测试

确认 SEATrack + SS 已在 LasHeR 上完成 60 轮训练，末轮权重 `full_zCqHZl/checkpoints/rgbt_ss/SEATrack_ep0060.pth.tar` 已保存并成功加载，文件内部轮次为 60。

从第 1 轮到第 60 轮，训练总损失从 1.44155 降至 1.04587，训练平均 IoU 从 69.198% 升至 76.291%，SS 损失从 0.02483 降至 0.01543。第 60 轮验证 IoU 为 74.895%，同期基线为 74.872%，相差 +0.023 个百分点。

用第 60 轮 SS 权重跑完 LasHeR 和 RGBT234，并用相同脚本对 SS 和第 60 轮基线的轨迹重新计分。逐序列核对了名单、帧数和标注指纹。

| 数据集 | 指标 | 基线 | + SS | 差值（百分点） |
|---|---|---:|---:|---:|
| LasHeR（245 序列，220,703 帧） | PR | 71.57% | 70.51% | −1.06 |
| LasHeR | NPR | 67.83% | 67.00% | −0.83 |
| LasHeR | SR | 57.51% | 56.71% | −0.80 |
| RGBT234（234 序列，116,649 帧） | MPR | 86.14% | 87.33% | +1.18 |
| RGBT234 | MSR | 63.73% | 64.67% | +0.94 |

本次对比中，SS 在 LasHeR 测试集上的三项指标均下降，在跨数据集测试 RGBT234 上的两项指标均上升。差值按未舍入分数计算。[四份指标报告及权重清单](汇报/结果/RGBT_SS_ep60/)

### RGB-E + SS：启动 VisEvent 训练

通过 128 个样本的试跑，确认 SS 损失有输出、优化器完成 2 次更新并保存了试跑权重。随后从 OSTrack 预训练权重开始 45 轮正式训练。沿用 RGB-E 基线学习率 0.00006，单卡每批 4 个样本，累积 16 批更新一次，每轮采样 59,968 个样本，共 937 次更新。VisEvent 本次配置只记录训练指标。

北京时间 23:05，训练进行到第 18/45 轮，本轮已完成 13,700/14,992 批，总进度 39.81%。最近已保存第 17 轮权重 `SEATrack_ep0017.pth.tar`。服务器实验目录为 `/nas/liziyan103/seatrack/training_runs/rgbe_pairwise_ss/run_PzOoDM`。

今天还部署了两个只读终端面板：[RGB-T 测试进度](server_setup/pairwise_ss_20261103/eval_progress.py)可查看两套数据集的轨迹和出分状态，[RGB-E 训练进度](server_setup/pairwise_ss_20261103/rgbe_progress.py)可查看轮次、批次、损失、IoU 和最新权重。

## 2026-11-08（周日）

在 GPU 3 启动 DepthTrack 的 RGB-D + SS 训练，实验编号 `run_HuBcot`。128 个训练样本完成 2 次参数更新，16 个验证样本通过，试跑权重成功保存。正式训练从 OSTrack 预训练权重开始，共 25 轮，每 5 轮验证一次。23:20 已保存第 9 轮权重，第 10 轮进行至 9,400/14,992 批。

## 2026-11-09（周一）

RGB-E + SS 完成 45 轮训练。00:53 确认末轮权重 `SEATrack_ep0045.pth.tar` 已保存，末轮训练 IoU 为 81.679%，总损失为 0.79296，SS 损失为 0.02225。使用该权重完成 VisEvent 全部 320 条序列测试。两版使用相同的测试名单、标注和计分协议。

| VisEvent 指标 | 第 45 轮基线 | 第 45 轮 + SS | 差值（百分点） |
|---|---:|---:|---:|
| PR | 77.10% | 76.24% | −0.86 |
| SR | 60.26% | 59.63% | −0.63 |

特殊序列的预测比官方标注多 26 帧，两版均按同一规则截断。单独排除该序列复算，319 条序列的 PR 和 SR 仍分别下降 0.86、0.64 个百分点。历史记录中 RGB-E 自训练基线与官方权重的模型参数相同，基线来源仍待追溯。[基线报告](汇报/结果/VisEvent_SS_ep45/baseline.json) · [SS 报告](汇报/结果/VisEvent_SS_ep45/ss.json)

## 2026-11-10（周二）

核验 RGB-D + SS 已完成第 25 轮，末轮权重 `SEATrack_ep0025.pth.tar` 约 364 MiB。使用这份权重分别启动 DepthTrack（50 条）和 VOT2022-RGBD（127 条）评测。

**LasHeR 跟偏复查。** 按 SR 逐序列配对，122 条提高、122 条下降、1 条持平。退步最大的两条合计拉低整体 SR 约 0.55 个百分点。将连续 5 帧基线 IoU ≥ 0.5 且 SS IoU < 0.2 定为持续跟偏，以第一帧计。`whitesuvturn` 在第 23 帧转向另一辆白车，`1blackteacher` 在第 165 帧转向邻近人脸。两者此后均未连续 5 帧恢复到 IoU ≥ 0.5。RGBT234 的分布有所不同，MSR 在 140 条上提高、91 条上下降、3 条持平。[白车对比视频](汇报/结果/LasHeR_ep60_跟偏分析/whitesuvturn.mp4) · [人群对比视频](汇报/结果/LasHeR_ep60_跟偏分析/1blackteacher.mp4)

**VisEvent 失分集中在少数序列。** SR 净降 0.635 个百分点，其中跌幅最大的 5 条合计贡献 −0.617 个百分点。`personFootball` 中 SS 框转向邻近球员，连续 510 帧 IoU < 0.2。`girl1` 从第 60 帧至结尾连续 122 帧低于该阈值。`machineBrad` 中两版一度同时跟偏，基线在第 152 帧恢复至 IoU 0.80，SS 当帧为 0。[同步可见光与事件关键帧](汇报/结果/VisEvent_SS_ep45/案例/)

## 2026-11-11（周三）

### RGB-D 评测

DepthTrack 的 50 条序列已完成。使用第 25 轮权重按同一协议与历史基线比较。

| DepthTrack 指标 | 基线 | + SS | 差值（百分点） |
|---|---:|---:|---:|
| 精确率 | 62.91% | 60.77% | −2.14 |
| 召回率 | 63.55% | 61.17% | −2.37 |
| F 分数 | 63.23% | 60.97% | −2.26 |

VOT2022 先因跟踪器响应超过 30 秒中断。13:33 核查时已有 80 条序列产生轨迹，续跑至 126 条后再次超时。随后将等待时间调至 240 秒。GPU 6 上的补跑在模型加载时显存不足，21:02 改用物理 GPU 5 继续。**截至北京时间 21:21，127/127 条序列均已创建轨迹目录，评测日志显示 99%，会话 `vot22_gpu5` 仍在运行。最终 EAO、准确率、鲁棒性及基线差值待核验。** 服务器评测目录为 `/nas/liziyan103/seatrack/training_runs/rgbd_pairwise_ss/run_HuBcot/eval_ep25`。三组训练均已完成，五个测试集已有四个正式出分。

### 为什么掉分：交换上一帧的搜索框

固定首帧模板和当前帧，在 LasHeR 和 VisEvent 的 5 条大幅退步序列中，分别给两份模型相同的基线前框、SS 前框或真实前框，逐帧独立预测。使用各自原前框时，预测坐标与存档轨迹的最大误差小于 0.000001 像素。

- **前序偏移会放大。** 白车第 23 帧，仅把 SS 的前框换成基线前框，IoU 就从 0 升到 0.862；反向交换，基线从 0.851 降到 0。
- **同一搜索区域内，目标选择也会不同。** 人群第 165 帧，两版都使用 SS 前框时，基线 IoU 为 0.746，SS 为 0.014。足球第 63 帧，两版都使用基线前框时，基线为 0.818，SS 为 0.031。
- **解释边界。** 这些失败案例支持“关键帧选错目标、后续搜索区随之偏移”这一过程。当前证据尚不足以将其归因于 SS 训练损失，也不能直接解释 DepthTrack 的下降。[完整实验记录](汇报/结果/搜索区域对照/实验记录.md) · [逐帧数据](汇报/结果/搜索区域对照/逐帧结果.csv) · [回放脚本](汇报/结果/搜索区域对照/replay.py)

按序列配对重采样 10,000 次，成功率差值的 95% 区间（百分点）为 LasHeR SR [−1.93, +0.18]、RGBT234 MSR [+0.37, +1.58]、VisEvent SR [−1.37, +0.04]。区间反映测试序列构成的影响，未覆盖训练随机性。

**下一步。** 核验 VOT2022 最终报告；对提高、持平和退步的序列施加相同的 0%、10%、20%、30% 搜索框偏移，比较两版定位对偏移的敏感程度。此偏移实验尚未执行。组会 PPT 暂缓制作，PPT Master 已安装。

**22:00 更新。** VOT2022-RGBD 的跟踪评测已到 100%，工具记录评测成功结束，随后启动指标分析。此时最终报告和基线对照文件尚未生成。

**22:19 核验。** VOT2022-RGBD 的 127 条序列完成计分，三组训练、五项完整测试均已结束。基线与 SS 的 EAO 为 0.73760 → 0.72659，准确率为 0.82064 → 0.81514，鲁棒性为 0.88600 → 0.87463。[完整报告](汇报/结果/VOT2022_RGBD_SS_ep25/results.json) · [基线对照](汇报/结果/VOT2022_RGBD_SS_ep25/comparison.json)

## 2026-11-12（周四）

### RGB-T 搜索区域 SS 消融

接手时服务器旧 RGB-T 目录只有第一版 SS 的 smoke 和 full；现有 tmux 无 A/B。分别从 ss-v1（9cbd945）建立独立检出，A 提交 4067d59（codex/ss-template-only），B 提交 913bda9（codex/ss-target-aware），两分支已推送。实训代码取自 training_runs/20261103_pairwise_ss/code，再叠加对应分支的实验文件。逐文件忽略换行符比对，标签与实训副本在训练入口、梯度累积器、训练器、LasHeR 读取、处理与采样、网络层、损失工具、评测和本机路径配置等处不同；只检出 Git 标签不足以重现实训。旧启动命令明确 --seed 0。

两组均从 vitb_256_mae_ce_32x4_ep300/OSTrack_ep0300.pth.tar 初始化。LasHeR_train 每轮 59,968 样本，单卡微批 4，累积 16，有效批量 64，937 次更新；LasHeR_val 每 5 轮验证，60,000 样本。60 轮，FP32，AdamW，学习率 0.0004，第 48 轮阶梯衰减。A 的总权重、模板、搜索系数为 0.1、0.5、0；B 为 0.1、0.5、0.5，搜索项按裁剪后归一化 xywh 的 patch 覆盖率计算，每样本内对前景–前景及双向前景–背景分别按质量归一并平均有效组。框仅由训练 Actor 传给辅助项。B 的微小框、跨界框、全出界框和全前景框已完成有限梯度检查。

服务器根目录 /nas/liziyan103/seatrack/training_runs。A 子目录 20261112_ss_template-only，GPU 4，会话 rgbt_ss_template-only；B 子目录 20261112_ss_target-aware，GPU 5，会话 rgbt_ss_target-aware。每组单独保存 code、smoke、full 和 TensorBoard 输出。两组真实数据短测首 16 微批的加权 SS 分别为 0.00115 和 0.00248。正式训练和评测状态以后续核验为准。计划末轮文件为各组 full/checkpoints/rgbt_ss/SEATrack_ep0060.pth.tar；原评测脚本仅替换实验路径，加载后核验轮次、网络和哈希，输出至 full/eval_ep0060。

<details><summary>复现差异清单（lib、tracking、experiments 下的 Python 和 YAML）</summary>

- 同名但内容有差异：`experiments/seatrack/rgbd.yaml`、`experiments/seatrack/rgbe.yaml`、`experiments/seatrack/rgbt.yaml`、`experiments/seatrack/rgbt_ss.yaml`、`lib/models/layers/attn.py`、`lib/models/layers/attn_blocks.py`、`lib/models/layers/head.py`、`lib/models/layers/patch_embed.py`、`lib/test/evaluation/local.py`、`lib/test/parameter/seatrack.py`、`lib/test/tracker/data_utils.py`、`lib/test/tracker/seatrack.py`、`lib/test/vot/seatrack_baseline.py`、`lib/train/admin/local.py`、`lib/train/base_functions.py`、`lib/train/data/processing.py`、`lib/train/data/processing_utils.py`、`lib/train/data/sampler.py`、`lib/train/dataset/lasher.py`、`lib/train/run_training.py`、`lib/train/train_script.py`、`lib/train/trainers/ltr_trainer.py`、`lib/utils/focal_loss.py`、`lib/utils/heapmap_utils.py`
- 服务器副本独有：`experiments/seatrack/rgbd_ss_HuBcot.yaml`、`experiments/seatrack/rgbd_ss_HuBcot_smoke.yaml`、`experiments/seatrack/rgbe_ss_PzOoDM.yaml`、`experiments/seatrack/rgbe_ss_PzOoDM_smoke.yaml`、`experiments/seatrack/rgbt_ss_baseline.yaml`、`experiments/seatrack/rgbt_ss_smoke.yaml`、`lib/train/trainers/accumulation.py`
- 标签独有：无

</details>

**正式训练核验。** 两组各完成 32 个短测训练批次、2 次优化器更新和 4 个验证批次；短测权重已保存并成功加载，内部轮次为 1。正式训练独立从 OSTrack 初始化，两个会话均已输出第 1/60 轮第 160/14,992 批（10 次更新）。A 总损失 1.75007、IoU 0.64858、加权 SS 0.00122；B 分别为 1.75664、0.64749、0.00259。尚无末轮性能结论。查看进度可在服务器运行 `tail -f /nas/liziyan103/seatrack/training_runs/20261112_ss_*/full/train.log`。

另设 rgbt_ss_comparison 会话，在两套全量评测均成功后生成 B 目录 full/comparison.md，复核名单、帧数、标注指纹及两个失败序列的连续五帧跟偏/恢复。将 A 的 LasHeR SR 高于第一版 SS（未舍入）作为启动半权重对照的判据；满足时使用独立 20261112_ss_half-weight 目录，从相同预训练权重开始，模板和搜索各 0.5、总权重 0.05。

### 2026-11-12 · RGB-T 频段互换观察

使用第 60 轮未加 SS 与第一版 SS，在相同的存档 SS 前框下完成 8 段 LasHeR 回放，共 88 帧、880 次预测。失败窗口中的 44 个原始融合 IoU 复现旧回放。第一版 SS 在白车第 23 帧采用“红外低频＋RGB 高频”后 IoU 从 0 升至 0.811，匹配幅值后为 0.825；人脸第 165 帧两种互换均未找回。6 段稳定对照的平均 IoU 从 0.802 降为 0.768 / 0.771。暂不支持固定模态频段分工，未做闭环或全量频域评测。[完整数据和方法](汇报/结果/RGBT频段互换观察/实验记录.md)；组会成果展示版已增加响应图对照。

### RGB-T 决策图频段融合及闭环评测（11 月 12 日 11:30 核验）

冻结第一版 SS 第 60 轮权重，两路最后的搜索特征各自经过同一中心分类头获得 sigmoid 前的得分图，频域加权在中心图上完成，框大小、偏移、Hann 窗和解码沿用原版。沿用 0.25 周期/格的径向截止频率，每个频段一个全局 RGB 权重，红外权重取补数。对 48 条 LasHeR 训练序列 384 帧做 150 次 Adam 更新，仅拟合两个参数；梯度有限且非零。验证使用另外 16 条序列 128 帧；拟合和验证均剔除 LasHeR 测试名单。RGB 的低、高频权重分别为 0.97319、0.26820。位置分类验证交叉熵：等权 2.72052、RGB 低＋红外高 2.73506、红外低＋RGB 高 2.81659、学习融合 2.69162。训练样本、权重与验证数据保存在 [fit.json](汇报/结果/RGBT决策图频段融合/fit.json)。

闭环复查以首帧初始化，之后每一步用自己上一帧的预测框。第一版 SS → 学习融合：whitesuvturn（137 帧）第 23 帧 IoU 0 → 0.86151，整段 SR 15.5718% → 15.5718%；1blackteacher（851 帧）第 165 帧 IoU 0.01379 → 0.01518，整段 SR 16.0539% → 16.0651%。两条案例不足以估计总体增益。服务器 evaluation_runs/decision_frequency_20261112 位于 /nas/liziyan103/seatrack 下，GPU 6；tmux 会话 rgbt_decision_frequency 顺序评测学习融合、等权、两种固定决策图频段；rgbt_frequency_controls 随后补测两种固定特征层互换并汇总。每种方案按旧协议评测 LasHeR 245 条、RGBT234 234 条，以已归档的原 SS 作对照。[关键序列原始数据](汇报/结果/RGBT决策图频段融合/pilot.json)
