# source

- Source: `source.pptx`
- Total slides: 8

## Slide 1

Spatial Self-similarity

SS：让两模态保持一致的空间关系结构

a 特征 → 关系矩阵 → 训练约束

F_RGB

S = U · Uᵀ

通道归一化

S_RGB

U = normalize(F)

patch 两两余弦相似

MSE

L_SS

\[B,N,C\]

区域加权、层平均

关系一致性

S = U · Uᵀ

通道归一化

F_IR

S_IR

保留反向梯度

同一区域内的位置对

b 模板与搜索分别约束，不跨区域配对

c 五个 block 入口，共享同一计算规则

64 × 64 → L_t

权重 0.5

Template · 64

3

5

7

9

11

零基索引 → 第 4 / 6 / 8 / 10 / 12 层之前

256 × 256 → L_s

Search · 256

权重 0.5

L_SS = mean_layers(0.5 L_t + 0.5 L_s)

L_total = L_tracking + 0.1 L_SS

不增加参数；反传更新上游 PEFT；推理跳过 SS。

L_tracking = 2 GIoU + 5 L1 + Focal；FP32、eps = 1e−6、不 detach；矩阵包含对角和双向位置对。

关系矩阵为结构示意，非实测热图。原编码器 AMG/HMoE 与预测头保持；direct、无 CLS、CE 保留率 1。

## Slide 2

搜索框交换：前序偏移与框内目标选择都有影响

逐序列：LasHeR 122 升／122 降／1 平，最差两条贡献约 −0.55 pp；VisEvent 最差五条贡献 −0.617 / 净 −0.635 pp。

白车从第 23 帧、人群从第 165 帧持续跟偏；足球连续 510 帧 IoU < 0.2，girl1 从第 60 帧至结尾连续 122 帧低于阈值。

目的：区分“上一帧定位偏移导致裁剪错误”和“在相同搜索区域内选错目标”。

固定输入

替换前一帧搜索框

两份固定权重

对比预测 IoU

首帧模板 + 当前帧

基线前框／SS 前框／GT 前框

基线／初版 SS

起点 −10 至 +15 帧

5 条失败序列，逐帧独立

控制搜索区域，GT 只作诊断

形成 2 × 3 组配对

无效标注跳过

白车第 23 帧：只换前框，即可改变成败

相同前框下，SS 仍可能选错目标

SS：自己的前框 0 → 基线前框 0.862

人群第 165 帧（同用 SS 前框）

基线：自己的前框 0.851 → SS 前框 0

基线 0.746；SS 0.014

起点后 16 帧平均：SS 用基线前框 0.831，用 SS 前框 0.009。

足球第 63 帧（同用基线前框）：基线 0.818；SS 0.031。

效果：支持“关键帧选错 → 搜索区偏移 → 后续持续失败”的过程解释。

这是非闭环诊断，不是补救算法，也不能单独证明 SS 损失导致退化；0/10/20/30% 人工偏移实验尚未执行。

持续跟偏：连续 5 帧基线 IoU ≥ 0.5 且 SS < 0.2；自前框回放坐标误差 < 10⁻⁶ px。

## Slide 3

SS 补救：约束的位置

a 区域消融

b Target-aware：把搜索关系拆成目标相关与背景关系

保留分支用蓝色；去掉仅指直接 SS 项

FG

BG

Template-only

L_t

L_s = 0

FG–FG

FG–BG

覆盖率 p_i

加权关系 MSE

连续软权重

各组归一 → 平均有效组

Search-only

L_t = 0

L_s

BG–FG

去掉

保留区域的最终系数均为 0.05

GT 框覆盖 patch

模板 SS 保留；GT 仅训练时用于辅助项，不增加预测网络。

原跟踪前向仍使用模板与搜索

示意中按 FG/BG 分块便于理解；实际用连续覆盖率构造位置对权重。

实验

目的

做法（最终附加项）

效果／状态

Template-only

搜索区域 SS 是否带来干扰

0.05 × mean(L_t)

LasHeR SR 57.31%

Target-aware

背景–背景约束是否不利

0.05 × mean(L_t + L_s,target)

LasHeR SR 57.29%

Search-only

仅约束 query/search 是否有效

0.05 × mean(L_s)，五层平均

LasHeR SR 56.70%

Half-weight / 单层

区分强度因素、定位有效层

0.025 × mean(L_t+L_s) / 单层 SS

56.95% / 单层待测

A/B 相对初版部分恢复，仍低于 LasHeR 基线；A 同时减弱总约束，需半权重对照排除混淆。

mean 为层平均；单层候选索引 3 / 5 / 7 / 9 / 11。矩阵与 GT patch 图均为机制示意。

## Slide 4

已有实验效果

消融只部分缓解退化，尚未找到稳定解法

LasHeR SR（%）

