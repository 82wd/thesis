<!-- ppt-master-schema: design-spec/v1 -->
# SEATrack 双方向实验复盘 - Design Spec

## I. Project Information
| Item | Value |
| --- | --- |
| Project Name | SEATrack 双方向实验复盘 |
| Canvas Format | ppt169 1280 × 720 |
| Page Count | 8 |
| Primary Language | zh-CN |
| Target Audience | 导师、师兄及课题组成员 |
| Communication Intent | 汇报实现、SS 补救证据和后续实验设计 |
| Desired Audience Outcome | 理解两路线差异并讨论消融顺序 |
| Core Message / Ask / Action | 分线验证；SS 补救尚未证明普遍改善 |
| Delivery Context | 中文组会现场，8–10 分钟 |
| Artifact Afterlife | 方法与计划查阅 |
| Reading Mode | balanced |
| Content Strategy | 基于本地记录；三种方法各一页，状态标日期，不推断实时进度 |
| Design Style | C 实验复盘：白底黑灰、问题—调整—证据 |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-11-17 |
| Design Spec Depth | brief |

## II. Canvas Specification
| Property | Value |
| --- | --- |
| Format | ppt169 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 60 px |
| Content Area | 1160 × 600 |

## III. Visual Theme
### Theme Style
- **Mode**: custom
- **Mode Behavior**: 按问题、实现、证据、调整、后续执行推进；每页先给可核验判断，结尾给下一步。
- **Visual style**: custom
- **Visual Style Behavior**: 白底黑灰的实验复盘，细线连接方法步骤，数字与短句强调证据。青灰标 SS，棕色标频域；背景平面区分方法和解释，不用拟物装饰。
- **Theme**: 实验记录的编号、细分隔线与边注
- **Tone**: 审慎、清晰、可讨论
### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | 画布 |
| Secondary background | #F3F4F4 | 分区 |
| Primary | #202629 | 标题 |
| Accent | #356E73 | SS |
| Secondary accent | #9A603E | 频域与待验证 |
| Body text | #303638 | 正文 |
| Secondary text | #626C70 | 注释 |
| Divider | #D7DDDF | 分隔 |

## IV. Typography System
### Font Plan
| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | 中性黑体，加粗 | PingFang SC | Arial | sans-serif |
| Body | 中性黑体 | PingFang SC | Arial | sans-serif |
- **Title stack**: Arial, PingFang SC, sans-serif
- **Body stack**: Arial, PingFang SC, sans-serif
### Font Size Hierarchy
| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 20 |
| Title | 32 |
| Subtitle | 24 |
| Annotation | 16 |
| Display | 52 |

## V. Layout Principles
### Deck-wide Direction
- **Hierarchy direction**: 判断句优先，流程或数值次之，来源在页脚。
- **Composition tendency**: 开场大标题，方法流程，证据左右对照，补救纵向进展，消融层位置序列。
- **Cross-page continuity**: 页码、研究路线标签；不重复相同布局承载不同任务。
- **Spacing posture**: 方法页与补救页较密，首尾留白。
- **Spacing anchors**: 60 / 24 / 40 / 0 / 36 px

## VI. Icon Usage Specification
- **Primary bundled library**: none
| Icon Path | Suitable Scenarios |
| --- | --- |

