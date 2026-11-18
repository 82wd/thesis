# 完整空间自相似性（pairwise SS）损失

更新：2026-11-03。按照师兄建议，先验证完整 patch 两两关系对齐是否有效，暂时移除平均池化和可学习 query anchor。操作与目的见 [本次改动日志](logs/2026-11-03_pairwise_ss.md)。

## 1. 计算方式

在选定 backbone block 的入口，取 RGB 和 X 两路特征，按 `[模板; 搜索]` 拆开。每个区域分别计算：

```text
F_rgb, F_x: [B, N, C]
U = normalize(F, dim=-1, eps=1e-6)   # 每个 patch 沿通道维归一化
S = U @ U.transpose(-2, -1)         # [B, N, N]
L_region = mean((S_rgb - S_x)^2)    # 沿 batch、两个空间维取均值
L_layer = TEMPLATE_WEIGHT * L_template + SEARCH_WEIGHT * L_search
L_ss = mean(L_layer across selected layers)
L_total = 原跟踪损失 + SS_WEIGHT * L_ss
```

`S[i,j]` 表示同一模态内位置 i 与 j 的余弦相似度。对齐的是两种模态各自的关系矩阵，不是直接计算 RGB 与 X 的交叉相似度，也不是特征逐元素 MSE。

默认模板 N=64，矩阵为 `[B,64,64]`；搜索 N=256，矩阵为 `[B,256,256]`。模板、搜索分别计算，不包含模板与搜索之间的 pair。使用完整矩阵，包括对角线和上下三角，不做 mask 或只取上三角。非零特征的对角线约为 1；保留对角线对应明确的 N² 均值定义。零向量通过 epsilon 避免除零。

SS 分支禁用 autocast，归一化、矩阵乘法和 MSE 使用 FP32；不 detach 特征，梯度可回传到两路上游可训练模块。SS 模块没有可训练参数，不再生成 anchor。

## 2. 接入位置和配置

```yaml
MODEL:
  SS:
    ENABLED: true
    LAYERS: [3, 5, 7, 9, 11]
    TEMPLATE_WEIGHT: 0.5
    SEARCH_WEIGHT: 0.5
TRAIN:
  SS_WEIGHT: 0.1
```

`LAYERS` 是从 0 开始的 block 输入索引，即默认在第 4、6、8、10、12 个 block 之前计算。层范围仍为 `[2, depth)`，不得重复；过早的位置没有可被 SS 优化的上游 PEFT 参数。区域权重直接相乘，不自动归一化。0.1 沿用初始实验值，尚未针对完整 SS 调参。

全局配置默认关闭 SS；`rgbt_ss.yaml`、`rgbd_ss.yaml`、`rgbe_ss.yaml` 开启完整 pairwise SS。`MODEL.SS.ANCHOR` 已删除，旧 YAML 若仍含该字段会报配置错误，应先删除。原 anchor 损失与完整 SS 的数值尺度不同，不能直接比较两者日志值来判断效果。

保持 `TRAIN.PEFT: true` 时，仍训练原有 LoRA、HMoE、scaling 参数。SS 只通过辅助损失影响上游参数，不会在一次前向中先更新参数再运行 AMG。最后一个 block 自身仍通过跟踪损失训练。

普通 `model.eval()` 推理默认跳过 SS；验证 Actor 显式计算 SS 以记录损失。SS 开关不改变相同权重下的预测输出，也不增加推理参数。

## 3. 训练与比较

先按原 README 配好数据集路径、预训练权重和 CUDA 训练环境，在项目目录执行：

```bash
# 原基线
python tracking/train.py --script seatrack --config rgbt --save_dir ./models_baseline --mode single

# 完整 pairwise SS
python tracking/train.py --script seatrack --config rgbt_ss --save_dir ./models_ss_pairwise --mode single
```

RGB-D / RGB-E 对应改用 `rgbd_ss` / `rgbe_ss`。使用全新且独立的保存目录，避免训练器自动恢复旧 anchor 实验。旧 query checkpoint 含已移除的 query 参数和不同优化器状态，不能直接当作本版本的断点续训；旧 mean checkpoint 虽然没有额外参数，也不适合作为公平对比的新实验起点。

对照实验保持数据、初始化、训练轮数、优化设置和评测流程一致，比较实际跟踪指标，并观察：

- `Loss/ss`：选中层平均后的区域加权损失。
- `Loss/ss_template`、`Loss/ss_search`：各区域损失的层平均。
- `Loss/ss_weighted`：实际加入总损失的 SS 项。

SS 下降不等于跟踪精度提升。完整 SS 仍包含背景关系，也依赖模态间的空间对应关系。未新增配准、遮挡 mask 或可靠性加权。

## 4. 计算量与限制

相似度矩阵空间复杂度为 O(BN²)，计算复杂度为 O(BN²C)。每样本每模态每层，模板和搜索共有 64²+256²=69,632 个相似度元素；原 anchor 图为 64+256=320 个元素。这个比例只描述相似度结果数量，不代表整个模型计算量或显存的比例。训练峰值显存需在实际 batch size、层数下测量。

仍要求 `[模板; 搜索]` 的 direct 布局、不插入 CLS、`CE_KEEP_RATIO=1`，以保持跨模态空间位置对应；没有扩展或修复原 CE 裁剪分支。

## 5. 文件与验证

- `lib/models/layers/semantic_alignment.py`：`SpatialSelfSimilarityAlignment`，完整两两相似度和区域损失。
- `lib/models/seatrack/vit_ci.py`：实例化新的无参数模块；沿用原层位置和损失汇总。
- `lib/config/seatrack/config.py`、三份 `*_ss.yaml`：移除 anchor 选项。
- `lib/train/base_functions.py`：移除仅为旧 query 参数添加的优化器匹配项。
- `tests/test_semantic_alignment.py`：数值、梯度、混合精度上下文和真实小尺寸骨干集成测试。

```bash
python -m unittest discover -s tests -v
```

2026-11-03 本机验证：8 项 CPU 测试全部通过（5.181 秒），104 个 Python 文件通过语法检查。完整环境和原始测试输出见改动日志。CPU 测试不能替代真实数据训练、完整模型评测或 CUDA / 多卡验证，不据此宣称精度提升。
