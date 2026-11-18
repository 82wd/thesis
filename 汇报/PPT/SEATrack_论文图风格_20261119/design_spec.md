<!-- ppt-master-schema: design-spec/v1 -->
# SEATrack 双方向实验复盘 - Design Spec

## I. Project Information
| Item | Value |
| --- | --- |
| Project Name | SEATrack 双方向实验复盘 |
| Canvas Format | ppt169 1280 × 720 |
| Page Count | 12 |
| Primary Language | zh-CN |
| Target Audience | 导师、师兄及课题组成员 |
| Communication Intent | 汇报实现、SS 补救证据和后续实验设计 |
| Desired Audience Outcome | 理解两路线差异并讨论消融顺序 |
| Core Message / Ask / Action | 分线验证；SS 补救尚未证明普遍改善 |
| Delivery Context | 中文组会现场，12–15 分钟 |
| Artifact Afterlife | 方法与计划查阅 |
| Reading Mode | balanced |
| Content Strategy | 基于本地记录；按原理、目的、做法、效果组织，状态标日期，不推断实时进度 |
| Design Style | C 实验复盘：白底浅蓝论文图、问题—调整—证据 |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-11-18 |
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
- **Visual Style Behavior**: 白底浅蓝论文图的实验复盘，细线连接方法步骤，数字与短句强调证据。浅蓝表示主方法、浅金表示另一模态或对照；背景平面区分方法和解释，不用拟物装饰。
- **Theme**: 实验记录的编号、细分隔线与边注
- **Tone**: 审慎、清晰、可讨论
### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | 画布 |
| Secondary background | #EDF5FA | 分区 |
| Primary | #202629 | 标题 |
| Accent | #4A8FBD | SS |
| Secondary accent | #BC8E53 | 频域与待验证 |
| Body text | #3036312 | 正文 |
| Secondary text | #626C70 | 注释 |
| Divider | #B9D4E5 | 分隔 |

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

| ss_results.png | 3840 × 1440 | 8:3 | Python实测数据图 | Chart | 完整展示 | no-crop | user | Existing | 本地实验数据，经Python绘制 | preserve | evidence |
| ab_results.png | 3840 × 1440 | 8:3 | Python实测数据图 | Chart | 完整展示 | no-crop | user | Existing | 本地实验数据，经Python绘制 | preserve | evidence |
| dynamics.png | 3840 × 1440 | 8:3 | Python实测数据图 | Chart | 完整展示 | no-crop | user | Existing | 本地实验数据，经Python绘制 | preserve | evidence |
| frequency_results.png | 3840 × 1440 | 8:3 | Python实测数据图 | Chart | 完整展示 | no-crop | user | Existing | 本地实验数据，经Python绘制 | preserve | evidence |

## IX. Content Outline
### Part 1: 实验与证据
#### Slide 01 - SS、补救与频段融合：实验复盘
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: SS、补救与频段融合：实验复盘
- **Core message**: 三条想法，两类干预：训练约束与预测融合；重点检验有效性。
- **Content**: 三条想法，两类干预：训练约束与预测融合；重点检验有效性。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 02 - SS 如何实现：对齐空间关系
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: order：输入、干预、输出；contrast：对照与实验。
- **Title**: SS 如何实现：对齐空间关系
- **Core message**: 两路区域特征归一化、pairwise矩阵、MSE、五层平均；原理图。
- **Content**: 两路区域特征归一化、pairwise矩阵、MSE、五层平均；原理图。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 03 - SS 没有带来普遍提升
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: SS 没有带来普遍提升
- **Core message**: 四个百分比指标差值图；VOT2022 EAO独立列出；RGB-D/E历史基线可比性边界。
- **Content**: 四个百分比指标差值图；VOT2022 EAO独立列出；RGB-D/E历史基线可比性边界。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。
- **Visualization**: result-plot=prepared Python scientific figure; data retained in figures/plot_results.py.
- **Native-ready**: result-plot=no (PNG embedded; editable SVG/PDF/source supplied).

