# 旧RGB-T基线 LasHeR 指标补齐

2026-11-04用户在服务器执行原Python参考指标脚本后回传。245个序列、220703帧，PR=71.5711%、NPR=67.8312%、SR=57.5125%；Invalid GT frames=1260，carried-forward predictions=0。

来源为旧自训练RGB-T第60轮，SHA256：e2547abb9c45b5b47601fae155ee3ede8e6946b6448f694ed34996b18e09da4d。启动命令在计算前已对预测使用清单检查该SHA；用户回传指标表示该检查未阻断流程。

服务器报告：`/nas/liziyan103/seatrack/SEATrack/RGBT_workspace/self_rgbt_ep0060/lasher_metrics_20261104.json`。

本地完整JSON已下载并独立解析：245个唯一序列、220703帧，逐序列统计与汇总一致；PR/NPR/SR与用户回传一致，无全零曲线被排除。报告SHA及本地核验摘要保存在local_verification.json。逐序列输入SHA字段格式已检查，但原始远端轨迹和标注未在本地重新计算哈希。

使用现有245条轨迹，只进行CPU指标计算，无新增GPU推理或训练。沿用历史Python参考协议，未MATLAB交叉验证，visible.txt与工具annos等价性未逐项确认。1260为该实现判定的无效GT帧数，不直接等同于数据损坏；未自行删除帧。
