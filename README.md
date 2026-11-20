# SEATrack 频段融合实验（不使用 SS）

分支：`experiment/frequency-fusion`。

本分支验证师兄的第二个想法：**在未加 SS 的 SEATrack 基线上，用 RGB 与红外的不同频段组合替代最终特征相加，观察是否改善跟踪。** 第一步采用固定权重、无需训练的即插即用融合。

**完整实现、公式、配置参数与运行说明：[README_FREQUENCY_FUSION.md](SEATrack-main/README_FREQUENCY_FUSION.md)。**

## 本分支做了什么

- 在两路最后的搜索特征上做二维 FFT，按径向频率分为低频和高频，组合后逆变换回空间域，再送入原预测头。
- 新增四组频段实验配置，均设置 `MODEL.SS.ENABLED: false` 和 `TRAIN.SS_WEIGHT: 0`。
- 保留原始相加及等权对照，支持两种相反的模态频段组合。
- 无新增可学习参数，默认截止频率为 0.25 周期/token；频段组合的输出倍率为 2，幅值影响需单独分析。
- 评测时显式指定 checkpoint，避免默认加载其他实验权重。

旧 SS 代码和配置保留用于历史追溯；本分支的四组频段配置不启用 SS。关闭 SS 配置并不能消除已训练权重中的 SS 影响，**必须使用确认未加 SS 的基线权重**。

## 实验分组

| 配置 | 用途 |
|---|---|
| `rgbt_freq_baseline` | 原始 SEATrack 特征相加，基线 |
| `rgbt_freq_equal` | 等权对照，与原始相加精确一致 |
| `rgbt_freq_rgb_low` | RGB 低频＋红外高频 |
| `rgbt_freq_ir_low` | 红外低频＋RGB 高频 |

四组应先使用同一份无 SS 权重、相同数据及计分协议评测。先核验 baseline/equal 的轨迹一致性，再比较两种频段组合。

## 开始运行

环境安装见 [原项目说明](SEATrack-main/README.md)。先配置本机项目路径和评测器中的数据集路径，然后从仓库根目录执行：

```bash
cd SEATrack-main
export SEATRACK_CHECKPOINT=/absolute/path/to/non_ss/SEATrack_ep0060.pth.tar
CUDA_VISIBLE_DEVICES=0 python RGBT_workspace/test_rgbt_mgpus.py \
  --script_name seatrack --yaml_name rgbt_freq_baseline \
  --dataset_name LasHeR --mode sequential --num_gpus 1 \
  --variants freq_baseline
```

其他组同时更换 `--yaml_name` 与 `--variants`，使用独立的新输出目录。该命令生成跟踪轨迹，指标还需按统一协议计分。参数说明、训练入口与注意事项见 [频段融合实验 README](SEATrack-main/README_FREQUENCY_FUSION.md)。

## 验证状态

2026-11-16：15 项 CPU 测试通过，覆盖频段选择、FFT 梯度、等权一致性、骨干权重兼容及原 SS 回归。**尚未进行本分支的 CUDA 试跑和完整 benchmark 评测，暂无精度提升结论。**

```bash
# 在 SEATrack-main 目录执行
python -m unittest discover -s tests -v
```

## 代码与文档入口

| 文档 | 用途 |
|---|---|
| [实验日志](seatrack/实验日志.md) | 按阶段整合过程、结果及证据，是实验记录的主要入口 |
| [复现日志](seatrack/复现日志.md) | 早期复现、环境排障、权重核查及 SS 接入的原始过程记录 |
| [实验日记](diary.md) | 后续逐日记录、完整指标和报告链接 |
| [LasHeR 旧基线说明](汇报/结果/LasHeR_旧基线_20261104/README.md) | 基线指标来源、权重身份和核验边界 |
| [第 20 轮可视化说明](汇报/结果/SS_vs_baseline_ep20_20261104/README.md) | 查看视频、关键帧与 SS 热力图的方法及解释边界 |
| [搜索区域交叉回放](汇报/结果/搜索区域对照/实验记录.md) | 控制前一帧框后的失败案例分析 |
| [频段互换观察](汇报/结果/RGBT频段互换观察/实验记录.md) | 历史频段实验的方法、局部结果与限制 |
| [template-only / target-aware 对比](汇报/结果/RGBT_SS_AB_ep60/20261112_ss_target-aware/full/comparison.md) | A/B 消融结果及逐序列统计 |
| [DepthTrack 退步诊断](汇报/PPT/SEATrack_SS_20261111/sources/DepthTrack_退步诊断.md) | 汇报使用的序列级诊断，注意其与正式 F 分数的区别 |

