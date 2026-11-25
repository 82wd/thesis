# 项目文档与证据索引

整体原理与主要结果见 [README](README.md)，当前任务与最后核验状态见 [项目交接](项目交接.md)。本页负责资料导航，不另外维护一份运行进度表。以下历史材料保留其原始日期；旧待办与旧分支描述不能替代当前代码及后续结果。

## 研究要求与实现解释

| 入口 | 内容与阅读边界 |
|---|---|
| [师兄想法](师兄想法.md) | 10.18 SS、11.9 频域、11.12 消融和11.18寄存器等原始要求；提出不代表实现 |
| [早期理解](理解.md) | 表征约束与 anchor 的早期设想；当前 SS 已采用完整 pairwise 矩阵 |
| [原 SEATrack README](SEATrack-main/README.md) | 原模型、安装、数据准备、训练评测与引用 |
| [SS 实现](SEATrack-main/README_SS.md) | 数学定义、损失系数、接入点和代码说明 |
| [SS 消融](SEATrack-main/README_SS_ABLATION.md) | search-only、逐层配置、训练日志；配置存在不代表全量实验已完成 |
| [频域融合](SEATrack-main/README_FREQUENCY_FUSION.md) | 当前无 SS 的固定特征融合与四组对照 |
| [寄存器与 RG](SEATrack-main/README_REGISTER_GUIDANCE.md) | token 位置、参数、特征外推、测试与评测边界 |
| [11月17日项目梳理](汇报/项目梳理/SEATrack_三个想法_已完成与下一步_20261117.md) | 当时三个方向的详细解释；不含随后完成的全部结果与寄存器进展 |

## 实验过程与完整结果

| 入口 | 内容与阅读边界 |
|---|---|
| [实验日记](diary.md) | 按日期记录目的、做法与结果 |
| [阶段实验日志](seatrack/实验日志.md) | 早期复现、初版 SS 与消融的阶段总结；进展以记录截止日期为界 |
| [复现日志](seatrack/复现日志.md) | 环境排障、权重核查、多模态评测和 SS 接入原始记录 |
| [LasHeR 旧基线](汇报/结果/LasHeR_旧基线_20261104/README.md) | 指标来源、权重身份和核验边界 |
| [template-only／target-aware 对比](汇报/结果/RGBT_SS_AB_ep60/20261112_ss_target-aware/full/comparison.md) | A/B 消融指标及逐序列统计 |
| [search-only ep60](汇报/结果/SS_search_ep60_20261119/评测记录.md) | LasHeR、RGBT234 两套全量结果、样本数及评测协议 |
| [half-weight ep60 归档](汇报/结果/SS_half_ep60_20261123) | 已下载的原始结果；尚未核验的任务状态查交接，不根据目录名推断完成 |

## 可视化、失败案例与优化分析

| 入口 | 内容与阅读边界 |
|---|---|
| [ep20 可视化](汇报/结果/SS_vs_baseline_ep20_20261104/README.md) | 视频、关键帧、SS 热力图及查看方式；中期表征改善不等于最终精度提升 |
| [搜索区域交叉回放](汇报/结果/搜索区域对照/实验记录.md) | 控制上一帧框后的 5 个失败案例分析；单步回放而非闭环全量测试 |
| [频段互换观察](汇报/结果/RGBT频段互换观察/实验记录.md) | 选定失败与稳定片段上的频域诊断、RMS 匹配及限制 |
| [决策图融合数据](汇报/结果/RGBT决策图频段融合) | 冻结初版 SS 后学习两个频段权重的历史实验；区别于当前无 SS 特征融合 |
| [search-only 训练动态图说明](汇报/结果/SS_search_训练动态_20261118/读图说明.md) · [Python 版](汇报/结果/SS_search_训练动态_20261118/Python版/读图说明.md) | 总损失、逐层 SS 与 IoU 曲线的解释 |
| [SS 优化动态](汇报/结果/SS_优化动态_20261121) | 末轮权重上的梯度范数、方向与原始数据；不是全程或多次独立训练结果 |
| [DepthTrack 退步诊断](汇报/PPT/SEATrack_SS_20261111/sources/DepthTrack_退步诊断.md) | 汇报使用的序列级分析，注意与正式 F 分数的区别 |

