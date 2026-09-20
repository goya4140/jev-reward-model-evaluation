# Jev Reward Model Evaluation — Phase 2 Plan

日期：2026-09-20

目标模型：`jev-1.13.0`（执行时再次固定并记录返回版本）

## 1. 第二阶段目标

第二阶段不再重复第一阶段的通用 pairwise 测试，而是补齐三种能力：

1. **过程奖励能力**：能否定位推理链的第一个错误，并对每一步给出有效性/冗余判断。
2. **真实部署形态的奖励能力**：独立给候选打分后进行 Pairwise 与 Best-of-N 选择，而不仅是把全部候选同时交给 Judge。
3. **可验证正确性与过度优化**：随着候选数量 K 增大，Jev 选出的答案是否真的更正确，还是出现 reward hacking / over-optimization。

## 2. Benchmark 范围

| Benchmark | 本轮状态 | 规模 | 主要能力 | 主指标 |
|---|---|---:|---|---|
| ProcessBench | 新增 | 3,400 traces | 首个错误步骤定位 | 四子集平均 F1 |
| PRMBench | 新增 | 6,216 problems / 83,456 step labels | 细粒度过程错误检测 | 官方 PRMScore、negative F1 |
| RMB | 新增 | 17,131 pairwise groups + 3,786 BoN groups，49 个数据文件 | 跨场景偏好与 Best-of-N | Pairwise accuracy、BoN top-1 |
| RM-Bench（THU-KEG） | 正式纳入；新增独立 RM 评分协议 | 1,327 prompts / 7,962 responses / 11,943 pairs | subtlety 与 style bias | 官方 Overall、Hard / Normal / Easy |
| PPE correctness suites | 新增 | 2,555 prompts / 81,760 responses | Best-of-K、可验证正确性、过度优化 | Max performance、loss、end score、ROC AUC |

PPE 待补的五个子集：

- `mmlu_pro_best_of_k`：知识与推理
- `math_best_of_k`：数学，使用符号等价正确性标签
- `gpqa_best_of_k`：高难 STEM
- `ifeval_best_of_k`：可验证指令遵循
- `mbpp_plus_best_of_k`：代码与测试用例正确性

## 3. 统一的两种 Jev 模式

为避免把 LLM Judge 能力误当作可部署的 scalar RM 能力，本轮明确区分：

### A. Jev-RM（主结果）

- 每个候选独立评分，不让模型看到其他候选。
- 使用固定、预先声明的 5 级质量或正确性标尺。
- 用同一分数执行 Pairwise、Best-of-N 和 Best-of-K。
- 平分时使用固定规则处理，并单独报告 tie rate。

### B. Jev-Judge（诊断结果）

- 同时看到多个候选并直接选择最佳项。
- 只用于衡量比较上下文带来的增益。
- 不与独立标量 RM 的 leaderboard 分数混为一谈。

最终报告将同时给出两者，并报告 `Judge - RM` 的差值。若差值很大，说明 Jev 更适合在线 Judge，而非可缓存的独立 reward scorer。

## 4. 各 Benchmark 协议

### 4.1 ProcessBench

数据包含 GSM8K 400、MATH 1,000、OlympiadBench 1,000、Omni-MATH 1,000，共 3,400 条。标签是首个错误步骤索引；完全正确的推理链标记为 `CLEAN/-1`。

主协议：

- 输入仅包含题目和带中性编号的推理步骤。
- Jev 在 `STEP_1 ... STEP_N, CLEAN` 中直接选择首个错误位置。
- 不提供最终答案正确性、生成模型、标签或错误解释。
- 主指标严格复刻官方：`error_acc`、`correct_acc`，以及二者调和平均 F1；分别报告四个子集和 macro average。

补充诊断：

- 首错位置绝对距离。
- `±1 step` 命中率。
- false alarm rate 与 missed-error rate。
- 按步骤长度、错误位置和题目难度分层。

