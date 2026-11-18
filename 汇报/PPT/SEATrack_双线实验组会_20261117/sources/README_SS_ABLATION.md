# SS 小步消融：search-only 与逐层验证

依据根目录《师兄想法.md》第三部分（11.12），先在 LasHeR 上验证 SS，再决定是否扩展到其他 benchmark。本次没有引入频段融合。

## 如何修改

- `lib/models/layers/semantic_alignment.py`：区域权重为 0 时直接跳过该区域的相似度矩阵计算。search-only 只计算两模态 search token 的区域内两两余弦相似度矩阵，再用 MSE 对齐；不是直接对齐两模态特征，也没有增加 anchor。
- `lib/models/seatrack/vit_ci.py`：保留跨层平均的训练目标，额外返回每层损失，供收敛观察。层号按执行顺序匹配，支持配置中层号乱序。
- `lib/train/actors/seatrack.py`：将每层损失写入现有 status，沿用训练器的训练/验证日志及 TensorBoard epoch 曲线。
- `tests/test_semantic_alignment.py`：补充 search-only 公式、模板直接梯度为零、跳过无效模板值和单层日志一致性的检查。

原 `rgbt_ss.yaml` 保留为 template + search 对照；新增配置都只使用 LasHeR 的 train/val 数据。原 RGB-D、RGB-E 配置不变。`server_setup` 是历史部署快照，本次未同步；运行新实验时请部署当前 `SEATrack-main` 代码与配置。

## 实验配置

| 配置名 | 约束位置 | 层号（从 0 开始的 block 输入） |
|---|---|---|
| rgbt_ss | template + search，旧版对照 | 3, 5, 7, 9, 11 |
| rgbt_ss_search | search-only，多层 | 3, 5, 7, 9, 11 |
| rgbt_ss_search_l3 | search-only，单层 | 3 |
| rgbt_ss_search_l5 | search-only，单层 | 5 |
| rgbt_ss_search_l7 | search-only，单层 | 7 |
| rgbt_ss_search_l9 | search-only，单层 | 9 |
| rgbt_ss_search_l11 | search-only，单层 | 11 |

query image 在这里解释为 search image。先比较旧版与 search-only 多层，再逐个训练单层配置，以区分区域选择与层选择的影响；不自动启动全部实验。

所有新配置使用 TEMPLATE_WEIGHT=0、SEARCH_WEIGHT=0.5、SS_WEIGHT=0.1。因此附加目标为 `0.05 × 所选层 search MSE 的平均值`。保留原 search 项的系数，避免删除模板约束的同时把 search 项翻倍。关闭区域的日志值为 0，表示未计算，不表示模板已对齐。模板仍可通过 backbone 自注意力间接影响 search 特征；这里仅去掉模板区域的直接 SS 约束。

## 运行

在已安装项目依赖、配置数据路径和预训练权重的服务器上，从 `SEATrack-main` 执行：

```bash
python -m unittest discover -s tests -v
python tracking/train.py --script seatrack --config rgbt_ss_search --mode single --save_dir ./output/rgbt_ss_search
```

将配置名换为 `rgbt_ss_search_l3` 等，并为每次实验使用独立 save_dir。各组应从相同初始权重开始，保持训练预算、数据和评测协议一致；不要接着旧 SS checkpoint 训练来充当公平消融。先用 LasHeR 验证集选择配置，最终再统一评测测试集。

## 收敛观察与验证范围

现有日志中的 `Loss/ss`、`Loss/ss_search`、`Loss/ss_template`、`Loss/ss_weighted` 保留。新增 `Loss/ss_loss_layer_3`、`Loss/ss_search_layer_3`、`Loss/ss_template_layer_3` 等指标；具体层号随配置变化。使用训练器现有 TensorBoard 目录观察训练与验证曲线，同时比较跟踪损失及最终跟踪指标，不能仅凭 SS 下降判定有效。

本地 Python 语法检查通过；运行 unittest 时因当前环境缺少 torch 而未能执行。尚未进行 GPU 训练或 benchmark 评测，不能据此声称精度提升。推理仍使用原特征相加及预测头，新增逐层输出仅在计算 SS 时产生。


## 2026-11-17：服务器跨轮停滞修复

服务器 `training_runs/20261116_ss_search` 首轮 1875 批训练结束后，日志近两小时未更新，GPU 5 利用率为 0%，主进程等待数据，下一轮 worker 处于锁等待。现象符合默认 fork 在已初始化线程环境中创建 worker 后的等待问题；未取得调用栈，根因仍属推断。

`lib/train/data/loader.py` 对多进程加载显式使用 `spawn`，并设置至少 180 秒的取批超时；`num_workers=0` 保持单进程及原 timeout。服务器和本地实现同步。9 项既有测试通过；真实 LasHeR 两轮短测使用 batch 32、10 workers，每轮 4 个训练批次和 2 个验证批次，成功跨轮，保存并重新加载第 2 轮权重，参数有限。短测只验证流程，不代表完整 60 轮完成或精度提升。

旧进程已定向停止，旧日志、输出及修改前 loader 保存在服务器实验目录的 `repair_20261116_173339/`（目录时间为 UTC）。旧运行没有 checkpoint，正式训练重新从原初始化权重、seed 0 开始；未加载短测权重。原正式配置仍为 batch 32、每轮 60000 样本、60 轮、每 5 轮验证一次。tmux 会话仍为 `ss_search_20261116`，正式训练窗口为 `train-repaired`；监控增加日志超过 300 秒未更新的提示，提示不等于自动诊断。


### 进度监控

通用只读面板：[training_monitor.py](../server_setup/training_monitor.py)。仅使用 Python 标准库，每 10 秒显示轮次/批次、训练和验证损失、GPU、权重文件数量及训练阶段 ETA。超过 300 秒无日志更新会提示疑似停滞并隐藏 ETA；告警仅显示在终端，不发送外部通知，不自动重启。完成状态需同时有退出码 0、结束日志和非空末轮权重文件，未加载权重校验内容。

已部署至服务器实验目录，运行在 `ss_search_20261116:1.0` 的 watch 窗口。连接服务器后执行 `tmux attach -t ss_search_20261116`，按 `Ctrl+B` 再按 `1` 查看。按 `Ctrl+B` 再按 `D` 可离开并保持后台刷新。

```bash
# 在服务器运行；默认指向本次 search-only 实验
/nas/liziyan103/anaconda3/envs/seatrack/bin/python /nas/liziyan103/seatrack/training_runs/20261116_ss_search/training_monitor.py --once
# 其他实验可指定 --root /path/to/run --config CONFIG --gpu GPU_ID
```

监控测试：`python3 -m unittest discover -s server_setup/tests -v`（从仓库根目录运行）。2026-11-17 共 12 项测试通过，包括旧面板测试和新增的字段解析、停更、完成证据及异常结束检查。