## 部署、数据与检查

| 入口 | 内容与适用范围 |
|---|---|
| [项目交接](项目交接.md) | 连接方式、当前日志、权重与监控入口；状态必须结合核验时间 |
| [寄存器部署](server_setup/register_20261123/README.md) | 独立代码快照、小批验证、正式训练设置与监控 |
| [SS 初版部署包](server_setup/pairwise_ss_20261103/README.md) | 11月3日历史部署，不能当作当前 search-only 或寄存器快照 |
| [可视化工具说明](server_setup/pairwise_ss_20261103/可视化说明.md) | ep20 可视化的生成与核验方式 |
| [数据划分说明](SEATrack-main/lib/train/data_specs/README.md) | 上游数据名单文件的含义 |
| [pairwise SS 改动日志](SEATrack-main/logs/2026-11-03_pairwise_ss.md) | 从 anchor 改为完整 pairwise SS 的过程 |
| [初次测试](SEATrack-main/logs/2026-11-03_pairwise_ss_tests_initial.txt) · [后续测试](SEATrack-main/logs/2026-11-03_pairwise_ss_tests.txt) | 历史测试证据，不代表当前版本重新运行过 |
| [安装验证](server_setup/pairwise_ss_20261103/LOCAL_VALIDATION.txt) · [PatchEmbed 验证](server_setup/pairwise_ss_20261103/PATCH_EMBED_VALIDATION.txt) · [进度面板验证](server_setup/pairwise_ss_20261103/PROGRESS_VALIDATION.txt) | 历史部署包本地检查记录 |

[server_setup](server_setup) 下其他按日期命名的脚本用于具体实验恢复、诊断和评测。运行前先核对其路径、权重和配置，不能把历史脚本直接当作通用启动入口。

## 汇报与讲解材料

| 入口 | 用途 |
|---|---|
| [11月5日导师汇报提纲](汇报/2026-11-05_导师汇报提纲.md) · [一页工作汇报](汇报/2026-11-05_一页工作汇报.md) | 早期阶段成果与汇报结构 |
| [11月11日 SS 组会工作区](汇报/PPT/SEATrack_SS_20261111/README.md) | SS 机制、结果和退化分析 |
| [11月17日双线实验工作区](汇报/PPT/SEATrack_双线实验组会_20261117) | SS 与频域方向的阶段解释 |
| [11月18日实验复盘工作区](汇报/PPT/SEATrack_实验复盘_20261118) | 实验方法、结果与复盘材料 |
| [11月19日论文图风格工作区](汇报/PPT/SEATrack_论文图风格_20261119) | 图表、PPT、讲稿与排版产物 |

各 PPT 工作区中的 README、`sources/`、`notes/`、设计规范与制作规格分别服务于该次汇报。复用前更新过时的实验状态；精度结论回到原始结果，不能以讲稿代替证据。

## 历史副本与协作规则

- [AGENTS.md](AGENTS.md)：项目协作约定和接手入口。
- [日记重写前存档](seatrack/日记存档/diary_重写前_20261123.md)：历史追溯，不与现行日记并行维护。
- [部署包 SS README](server_setup/pairwise_ss_20261103/payload/README_SS.md)与[部署包日志](server_setup/pairwise_ss_20261103/payload/logs/)：打包时的代码说明副本，不代表当前源码。
- [另一份 ep20 可视化 README](<汇报/结果/SS_vs_baseline_ep20_20261104 2/README.md>)：历史副本，日常查看使用上方主要入口；未据此认定整个目录相同。
- [git.md](git.md)：当前为空，不作为 Git 操作说明。

维护时将新说明链接加入对应类别，实时进度只在交接维护，具体过程写入日记，原始结果保存在结果目录。本页整合日期：2026-11-25；未改写历史实验材料或清理副本。