### 4.2 PRMBench

每个问题一次请求，Jev 对每一步分别输出：

- `validity`：有效 / 无效及概率。
- `redundancy`：必要 / 冗余及概率。

严格排除 `modified_steps`、`error_steps`、`reason`、类别答案等泄漏字段。使用官方实现计算：

- overall F1 与 negative F1。
- 官方 PRMScore。
- Simplicity、Soundness、Sensitivity 三大类宏平均。
- NR、NCL、ES、SC、DC、CI、PS、DR、MS 九个子类。
- 正负类召回率、误报率，以及错误步骤位置分层。

阈值不得在完整测试集上调优。主结果使用固定语义阈值；另给一份明确标记为“calibrated diagnostic”的留出校准结果，不与官方主结果混合。

官方项目同时发布了覆盖物理、化学和生物的 PRMBench-STEM。它作为扩展轨单独运行、单独报告，不与主 PRMBench 数学集合混算；先核验其完整数据和官方 scorer 可公开复现，再进入 full run。

### 4.3 RMB

RMB 与 RM-Bench 是两个不同数据集。本轮测试 RMB 的 helpfulness / harmlessness、49 个细粒度场景、Pairwise 与 BoN 两种设置。

Pairwise：

- Jev-RM：两个回答分别独立评分，再比较标量。
- Jev-Judge：随机化 A/B 后直接选择。
- 报告 micro accuracy、49 场景 macro、helpfulness / harmlessness macro、order consistency。

Best-of-N：

- Jev-RM：逐候选独立评分并取最大值，作为主结果。
- Jev-Judge：一次性 listwise 选择，作为诊断。
- 报告 top-1 accuracy、随 N 的曲线、MRR、winner rank、场景宏平均。

### 4.4 RM-Bench

本项固定指向 `THU-KEG/RM-Bench`，即 ICLR 2025 Oral 的 **RM-Bench: Benchmarking Reward Models of Language Models with Subtlety and Style**。每个 prompt 包含三种风格的 chosen response 和三种风格的 rejected response，构成 3×3 Style–Substance Matrix。

主协议采用官方 scalar RM 语义，而不是直接让模型做九次二选一：

- **Jev-RM 主结果**：六个 response 分别独立评分，每个 response 只看到 prompt 和自身内容；随后离线比较三个 chosen 分数与三个 rejected 分数，重建 3×3 矩阵。
- 每个 response 在正式运行中只评分一次，同一分数复用于九个 pair，避免比较上下文和重复调用造成的漂移。
- **Jev-Judge 诊断结果**：对九个 pair 直接做中性命名的二选一。第一阶段经官方聚合口径复核为 81.29%，属于这一协议，可作为历史基线；本轮不把它冒充独立 scalar RM 成绩。

主指标严格跟随官方：

- Hard：简洁 chosen 对比风格更华丽的 rejected。
- Normal：chosen 与 rejected 风格匹配。
- Easy：风格更华丽的 chosen 对比更简洁的 rejected。
- Chat、Code、Math、Safety 四领域分数；Safety 由 safety-refuse 与 safety-response 汇总。
- `Overall = (Chat + Code + Math + Safety) / 4`，同时报告 Hard / Normal / Easy 的四领域等权宏平均。
- 额外报告 3×3 矩阵、style gap、五个原始 domain、RM/Judge 差值和概率校准。

因此，本轮确实需要对该官方数据集执行一套新的全量 **独立奖励评分**；已有结果只用于 Judge 对照和回归审计。

### 4.5 PPE correctness / Best-of-K

对五个数据集中的每个 response 生成独立正确性 reward。数据集自带的 correctness 标签只在服务端评分阶段使用，不进入 Jev state。

主指标：

- response-level ROC AUC 与正/负类分数分布。
- pairwise correctness accuracy。
- Best-of-K curve，K = 1, 2, 4, 8, 16, 32。
- Maximum Achieved Performance。
- End Score at K=32。
- PPE 官方 loss。
- over-optimization gap：`max performance - end score`。

