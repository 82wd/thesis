# Design Specification

## Communication
中文研究组会，16:9，约 10 分钟。受众为导师和组内同学。使用自由排版，以数据表、真实关键帧和交叉回放为证据。


## IX. Content Outline

#### Slide 01 - SEATrack 加入 SS 后，为什么会掉分？

- **Audience move**: 用十分钟回答三个问题：增益出现在哪里，下降由哪些序列贡献，以及控制上一帧搜索位置以后，模型表现如何变化。
- **Relationships**: none

#### Slide 02 - SS 约束两种模态对空间结构的描述

- **Audience move**: 辅助模态依次是热红外、事件和深度。
- **Relationships**: none

#### Slide 03 - 同轮比较中，只有 RGBT234 的指标提高

- **Audience move**: VOT22 的 EAO 原始值由 0.73760 降到 0.72659。
- **Relationships**: none

#### Slide 04 - 少数大幅退步的序列可以拉低总体均值

- **Audience move**: LasHeR 的改善和下降条数一样，退步序列的幅度更大。
- **Relationships**: none

#### Slide 05 - 白车第 23 帧：搜索框的位置改变了预测

- **Audience move**: SS 框移到了目标左上方另一辆白车。
- **Relationships**: none

#### Slide 06 - 足球第 63 帧：同一搜索区域也会选错人

- **Audience move**: 足球场里有多个相近的球员。
- **Relationships**: none

#### Slide 07 - 一个易拉罐序列贡献了约 47% 的平均 IoU 降幅

- **Audience move**: 这项补充分析解释了下降的集中程度。
- **Relationships**: none

#### Slide 08 - 固定搜索区域后，持续失分明显缩小

- **Audience move**: 交换的是上一帧框的位置和大小。
- **Relationships**: none

#### Slide 09 - SS 是否更容易受搜索偏移和相似目标干扰？

- **Audience move**: 当前已确认一次错误能经搜索位置传播，也观察到同一区域内两份权重作出不同预测。
- **Relationships**: none