## 部署、数据与验证说明

### 服务器环境与连接

以下信息整理于 2026-11-17，来源为 [复现日志](seatrack/复现日志.md)中的环境摸底、目录确认、环境验证和连接记录，以及 [实验日记](diary.md)中的后续实验目录。**这是已有记录的汇总，本次未连接服务器核验；GPU 占用、剩余空间和连接端口需使用前确认。**

| 项目 | 已有记录 |
|---|---|
| SSH 地址与用户 | `liziyan103@10.68.240.49` |
| SSH 端口 | 早期传输记录为 `10358`；2026-11-03 准备记录改用 `10343`，该条未实际连接验证 |
| 本地 SSH 密钥路径 | `~/.ssh/id_ed25519_82wd`（仅记录路径） |
| GPU | 7 张 NVIDIA GeForce RTX 4090，每张约 24 GB 显存；共享服务器 |
| 驱动 | 2026-10-10 记录为 `580.126.09`，驱动报告 CUDA `13.0`；此数值不代表 PyTorch 使用的 CUDA 运行时版本 |
| 用户家目录 | `/nas/liziyan103` |
| 项目根目录 | `/nas/liziyan103/seatrack` |
| 原始主代码目录 | `/nas/liziyan103/seatrack/SEATrack`；其内部 `SEATrack-main/` 被记录为重复旧副本，不作为运行入口 |
| 数据集根目录 | `/nas/liziyan103/seatrack/datasets`，早期记录含 `lasher/`、`depthtrack/`、`visevent/` |
| Conda 环境 | `/nas/liziyan103/anaconda3/envs/seatrack` |
| 实验环境版本 | Python `3.8.20`、PyTorch `2.2.2`，历史验证 CUDA 可用；最初摸底的 Python `3.12.2` 不是这里确认的实验环境 |
| 独立训练实验 | `/nas/liziyan103/seatrack/training_runs/`，各实验保存独立代码、配置、日志和 checkpoint |
| 独立评测实验 | `/nas/liziyan103/seatrack/evaluation_runs/`，具体运行目录见实验日记 |

确认当前端口后连接（以下采用较晚记录中的 `10343`）：

```bash
ssh -i ~/.ssh/id_ed25519_82wd -p 10343 liziyan103@10.68.240.49
```
登陆服务器

在校园网里：

直接按快捷键。脚本会自动直连服务器，不需要启动 Docker 或 EasyConnect。

用手机热点、家里网络时：

1. 开启 Clash Verge，让 Codex、ChatGPT 正常联网。
2. 打开 Docker Desktop，终端执行：

   docker start nwpu-vpn
3. Finder 按 ⌘K，连接：

   vnc://127.0.0.1:15901
   屏幕共享密码：ecLocal7。
4. 在 EasyConnect 中登录学校账号。登录成功后可以关闭屏幕共享窗口。
5. 按 iTerm 快捷键，脚本会在约 3 秒的直连检测后自动走 VPN。

注意：启动容器不等于 VPN 已登录。 使用期间保持 Docker 运行、EasyConnect 在线；如果提示 Connection closed by UNKNOWN port 65535，优先检查 VPN 是否掉线。

不用快捷键时，也可以直接在终端运行：

/Users/lzy/.local/bin/nwpu-ssh

在服务器使用已确认的实验解释器检查环境：

```bash
nvidia-smi
/nas/liziyan103/anaconda3/envs/seatrack/bin/python -c 'import sys, torch; print(sys.version); print(torch.__version__, torch.version.cuda, torch.cuda.is_available())'
```

运行约定与历史问题：

