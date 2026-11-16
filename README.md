# 毕设：基于 SEATrack 的跨模态表征约束

本仓库包含 SEATrack 代码、SS 改动、实验记录和汇报材料。环境安装、数据准备及原版训练评测流程见 [SEATrack 项目 README](SEATrack-main/README.md)。

## 代码改动说明

按改动阶段查阅对应 README：

| 阶段 | 改动内容 | 详细说明 |
|---|---|---|
| SS 初版 | 在 SEATrack 上增加 template/search 空间自相似性约束 | [README_SS.md](SEATrack-main/README_SS.md) |
| SS 消融 | search-only、单层与多层对照、逐层损失日志 | [README_SS_ABLATION.md](SEATrack-main/README_SS_ABLATION.md) |

当前新增实验入口为 SS 消融说明；原 SS 配置保留作为对照。后续每次新增改动说明 README 时，在此表追加链接和简要描述。

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

## 部署与实验资料

- [SS 初版服务器部署说明（历史快照）](server_setup/pairwise_ss_20261103/README.md)
- [LasHeR 旧基线结果](汇报/结果/LasHeR_旧基线_20261104/README.md)
- [SS 与基线第 20 轮结果对比](汇报/结果/SS_vs_baseline_ep20_20261104/README.md)
- [组会汇报材料说明](汇报/PPT/SEATrack_SS_20261111/README.md)
- [实验日志（整合入口）](seatrack/实验日志.md)