基线 57.51 ｜ 初版 SS 56.71

Template-only 57.31 ｜ Target-aware 57.29

Search-only 56.70 ｜ Half-weight 56.95

RGBT234 MSR（%）

基线 63.73 ｜ 初版 SS 64.67

Template-only 64.03 ｜ Target-aware 64.06

Search-only 63.60 ｜ Half-weight 待最终核验

结论

Template-only、Target-aware 与 Half-weight 对 LasHeR 有部分恢复，仍低于基线

Search-only 两套全量结果已完成，未恢复成功率；单层配置未完成独立重训评测

训练更新预算不完全匹配，不能将差异完全归因于 SS 区域选择

结果说明：现有消融界定了问题边界，还未证明有效补救

## Slide 5

从损失约束走向架构改动

寄存器：为特征交互增加可学习的计算位置

空间 patch

追加 registers

注意力交互

保留视觉输出

模板与搜索 token

4 个非空间 token

与 patch 共同计算

移除 registers

承载局部视觉信息

可学习初始参数

容纳额外信息

搜索特征进入预测头

动机与预期

与 SS 的关系

提供额外的信息交互位置

在无 SS 基线上独立训练

期望 patch 更平滑、结构更清晰

损失仍为原跟踪损失

高范数与精度收益仍需实测

不将架构收益与 SS 约束混合

增加计算槽位 → 改变特征交互 → 再检验跟踪收益

机制示意；实现依据 README_REGISTER_GUIDANCE.md，状态采用注明日期的核验记录。

### Speaker Notes

想法 4 · 从损失约束走向架构改动。寄存器：为特征交互增加可学习的计算位置。本页围绕图中的计算过程说明机制，实验结果与机制假设分别判断。

## Slide 6

token 布局与双模态路径

插入位置：前 9 层之后，后 3 层共同计算

两模态输入

blocks 0–8

blocks 9–11

移除寄存器

每路 64 template

原始视觉 token

追加 4 registers

LayerNorm 前移除

+ 256 search

共 320 个位置

320 → 324 tokens

256×768 搜索输出

共享初值，分别演化

保留空间接口

RGB / IR 共享 4×768 初始寄存器

顺序：\[template; search; registers\]

两路随后各自进行注意力计算

registers 不进入 HMoE 空间分组

新增参数总数为 3,072

原 RGB+IR 融合及 CENTER 头保留

新增 token 参与计算，但不直接作为目标框预测输出

机制示意；实现依据 README_REGISTER_GUIDANCE.md，状态采用注明日期的核验记录。

### Speaker Notes

想法 4 · token 布局与双模态路径。插入位置：前 9 层之后，后 3 层共同计算。本页围绕图中的计算过程说明机制，实验结果与机制假设分别判断。

## Slide 7

可训练参数与反向传播

训练机制：通过跟踪损失学习寄存器

前向输入

特征交互

目标预测

反向传播

模板与搜索图像

Self-attention / AMG

搜索特征融合

2 GIoU + 5 L1

训练始终保留寄存器

MLP 更新全部 token

CENTER 原预测头

+ Focal loss

更新什么

怎样验证机制

训练 lora / moe / scaling 参数

观察 register / patch 范数分布

同时更新 register_tokens

固定样本比较空间特征与平滑度

主干大部分参数和预测头冻结

范数变大本身不等于跟踪更准

当前不做 register dropout；SS 与频域融合均关闭

机制示意；实现依据 README_REGISTER_GUIDANCE.md，状态采用注明日期的核验记录。

### Speaker Notes

想法 4 · 可训练参数与反向传播。训练机制：通过跟踪损失学习寄存器。本页围绕图中的计算过程说明机制，实验结果与机制假设分别判断。

## Slide 8

相同输入、相同权重，推理时两路对照

Register Guidance：外推有寄存器带来的特征变化

同一模型

求特征差

指导外推

一次预测头

有寄存器：F_reg

ΔF = F_reg

F_RG = F_reg

CENTER → bbox

无寄存器：F_no_reg

− F_no_reg

+ w × ΔF

Hann 与原框解码

推理代价与含义

当前证据与评测

w=0：仅有寄存器的一次前向

已通过本地与 CUDA 小批验证

w>0：骨干两次前向、预测头一次

60轮训练完成；ep60权重已保存

无寄存器分支不是独立训练基线

全量基线 / Register / RG 待比较

跟踪特征层的 RG 适配；不是对参考论文扩散采样的直接复现

机制示意；实现依据 README_REGISTER_GUIDANCE.md，状态采用注明日期的核验记录。

### Speaker Notes

想法 4 · 相同输入、相同权重，推理时两路对照。Register Guidance：外推有寄存器带来的特征变化。本页围绕图中的计算过程说明机制，实验结果与机制假设分别判断。