#### Slide 04 - 搜索框交换：偏移与目标选择都有影响
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: order：输入、干预、输出；contrast：对照与实验。
- **Title**: 搜索框交换：偏移与目标选择都有影响
- **Core message**: 逐序列诊断；2模型×3前框来源；固定首帧模板、当前帧，独立回放；关键帧和16帧平均。
- **Content**: 逐序列诊断；2模型×3前框来源；固定首帧模板、当前帧，独立回放；关键帧和16帧平均。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 05 - 补救的三个切口：区域、目标、层
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: order：输入、干预、输出；contrast：对照与实验。
- **Title**: 补救的三个切口：区域、目标、层
- **Core message**: template-only、target-aware、search-only图示；半权重与逐层的目的和状态。
- **Content**: template-only、target-aware、search-only图示；半权重与逐层的目的和状态。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 06 - A/B 恢复部分 LasHeR 性能，但仍低于基线
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: A/B 恢复部分 LasHeR 性能，但仍低于基线
- **Core message**: 60轮重训，完整协议与五指标表；两个数据集点图；失败序列复查。
- **Content**: 60轮重训，完整协议与五指标表；两个数据集点图；失败序列复查。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。
- **Visualization**: result-plot=prepared Python scientific figure; data retained in figures/plot_results.py.
- **Native-ready**: result-plot=no (PNG embedded; editable SVG/PDF/source supplied).

#### Slide 07 - Search-only 已训练完成：收敛不等于有效
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: Search-only 已训练完成：收敛不等于有效
- **Core message**: 60轮训练；SS与IoU曲线；末轮数据；更新次数差异与梯度缺失。
- **Content**: 60轮训练；SS与IoU曲线；末轮数据；更新次数差异与梯度缺失。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。
- **Visualization**: result-plot=prepared Python scientific figure; data retained in figures/plot_results.py.
- **Native-ready**: result-plot=no (PNG embedded; editable SVG/PDF/source supplied).

#### Slide 08 - 固定频段融合：用相同规则检验互补性
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: order：输入、干预、输出；contrast：对照与实验。
- **Title**: 固定频段融合：用相同规则检验互补性
- **Core message**: 两模态末层搜索特征→FFT→硬掩膜→逆变换→原头；2失败窗+6稳定窗，RMS对照。
- **Content**: 两模态末层搜索特征→FFT→硬掩膜→逆变换→原头；2失败窗+6稳定窗，RMS对照。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 09 - 固定融合救回白车，却损害稳定片段
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: 固定融合救回白车，却损害稳定片段
- **Core message**: 五种方案三类样本柱图；基线权重对照；失败窗口均值；不支持固定分工。
- **Content**: 五种方案三类样本柱图；基线权重对照；失败窗口均值；不支持固定分工。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。
- **Visualization**: result-plot=prepared Python scientific figure; data retained in figures/plot_results.py.
- **Native-ready**: result-plot=no (PNG embedded; editable SVG/PDF/source supplied).

#### Slide 10 - 决策图融合：只学习两个全局频段权重
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: order：输入、干预、输出；contrast：对照与实验。
- **Title**: 决策图融合：只学习两个全局频段权重
- **Core message**: 冻结SS模型；两路分类logits→FFT→低高权重→逆变换→解码；训练验证拆分。
- **Content**: 冻结SS模型；两路分类logits→FFT→低高权重→逆变换→解码；训练验证拆分。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 11 - 分类损失改善，尚未变成整段跟踪收益
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: 分类损失改善，尚未变成整段跟踪收益
- **Core message**: 四方案CE表，2序列闭环关键帧IoU及整段SR；白车单帧与整段矛盾。
- **Content**: 四方案CE表，2序列闭环关键帧IoU及整段SR；白车单帧与整段矛盾。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

#### Slide 12 - 当前结论与下一步验证
- **Audience move**: 理解本页证据及其推论边界。
- **Relationships**: contrast：假设与实验结果。
- **Title**: 当前结论与下一步验证
- **Core message**: 三想法分别目的、已做、结论、下一步；区分未完成全量评测的工作。
- **Content**: 三想法分别目的、已做、结论、下一步；区分未完成全量评测的工作。
- **Composition**: 原理用可编辑节点与连线；实验用图表与目的、做法、效果说明。

## X. Speaker Notes Requirements
- **Generation**: enabled
- **Filename**: match SVG stems
- **Content**: 说明每页目的、做法、效果与证据边界。
- **Total duration**: 12–15分钟

## Reference-style revision 2026-11-19
用户授权参考照片风格：上方主流程，下方局部机制面板；特征堆叠、关系矩阵、前景掩膜、频域掩膜用可编辑SVG。白底、浅蓝、蓝色箭头、虚线分区；不复制参考中的SAM方法。P02/05/08/10重新组织视觉，所有实验数据保持。数学使用普通文本，不新增复杂公式渲染。示意矩阵和掩膜均明确注明非实测。