- 长任务使用 `tmux`；每次启动前重新检查 GPU，按实际空闲情况设置 `CUDA_VISIBLE_DEVICES`，不沿用日志中的旧 GPU 分配。
- Conda 曾出现 `conda-libmamba-solver` / `QueryFormat` 插件错误，日志使用 `CONDA_NO_PLUGINS=true` 绕过；已有环境中的 Python、PyTorch 和 CUDA 验证正常。
- 后续训练使用 `training_runs/` 下的独立代码副本，其中包含服务器适配和梯度累积等修改；仅检出历史 Git 标签不足以复现实训，具体差异见实验日记 2026-11-12 条目。
- 权重需按实验配置和来源清单选择。早期日志中对“官方权重”的称呼后来有来源疑问，不能仅凭目录名判断，也不能将经过 SS 训练的权重当作无 SS 基线。

### 部署与验证资料

| 文档 | 用途与适用范围 |
|---|---|
| [SS 初版部署包 README](server_setup/pairwise_ss_20261103/README.md) | 2026-11-03 历史安装包、独立实验副本及监控工具说明；不是当前 search-only 的部署快照 |
| [可视化工具说明](server_setup/pairwise_ss_20261103/可视化说明.md) | 第 20 轮可视化生成、核验与查看方式 |
| [数据划分文件说明](SEATrack-main/lib/train/data_specs/README.md) | 上游数据名单文件的含义 |
| [pairwise SS 改动日志](SEATrack-main/logs/2026-11-03_pairwise_ss.md) | 从 anchor 改为完整 pairwise SS 的实现过程与验证记录 |
| [初次测试输出](SEATrack-main/logs/2026-11-03_pairwise_ss_tests_initial.txt) · [后续测试输出](SEATrack-main/logs/2026-11-03_pairwise_ss_tests.txt) | 历史测试证据，不代表当前版本已重新运行 |
| [安装验证](server_setup/pairwise_ss_20261103/LOCAL_VALIDATION.txt) · [PatchEmbed 兼容验证](server_setup/pairwise_ss_20261103/PATCH_EMBED_VALIDATION.txt) · [进度面板验证](server_setup/pairwise_ss_20261103/PROGRESS_VALIDATION.txt) | 历史部署包的本地核验输出 |

## 汇报材料

| 文档 | 用途 |
|---|---|
| [2026-11-05 导师汇报提纲](汇报/2026-11-05_导师汇报提纲.md) | 当时的汇报结构与待办 |
| [2026-11-05 一页工作汇报](汇报/2026-11-05_一页工作汇报.md) | 当时的阶段成果摘要 |
| [2026-11-11 组会材料 README](汇报/PPT/SEATrack_SS_20261111/README.md) | PPT 工作区说明与产物入口 |
| [设计规范](汇报/PPT/SEATrack_SS_20261111/design_spec.md) · [制作规格](汇报/PPT/SEATrack_SS_20261111/spec_lock.md) · [逐页讲稿](汇报/PPT/SEATrack_SS_20261111/notes/) | PPT 制作与讲解资料 |

汇报材料中的训练轮次和“下一步”属于当时快照；查实验结论优先阅读实验日志。

## 历史副本与占位文件

以下文件保留供追溯，不作为当前代码说明的首选入口：

- [部署包内的 SS README](server_setup/pairwise_ss_20261103/payload/README_SS.md)、[部署包改动日志](server_setup/pairwise_ss_20261103/payload/logs/2026-11-03_pairwise_ss.md)及其 [测试记录目录](server_setup/pairwise_ss_20261103/payload/logs/)：打包时的历史副本。
- [第 20 轮可视化另一份 README](<汇报/结果/SS_vs_baseline_ep20_20261104 2/README.md>)：本次核对 README 内容与主要目录一致，未据此认定整个目录完全相同；日常查看使用上方主要入口。
- [git.md](git.md)：目前为空，尚无 Git 操作说明。

后续新增实验或代码改动时，将说明链接补入对应表格；总 README 只保留导航和简要结果，细节写入专项 README 或实验日志。
- [频段融合模块](SEATrack-main/lib/models/layers/frequency_fusion.py)
- [模型接入位置](SEATrack-main/lib/models/seatrack/vit_ci.py)
- [实验配置目录](SEATrack-main/experiments/seatrack/)
- [频段融合测试](SEATrack-main/tests/test_frequency_fusion.py)
- [项目文档与历史实验导航](PROJECT_GUIDE.md)：原总 README 的文档索引与历史进展。
- [实验日志](seatrack/实验日志.md)：历史实验记录；此前频段观察不等于本分支新实现的评测结果。