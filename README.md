# 毕设：基于 SEATrack 的跨模态表征约束

本仓库包含 SEATrack 代码、SS 改动、实验记录和汇报材料。环境安装、数据准备及原版训练评测流程见 [SEATrack 项目 README](SEATrack-main/README.md)。

## 代码改动说明

按改动阶段查阅对应 README：

| 阶段 | 改动内容 | 详细说明 |
|---|---|---|
| SS 初版 | 在 SEATrack 上增加 template/search 空间自相似性约束 | [README_SS.md](SEATrack-main/README_SS.md) |
| SS 消融 | search-only、单层与多层对照、逐层损失日志 | [README_SS_ABLATION.md](SEATrack-main/README_SS_ABLATION.md) |

当前新增实验入口为 SS 消融说明；原 SS 配置保留作为对照。后续每次新增改动说明 README 时，在此表追加链接和简要描述。

## 部署与实验资料

- [SS 初版服务器部署说明（历史快照）](server_setup/pairwise_ss_20261103/README.md)
- [LasHeR 旧基线结果](汇报/结果/LasHeR_旧基线_20261104/README.md)
- [SS 与基线第 20 轮结果对比](汇报/结果/SS_vs_baseline_ep20_20261104/README.md)
- [组会汇报材料说明](汇报/PPT/SEATrack_SS_20261111/README.md)
- [实验日记](diary.md)