## VIII. Image Resource List
| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline
### Part 1: 方法、证据与安排
#### Slide 01 - 双方向实验复盘
- **Audience move**: 从分散实验到本次汇报主线。
- **Relationships**: order：问题、调整、证据、下一步。
- **Title**: SEATrack 双方向实验复盘
- **Core message**: SS 与频段融合分线验证，先解释结果再设计验证。
- **Content**: 两条路线；SS 补救；后续实验设计；2026-11-17。
#### Slide 02 - 两条路线，作用位置不同
- **Audience move**: 从混同模块到区分训练约束和融合算子。
- **Relationships**: order：两模态输入、嵌入、共享ViT、末层search相加、预测头；membership：AMG-LoRA与HMoE属于增强编码器；contrast：SS输入支路与末端融合改动。
- **Title**: 原模型：双流匹配、层内交互、末端相加
- **Core message**: SS 改训练目标，频段融合改预测头之前的融合。
- **Content**: 参照原论文图2重绘：RGB/X模板与search输入，共享权重Patch Embedding与堆叠ViT；AMG-LoRA对齐attention logits，HMoE跨模态融合；末层search相加入预测头。补全LN、注意力残差、HMoE残差、LN/MLP残差、HMoE残差；说明K/V LoRA、softmax前双向logits互引导、本路V不交换；HMoE分template/search融合、分层软路由与低秩专家；预测头输出中心分数/尺寸/偏移。
- **Composition**: 双流架构主图，下方增强层局部展开；注解两种新增干预位置。
#### Slide 03 - SS：对齐关系，而非逐元素特征
- **Audience move**: 理解 pairwise SS 的输入、计算、梯度路径。
- **Relationships**: order：区域特征、归一化、两两相似度、MSE、总损失；contrast：template/search 分开。
- **Title**: SS：对齐关系，而非逐元素特征
- **Core message**: 无新增参数的训练辅助项。
- **Content**: block输入前取两模态特征，主干继续AMG-LoRA/HMoE等原流程；辅助支路分template/search，归一化后两两余弦矩阵，以MSE对齐；模板64×64，搜索256×256；层索引3/5/7/9/11；区域各0.5，总权重0.1；无新增参数；反传优化上游PEFT，推理跳过；张量[B,320,768]，模板64、搜索256；完整矩阵含对角及上下三角，FP32、eps=1e-6、不detach；总目标和原跟踪损失系数；search-only权重保持及单层消融；direct布局、无CLS和不裁剪。
- **Composition**: 上部主干两路流，下部SS支路；矩形表示张量/运算，虚线为训练取特征，实线为前向流程。
#### Slide 04 - 频段融合：在末层 search 特征上替换相加
- **Audience move**: 理解固定频段选择和等权对照。
- **Relationships**: order：末层 search 特征、二维实数 FFT、频段权重、逆变换、原预测头。
- **Title**: 频段融合：在末层 search 特征上替换相加
- **Core message**: 截止0.25，保留复数系数；当前模块非学习。
- **Content**: 保留原AMG-LoRA/HMoE，末层归一化和恢复空间后取两路search；逐通道二维实数FFT；低频中心圆与高频补集示意只表达频段选取，不是真实谱；RGB低/红外高及反向组合完整复数系数；逆变换gain2送原预测头；等权直接返回相加；关闭SS；梯度可回传；不保证RMS一致；输入[B,256,768]恢复[B,768,16,16]，实数FFT频谱[B,768,16,9]，由空间网格推导而非写死；完整复数线性组合公式、四种对照、同一无SS权重与独立幅值敏感性检验；direct无CLS且保留率1。
- **Composition**: 双路特征、FFT、低/高频掩膜、汇合、逆变换、预测头的完整箭头架构；注明掩膜按中心化频谱示意。
#### Slide 05 - 想法三：search-only 与逐层消融
- **Audience move**: 将 SS 效果不稳拆成区域、层位置和强度三个可检验问题。
- **Relationships**: order：区域拆分、归一化、SS矩阵、MSE；order：编码器层深度；contrast：多层均值与单层约束。
- **Title**: Search-only + 逐层消融：约束哪里、在哪层约束？
- **Core message**: 只约束搜索且保留原系数，再定位层位置；最终结果待核验。
- **Content**: 模板权重0但继续原前向，搜索SS系数0.05；索引3/5/7/9/11多层均值与单层分别训练；记录训练和验证SS曲线，在LasHeR控制预算并评估跟踪指标。
- **Composition**: 区域损失路径、层深度序列、下方损失公式和验证边界；topology=yes。
#### Slide 06 - 局部改善尚未形成稳定收益
- **Audience move**: 从单点改善到理解证据边界。
- **Relationships**: contrast：SS 的 LasHeR 与 RGBT234；频段失败帧改善与稳定片段退化。
- **Title**: 局部改善尚未形成稳定收益
- **Core message**: SS 收敛、单帧救回均不等于全量提升。
- **Content**: SS LasHeR SR57.51→56.71，RGBT234 MSR63.73→64.67；历史SS频段回放白车IoU0→0.811；稳定66帧0.802→0.771；8段88帧880次预测；非闭环或全量结论。
#### Slide 07 - SS 补救：拆开区域、目标与层的影响
- **Audience move**: 从整体失败到可验证的消融问题。
- **Relationships**: order：已完成A/B与后续search-only逐层；contrast：移除搜索、目标感知、仅搜索。
- **Title**: SS 补救：拆开区域、目标与层的影响
- **Core message**: A/B 部分恢复，尚未超过 LasHeR 基线；下一步缩小验证范围。
- **Content**: A仅模板 SR57.31；B保留模板，搜索按目标覆盖率约束前景相关pair，SR57.29；基线57.51/初版56.71；A/B RGBT234 MSR64.03/64.06，低于初版64.67；search-only多层及单层，系数0.05，记录逐层曲线；结果待验证；半权重对照待核验。
#### Slide 08 - 下一步：先把因果拆清，再扩大实验
- **Audience move**: 明确待验证问题和推进顺序。
- **Relationships**: order：公平性核对、LasHeR消融、全量评测、扩大或组合。
- **Title**: 下一步：先把因果拆清，再扩大实验
- **Core message**: 先验证配置是否稳定有效，再扩展 benchmark。
- **Content**: SS先search-only后逐层；频域先相加/等权轨迹一致性，再双向频段；统一初始化/预算/seed/数据；验证集选择，测试集统一评估；保存证据。

## X. Speaker Notes Requirements
- **Generation**: enabled
- **Filename**: match each SVG filename under notes/
- **Content**: 依据最终可见内容解释流程与边界，列出本地来源；历史状态不说成实时状态。
- **Total duration**: 8–10分钟
- **Notes style**: 组会口语，清晰审慎
- **Presentation purpose**: 汇报实现、SS 补救与后续实验设计

## Nature-figure 原理图修订
02–04 按已确认内容重绘：整体架构与 AMG/HMoE 分解、SS 双区域损失、双路频谱融合与四组对照。采用 32/20/16 px 三级字号与原配色。16:9 投影尺寸覆盖期刊栏宽要求；SVG 显式 px 单位为审计保留。

## Idea 3 addition
P05: 想法三，search-only 与逐层消融。Relationships: 区域拆分、损失计算顺序、网络深度顺序；topology=yes。Composition: 上方区域损失路径，中间层位置序列，下方权重与评估。P05 modules: native shapes, text, arrows。原 P05–07 顺延为 P06–08，共 8 页。
