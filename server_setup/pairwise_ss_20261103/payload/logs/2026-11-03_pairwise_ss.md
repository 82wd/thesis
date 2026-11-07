# 2026-11-03 操作日志：将 anchor SS 改为完整 pairwise SS

日期使用北京时间。此文件记录本次代码操作与目的，不是训练指标日志。

## 需求与实现约定

师兄建议：先使用标准空间自相似性，逐 patch 两两计算并构成 loss；暂不采用平均池化或可学习 query 构建 anchor，先验证完整 SS 是否有效。

本次具体实现采用逐 patch L2 归一化后的余弦 Gram 矩阵，在 RGB 与 X 两路之间计算矩阵 MSE。模板与搜索分开计算，完整保留对角线与上下三角，按 batch 和全部 N² 元素求均值；区域权重、取特征层及最终 loss 权重沿用原配置。上述是本次明确采用的实现细节，不代表师兄已指定所有公式细节。

## 操作与目的

| 顺序 | 操作 / 文件 | 目的与结果 |
| --- | --- | --- |
| 1 | 阅读现有 SS 模块、骨干、Actor、优化器、配置、测试及 README | 确认旧实现是 N-to-1 anchor 约束，确定损失到训练器的完整路径。当前目录不是 Git 仓库。 |
| 2 | 修改前备份本次涉及的原文件到 `/tmp/seatrack-before-pairwise-20261103` | 在没有 Git 的情况下保留本次修改前的原内容；临时目录不是长期版本管理。 |
| 3 | `lib/models/layers/semantic_alignment.py`：类改为 `SpatialSelfSimilarityAlignment`，去除 mean/query 分支、query 参数，改为 `normalize(F) @ normalize(F).T` | 每个空间 patch 与同区域内全部 patch 比较，直接验证跨模态空间关系对齐的作用。 |
| 4 | SS 分支显式关闭 autocast，以 FP32 计算矩阵和 MSE | 仅 `.float()` 不足以防止矩阵乘法被外层 AMP 降为低精度；保留梯度路径并处理零向量。 |
| 5 | `lib/models/seatrack/vit_ci.py` 更新导入和构造参数 | 将新模块接入真实训练骨干；继续在选定 AMG block 输入处施加损失并按层平均。 |
| 6 | `lib/config/seatrack/config.py` 及 RGB-T / RGB-D / RGB-E 三份 SS YAML 删除 `ANCHOR` | 避免配置仍显示 mean/query 而实际执行 pairwise，引发实验含义混淆；基线默认关闭 SS。 |
| 7 | `lib/train/base_functions.py` 移除 `ss_alignment` 参数名称匹配 | 新 SS 无可训练参数，优化器只需原来的 LoRA、HMoE、scaling 路径。 |
| 8 | 保留 Actor 的 SS 加权、日志指标及推理开关 | 新损失沿用原训练接口，避免引入无关训练流程变化。 |
| 9 | 更新 `tests/test_semantic_alignment.py` | 用显式枚举 pair 的独立参考和手算矩阵检查公式；检查空间对应、梯度、参数量、矩阵尺寸、autocast、骨干集成及推理一致性。 |
| 10 | 重写 `README_SS.md` | 文档与当前代码同步，说明公式、运行命令、配置迁移、计算量和验证边界。 |
| 11 | 创建本日志 | 留存每项操作及其目的，便于向师兄说明与后续复查。 |

## 验证记录

- 本机默认 Python 未安装 PyTorch，旧 `/tmp/seatrack-ss-venv` 已不存在。
- 创建隔离测试环境 `/tmp/seatrack-pairwise-venv`，不修改项目 `environment.yaml` 或系统 Python。
- 首次依赖安装因受限网络 DNS 失败，随后以允许联网的方式重试。
- 首次测试未进入用例：训练模块导入所需的 TensorBoard 未安装。原始输出保存在 `2026-11-03_pairwise_ss_tests_initial.txt`；补装项目使用的 TensorBoard 2.14.0 后重试成功。
- 实际测试环境：Python 3.9.6、PyTorch 2.8.0、timm 0.9.7、NumPy 2.0.2，macOS ARM CPU。此环境用于本机验证，不替代项目 CUDA 环境。
- 语法检查：`lib/` 和 `tests/` 共 104 个 Python 文件全部通过 AST 解析。
- 配置差异检查：三份 SS 实验 YAML 除移除 `ANCHOR` 外，其余设置与修改前一致。
- 数值及集成测试：**8 项全部通过，耗时 5.181 秒**。命令：`/tmp/seatrack-pairwise-venv/bin/python -m unittest discover -s tests -v`，工作目录为项目根目录。
- 成功测试原始输出：[2026-11-03_pairwise_ss_tests.txt](2026-11-03_pairwise_ss_tests.txt)。
- 覆盖：显式枚举 pair 的参考值与手算值、模板搜索隔离、零向量、双路梯度、通道旋转关系不变性、空间顺序对应、64×64 / 256×256 矩阵、CPU autocast 下 FP32、实际缩小骨干上游 PEFT 梯度和优化器更新、开关 SS 的推理输出逐值一致、Actor 加权损失、旧 ANCHOR 配置拒绝及输入保护。
- 另外单独执行标准大小 `[1,320,768]` 随机特征的 SS 前后向，CPU autocast 下输出为 FP32，双路梯度有限且非零。

## 后续实验与边界

本次交付是可验证的代码改动；尚未开展真实数据完整训练和跟踪指标比较，也未验证 CUDA AMP 或多卡训练。CPU autocast 测试仅验证当前 CPU 上的 FP32 分支行为。

使用新的 `models_ss_pairwise` 保存目录，从与基线相同的初始化开始对比。不要自动续训到旧 mean/query 实验；query checkpoint 还包含已移除参数及不同优化器状态。权重 0.1 只是沿用起点，需要根据训练曲线和跟踪指标判断。完整 SS 不消除背景 pair 或模态配准误差的影响。
