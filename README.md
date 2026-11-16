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

- [频段融合模块](SEATrack-main/lib/models/layers/frequency_fusion.py)
- [模型接入位置](SEATrack-main/lib/models/seatrack/vit_ci.py)
- [实验配置目录](SEATrack-main/experiments/seatrack/)
- [频段融合测试](SEATrack-main/tests/test_frequency_fusion.py)
- [项目文档与历史实验导航](PROJECT_GUIDE.md)：原总 README 的文档索引与历史进展。
- [实验日志](seatrack/实验日志.md)：历史实验记录；此前频段观察不等于本分支新实现的评测结果。
