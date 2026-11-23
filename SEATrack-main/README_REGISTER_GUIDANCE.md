# 11.18：寄存器 token 与 Register Guidance

## 目的与实现边界

在无 SS、无频域融合的 SEATrack 基线上，独立验证寄存器能否改善特征与跟踪表现。
参考本地 `2611.18549v1.pdf`（JVT，§3.3，式 3–4、附录 A）：可学习寄存器在中间层插入，训练时始终保留；推理时用同一模型的有／无寄存器输出作外推。论文操作的是扩散速度，**本实现是面向跟踪的特征层适配，不是原论文扩散采样的复现**。

## 怎么做

- 默认第 9 个 block 输入处插入（从 0 编号，即前 9 层之后），两模态共享一组 4×768 可学习初始寄存器，随后分别演化；新增 3072 个参数。正态初始化标准差 0.02，不加位置、类别或时间条件。
- token 顺序是 `[template; search; registers]`。末尾插入便于保留既有空间索引；寄存器参与余下各层 self-attention、AMG 和逐 token MLP，不进入模板／搜索 HMoE 分组。
- 最后 LayerNorm 前移除寄存器，搜索输出仍为 `[B,256,768]`。保留原 RGB＋IR 融合及 CENTER 预测头。
- PEFT 训练保留原 `moe/scaling/lora` 参数，并加入 `register_tokens`；损失仍是跟踪损失，SS 权重为 0。
- 推理时 `F_rg = F_reg + w * (F_reg - F_no_reg)`，之后只运行一次预测头。`F_no_reg` 来自相同输入、相同训练后权重，真正移除寄存器；它不是独立训练的原始基线。`w=0` 只执行有寄存器的一次骨干前向，`w>0` 执行两次。训练始终只前向一次；不做 register dropout。
- 限定 direct 拼接、无 CLS／segment、CE_KEEP_RATIO=1；与 SS、频域融合组合会报错。禁止使用带 padding mask 的底层寄存器前向，避免沿用未实现的 mask 行为。
- `Register/register_norm` 与 `Register/patch_norm` 记录最后一层、LayerNorm 前的平均 L2 范数。高范数、空间平滑和精度收益均是待验证假设，不通过人为放大初始化实现。

4 个 token 与特征层指导是本实验选择，论文视频设置采用 32 个 token。`INSERT_LAYER`、`NUM_TOKENS` 可配置；应通过验证集确定，不能宣称已优化。

## 配置与运行

| 配置 | 用途 | 指导系数 |
|---|---|---|
| `rgbt` | 独立原始基线训练／评测 | 无寄存器 |
| `rgbt_register` | 寄存器训练、无 RG 评测 | 0 |
| `rgbt_register_guidance` | **同一寄存器 checkpoint** 的 RG 评测 | 1（起始值，未调优） |

从 `SEATrack-main` 运行现有训练入口：

```bash
python tracking/train.py --script seatrack --config rgbt_register --save_dir /absolute/new/register_run --mode single
```

默认继承 `rgbt.yaml` 的 OSTrack 初始化文件、LasHeR 数据和 60 轮设置；运行前配置已有环境中的数据与权重路径。不得把 SS checkpoint 当作无 SS 初始化。公平比较应使用相同初始化、采样量、优化器、随机种子及评测协议。先查共享 GPU 占用，再在服务器独立代码快照中启动；2026-11-23 已按后续指令在独立服务器快照启动训练，入口见 `../server_setup/register_20261123/README.md`。

评测通过 `lib.test.parameter.seatrack.parameters('rgbt_register')` 或 `parameters('rgbt_register_guidance')` 接入现有 Tracker，均要求：

```bash
export SEATRACK_CHECKPOINT=/absolute/register_run/checkpoints/.../SEATrack_ep0060.pth.tar
```

使用训练完成的寄存器权重，Tracker 严格加载，旧基线权重缺少寄存器参数会拒绝。两配置共享 checkpoint，仅指导系数不同；参数入口将任务映射为 `rgbt`，保留原 RGB-T LoRA 合并权重加载约定。仓库旧 `RGBT_workspace/test_rgbt_mgpus.py` 含硬编码数据路径，不能直接视作当前服务器的全量评测脚本；部署时按现有同协议评测入口指定配置和独立输出目录。

验证集可先比较 w=0、0.5、1.0，再固定系数进行全量测试。报告独立基线／寄存器／寄存器+RG 三组 SR/MSR 和推理耗时；不要只比较有／无寄存器的同权重两次前向。

## 本地验证与待办

```bash
python -m unittest discover -s tests -p 'test_register_guidance.py'
```

2026-11-23 本地验证：20 项测试全部通过（寄存器 5 项、频域 6 项、SS 9 项）；另与修改前 HEAD 的注意力 block 对照，两模态在关闭寄存器时逐值一致。8 个修改的 Python 文件语法检查通过；保留原 CRLF 文件行尾，`git -c core.whitespace=cr-at-eol diff --check` 通过。

测试覆盖移除寄存器与基线一致性、输出尺寸、权重往返、指导公式、训练／推理前向次数、真实优化器参数及梯度更新、HMoE 排除寄存器、配置和 checkpoint 路由、非法配置保护。另运行原 SS／频域测试检查回归。

本地测试环境为临时虚拟环境（Python 3.9、PyTorch 2.8.0、timm 0.6.13）；评测模块导入还需项目原有的 easydict、tensorboardX、lmdb、jpeg4py、pandas、pycocotools 等依赖。没有修改服务器环境。

2026-11-23 服务器 OSTrack 初始化加载及 CUDA 小批训练／验证已通过，正式60轮训练运行中。全量跟踪评测仍待做。本地随机输入测试不能证明性能提升；范数均值也不足以证明 patch 更平滑，后续还需固定样本特征图与空间差分诊断。