五个子集分别报告，最后做等权宏平均，避免某一领域支配总分。

## 5. 先导实验与执行门槛

在全量调用前先运行 pilot：

| 数据集 | Pilot 规模 | 必须通过的检查 |
|---|---:|---|
| ProcessBench | 200 | 标签解析 100%；顺序交换不适用；首错选项覆盖正常 |
| PRMBench | 200 | 所有步骤均有输出；无字段泄漏；正负预测不塌缩 |
| RMB | 300 pairwise + 100 BoN | A/B 交换一致率 ≥95%；RM/Judge 均可解析 |
| PPE | 每个子集 50 prompts | 单候选与小批评分 Spearman ≥0.99，Best-of-K 选择一致率 ≥99% |
| RM-Bench（THU-KEG） | 200 | 六回答独立评分无塌缩；单条与安全批处理 Spearman ≥0.99；九 pair 可完整重建 |

PPE 若通过批处理等价性检查，可把每 4–8 个候选放入一次 API 请求、仍分别评分，以显著减少请求数；不通过则使用严格单候选调用。

## 6. 防泄漏与稳定性审计

- 候选和步骤只使用中性 ID；不得出现 `chosen/rejected/correct/error` 等标签化名称。
- 数据标签、验证器结果、错误解释和 source model 不发送给 Jev。
- Pairwise 至少 10% 样本做 A/B 翻转审计。
- ProcessBench 至少 10% 样本做无关步骤编号格式变换。
- PRMBench 至少 10% 样本做等价编号/排版扰动。
- 每类抽样 100 条重复三次，报告重复一致率。
- 固定数据快照、提示模板 hash、模型返回版本、代码 commit 和随机种子。
- 每条记录保存概率、分数、token、延迟、重试次数和解析状态。

## 7. 执行顺序

1. 数据快照与 loader 审计。
2. ProcessBench adapter + pilot + full run。
3. PRMBench adapter + pilot + full run。
4. RMB Pairwise/BoN adapter + pilot + full run。
5. THU-KEG RM-Bench 独立评分 adapter + pilot + full run，并与第一阶段 Judge 结果对照。
6. PPE 五个 correctness suites pilot；决定严格单候选或安全批处理。
7. PPE full run。
8. 合并第一、二阶段结果，生成总报告和逐样本审计清单。

## 8. 预算控制

第二阶段最大成本来自 PPE 的 81,760 个候选以及 PRMBench 的长推理链。正式全量前根据 pilot 的真实 token 用量生成预算，不以拍脑袋估算直接开跑。

设置三个自动停止门：

- 任何 benchmark API 错误率超过 1%，暂停并诊断。
- 实际 token/样本超过 pilot 估计的 1.5 倍，暂停并重新估算。
- 模型返回版本不再是固定版本，立即暂停，禁止混合版本结果。

预算报告区分：有效正式运行成本、pilot 成本、废弃审计重跑成本。

## 9. 最终交付

- 第二阶段完整中文报告。
- 每个 benchmark 的官方主指标与诊断指标。
- Jev-RM vs Jev-Judge 对照表。
- Best-of-K 曲线与 over-optimization 分析。
- 过程错误类型热力图和弱项清单。
- 逐样本 JSONL、机器可读 summary、失败/重试审计。
- 第一、二阶段统一结论：适合的 RM 场景、不适合的场景，以及上线前需要的校准与组合验证器。

## 10. 官方来源

- ProcessBench: https://github.com/QwenLM/ProcessBench
- PRMBench: https://github.com/ssmisya/PRMBench
- RMB: https://github.com/Zhou-Zoey/RMB-Reward-Model-Benchmark
- RM-Bench: https://github.com/THU-KEG/RM-Bench
- PPE: https://github.com/lmarena/PPE
