# 在已有单卡训练代码上准备 pairwise SS 实验

此包由用户上传并执行；不会连接服务器，不会启动训练，也不会调用旧训练队列。

## 包含内容

- `prepare.py`：检查源代码兼容性，创建独立实验副本，接入 SS。
- `reference/`：本地历史源码，用于语法结构比对。服务器源码若存在未知改动，拒绝覆盖。
- `payload/`：本次 SS 模块、模型/Actor/配置接入、PatchEmbed 修复、测试和说明。
- `package_manifest.json`：上传内容 SHA-256，用于检查传输完整性。
- `LOCAL_VALIDATION.txt`：本地安装流程验证结果，不是服务器训练结果。

## 服务器准备命令

```bash
/nas/liziyan103/anaconda3/envs/seatrack/bin/python \
  /nas/liziyan103/seatrack/pairwise_ss_20261103/prepare.py
```

默认源：`/nas/liziyan103/seatrack/training_runs/20261011_remaining/code_single`。

新实验：`/nas/liziyan103/seatrack/training_runs/20261103_pairwise_ss`。

仅复制 lib、experiments、tracking；数据和权重继续使用已验证路径。保留梯度累积、LasHeR 帧名匹配修复、原优化器和训练器。TensorBoard 指向新目录。输出目录已经存在时拒绝覆盖；遇到未知代码差异时停止并报告文件名，请回传错误分析，不使用强制覆盖绕过。

成功输出 `PREPARE_OK` 后：

```bash
cd /nas/liziyan103/seatrack/training_runs/20261103_pairwise_ss/code
/nas/liziyan103/anaconda3/envs/seatrack/bin/python \
  -m unittest discover -s tests -p test_semantic_alignment.py -v
```

该测试不使用 GPU、不读取真实数据或初始化权重。需要先完成这一步，再进行 GPU 试跑。

## 生成的配置

| 配置名 | 用途 |
| --- | --- |
| rgbt_ss_smoke | 1 轮、128 个训练样本、每批 4、累积 16，共 32 个训练微批/2 次更新；16 个验证样本、4 个验证批次；0 个数据加载子进程；每 16 微批打印。 |
| rgbt_ss | 正式 SS 实验；沿用已完成基线的 60 轮、59968 训练样本/轮、batch4×累积16、FP32、LR0.0004、原保存频率。 |
| rgbt_ss_baseline | 与正式 SS 配置仅 ENABLED 不同，供同条件基线对照。 |

三个配置必须使用不同且初始为空的保存目录。试跑权重不能直接当作正式实验的恢复点。`rgbd_ss` / `rgbe_ss` 配置随包提供仅供现有单元测试读取；本包只准备 RGB-T 训练，不意味着其他数据路径已验证。

## 验证边界

本地根据历史 configure.py / configure_single.py 重建训练副本后测试安装：原代码逐文件哈希不变，梯度累积和数据加载器等文件逐字保留，安装后 8 项 CPU 测试通过；已存在的实验目录及未知源码改动均被拒绝。夹具使用占位权重文件，仅验证路径检查，不冒充模型加载或真实训练。

服务器 PyTorch 2.2.2 的测试和真实 GPU 训练尚待用户执行。安装过程会写入新目录的 `setup.log` 与 `setup_manifest.json`，记录北京时间、源目录、操作目的和文件哈希。

## 2026-11-03 兼容性修正

prepare.py 额外识别用户确认的 PatchEmbed 版本：`self.flatten = flatten` 位于 `self.num_patches` 之后。仅接受这一具体等价排列，并逐字保留已修复文件；其他行为差异继续拒绝。原版及该版本均通过本地安装测试，详见 `PATCH_EMBED_VALIDATION.txt`。如果已上传此前的包，只更新 prepare.py 即可；payload 和其校验清单没有变化。

## 只读进度面板（2026-11-04）

新增 `progress.py`，仅用 Python 标准库，每10秒刷新。默认展示GPU1，训练会话名称按用户确认为1；该名称仅用于显示和返回指引，不执行tmux控制。面板读取train.log、exitcode.txt和权重文件名，不导入PyTorch、不加载权重、不启动或停止训练、不修改实验文件。

上传单个文件后，在独立ss_progress会话运行：

```bash
/nas/liziyan103/anaconda3/envs/seatrack/bin/python /nas/liziyan103/seatrack/pairwise_ss_20261103/progress.py --session 1
```

默认自动选择唯一的full_*目录并固定读取它；忽略smoke目录。多个正式目录时会列出路径，需添加 `--run-dir /完整/full_目录`；不会悄悄切换实验。`--once`只显示一次，`--interval 10`设置刷新间隔，`--gpu -1`关闭GPU查询。

内容：当前训练/验证阶段、轮次、本轮和总体训练百分比、推算参数更新次数、总损失/IoU/SS及其分项、速度、剩余训练阶段时间估算、checkpoint非空文件数、日志新鲜度、整卡显存/利用率和错误尾部。ETA不包含后续验证/保存/停顿，日志超过10分钟未更新时暂停显示ETA；日志安静不自动判定训练进程已死。到100%仅表示训练批次进度；退出码0、Finished training和末轮非空权重文件齐全才标完成，不等价于已校验权重内容或评测质量。

本地7项测试通过，覆盖日志解析、阶段与指标、100%但未完成、退出失败和非有限数值、读操作不改文件、实验目录歧义、GPU查询超时、配置轮数及初始化等待。Python3.8语法检查通过。尚未在服务器运行，进度和GPU实时状态待用户查看。
