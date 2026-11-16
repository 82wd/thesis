# 毕设：基于 SEATrack 的跨模态表征约束

本仓库包含 SEATrack 源码、SS 改动、实验记录和汇报材料。源码位于 `SEATrack-main/`，已包含本项目改动；下表按用途提供文档入口。详细实现和实验指标保留在对应文档中。

## 从这里开始

| 想了解什么 | 阅读入口 |
|---|---|
| 安装环境、准备数据、了解原项目训练评测流程 | [SEATrack 项目 README](SEATrack-main/README.md) |
| 师兄的三个研究想法 | [师兄想法](师兄想法.md) |
| 最初对表征约束的理解 | [理解笔记（早期思路）](理解.md) |
| 实验做到了哪一步、结果如何 | [实验日志（整合入口）](seatrack/实验日志.md) |
| SS 具体怎么实现、如何做消融 | 下方“代码改动说明” |

`理解.md` 中的 anchor 等设想不等于当前实现；以代码改动说明为准。SS 消融是 SS 方向的深化，频段融合是另一条实验方向，历史观察结果见下方索引。

## 代码改动说明

按改动阶段查阅对应 README：

| 阶段 | 改动内容 | 详细说明 |
|---|---|---|
| SS 初版 | 在 SEATrack 上增加 template/search 空间自相似性约束 | [README_SS.md](SEATrack-main/README_SS.md) |
| SS 消融 | search-only、单层与多层对照、逐层损失日志 | [README_SS_ABLATION.md](SEATrack-main/README_SS_ABLATION.md) |
| 频段融合（无 SS） | 搜索特征频域融合、原始相加及等权对照 | [README_FREQUENCY_FUSION.md](SEATrack-main/README_FREQUENCY_FUSION.md) |

本分支新增频段融合入口，四组频段实验配置均关闭 SS；原 SS 配置保留供独立实验使用。后续每次新增改动说明 README 时，在此表追加链接和简要描述。

## 实验进展

| 时间 | 做了什么 | 结果概况 |
|---|---|---|
| 2026-10-10～10-23 | 打通基线训练与多模态评测流程 | 报告完成归档核验，部分权重来源仍需追溯 |
| 2026-11-03～11-05 | 接入 SS、确认基线并制作中期可视化 | 短测通过；中期相似度改善不代表最终精度提升 |
| 2026-11-07～11-11 | 完成 SS 初版三模态、五测试集评测 | RGBT234 提升，其余四项下降 |
| 2026-11-12 | 探索频段互换和决策图融合 | 局部案例有改善，尚无总体收益结论；实验代码已移除 |
| 2026-11-12～11-16 | 完成 template-only / target-aware 消融 | 恢复部分 LasHeR 表现，但仍略低于基线；半权重结果待核验 |
| 2026-11-15～11-16 | 新增 search-only、逐层配置并部署服务器 | 9 项测试通过；最近核验为等待 GPU，暂无精度结果 |

详细设置、指标、证据链接和后续状态统一见 [实验日志](seatrack/实验日志.md)。以上为记录时的状态，不是服务器实时进度。

## 实验过程与结果索引

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
