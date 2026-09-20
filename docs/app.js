const COLORS = {
  ink: "#111827",
  muted: "#718096",
  line: "#d9e1ea",
  nightLine: "#26364a",
  blue: "#4c9fff",
  blueStrong: "#2369dc",
  gold: "#e4ad3a",
  cyan: "#52d3d8",
  white: "#eef6ff",
};

const difficultyData = {
  labels: ["Easy", "Normal", "Hard"],
  structured: [87.82, 83.92, 76.84],
  pointwise: [82.90, 84.89, 83.57],
};

const benchmarkData = [
  {
    name: "RewardBench v1",
    jev: 92.58,
    metric: "官方四分区宏平均",
    note: "Jev 距冻结榜首 2.53 pp，且与最佳 generative reference 仅差 0.90 pp。",
    baselines: [["INF-ORM-Llama3.1-70B", 95.11], ["Llama-3.1-Nemotron-70B", 94.11], ["TextEval-Llama3.1-70B", 93.48]],
  },
  {
    name: "RewardBench 2",
    jev: 81.15,
    metric: "官方六领域宏平均",
    note: "Jev 高于 Gemini-2.5-Pro 1.65 pp，距离榜首 Skywork 2.95 pp。",
    baselines: [["Skywork-Reward-V2-8B", 84.10], ["LMUnit-Qwen2.5-72B", 82.10], ["Gemini-2.5-Pro", 79.50]],
  },
  {
    name: "RM-Bench · structured pairwise",
    jev: 81.29,
    metric: "官方四领域宏平均",
    note: "结构化直接比较超过 GPT-4.1 3.89 pp；相对完整领域 DeepSeek R1 低 4.01 pp，榜首 96.0 仅报告 Overall。",
    baselines: [["Skywork-Reward-V2-8B-40M*", 96.00], ["DeepSeek R1", 85.30], ["Nemotron-49B GenRM", 84.20]],
  },
  {
    name: "RubricBench · human rubric",
    jev: 76.02,
    metric: "Pairwise accuracy",
    note: "Jev 使用 benchmark 的 human rubric，但未复刻论文 Oracle pipeline；对比值仅作协议邻近参考。",
    baselines: [["OpenRubric + Gemini Oracle", 85.30], ["CheckEval + Gemini Oracle", 80.60], ["OpenRubric + Gemini Self-gen", 58.10]],
  },
  {
    name: "PPE · Human Preference V1",
    jev: 64.40,
    metric: "去平局逐样本准确率",
    note: "Jev 与 Athene-RM-8B 只差 0.19 pp；其模型级 Spearman 反而高出 2.10。",
    baselines: [["Ensemble Judges", 68.59], ["Athene-RM-70B", 66.56], ["Athene-RM-8B", 64.59]],
  },
  {
    name: "ProcessBench",
    jev: 69.51,
    metric: "官方 mean F1",
    note: "Jev 超过原论文 GPT-4o 7.61 pp，接近 QwQ-32B，但与 o1-mini 尚有明显距离。",
    baselines: [["o1-mini", 87.90], ["QwQ-32B-Preview", 71.50], ["GPT-4o-0806", 61.90]],
  },
  {
    name: "PRMBench Preview",
    jev: 66.38,
    metric: "官方 PRM score",
    note: "Jev 与 GPT-4o 仅差 0.42 pp，距离最佳模型结果 2.42 pp。",
    baselines: [["Gemini-2.0-thinking", 68.80], ["o1-mini", 68.80], ["GPT-4o", 66.80]],
  },
  {
    name: "RM-Bench · pointwise",
    jev: 83.79,
    metric: "官方四领域宏平均",
    note: "Pointwise Jev 超过 Qwen-3-Nemotron-32B 1.89 pp；距完整领域 REWARDANYTHING 2.61 pp，距仅 Overall 榜首 12.21 pp。",
    baselines: [["Skywork-Reward-V2-8B-40M*", 96.00], ["REWARDANYTHING-8B", 86.40], ["Qwen-3-Nemotron-32B", 81.90]],
  },
];

const sotaData = [
  {
    name: "RewardBench v1",
    metric: "官方四分区宏平均",
    snapshot: "Frozen official leaderboard",
    sourceLabel: "官方冻结榜 ↗",
    sourceUrl: "https://huggingface.co/spaces/allenai/reward-bench",
    protocol: "榜单已冻结；模型可能受公开评测集污染影响。",
    jevEdge: "Reasoning 97.48%，接近头部模型；以 API generative judge 身份达到 92.58%。",
    sotaEdge: "序列分类器仍占据榜首，INF-ORM 领先 Jev 2.53 pp；Chat Hard 是 Jev 的主要差距来源。",
    rows: [
      ["INF-ORM-Llama3.1-70B", 95.11, "Seq. classifier", "sota"],
      ["LDL-Reward-Gemma-2-27B-v0.1", 94.99, "Seq. classifier", "reference"],
      ["QRM-Gemma-2-27B", 94.44, "Seq. classifier", "reference"],
      ["Skywork-Reward-Gemma-2-27B-v0.2", 94.26, "Seq. classifier", "reference"],
      ["Llama-3.1-Nemotron-70B-Reward", 94.11, "Custom classifier", "reference"],
      ["TextEval-Llama3.1-70B", 93.48, "Generative", "reference"],
      ["Jev 1.13", 92.58, "Generative API judge", "jev"],
    ],
  },
  {
    name: "RewardBench 2",
    metric: "官方六领域宏平均",
    snapshot: "Official snapshot · 2025-12",
    sourceLabel: "官方结果集 ↗",
    sourceUrl: "https://huggingface.co/collections/allenai/reward-bench-2",
    protocol: "包含 ties 与多候选任务；不能与 RewardBench v1 分数混排。",
    jevEdge: "81.15% 位于所列模型第 3，超过 LMUnit-Llama、PGRM、Gemini-2.5-Pro。Safety 95.33%、Ties 94.04%。",
    sotaEdge: "Skywork 8B 领先 2.95 pp；Jev 的 Precise IF 仅 50.63%，显著拖累总分。",
    rows: [
      ["Skywork-Reward-V2-Llama-3.1-8B", 84.10, "Seq. classifier", "sota"],
      ["LMUnit-Qwen2.5-72B", 82.10, "Generative", "reference"],
      ["Jev 1.13", 81.15, "Generative API judge", "jev"],
      ["LMUnit-Llama3.1-70B", 80.50, "Generative", "reference"],
      ["PGRM", 80.00, "Seq. classifier", "reference"],
      ["Gemini-2.5-Pro", 79.50, "Generative", "reference"],
      ["Skywork-Reward-V2-Qwen3-8B", 78.40, "Seq. classifier", "reference"],
    ],
  },
  {
    name: "RM-Bench · structured pairwise",
    metric: "官方四领域宏平均",
    snapshot: "Public leaderboard · 2026-07",
    sourceLabel: "官方公开榜 ↗",
    sourceUrl: "https://github.com/THU-KEG/RM-Bench-Leaderboard",
    protocol: "Jev 一次输出 3×3 pairwise 矩阵。带 * 的结果仅报告 Overall，缺少完整领域列。",
    jevEdge: "81.29% 超过 GPT-4.1 的完整领域结果 3.89 pp；Safety 与 Easy 任务稳健。",
    sotaEdge: "与最高完整领域结果 DeepSeek R1 相差 4.01 pp；榜首 Skywork 96.0* 无领域列，不能做完整诊断。",
    rows: [
      ["Skywork-Reward-V2-Llama-3.1-8B-40M*", 96.00, "Scalar RM", "sota"],
      ["Skywork-Reward-V2-Llama-3.1-8B*", 92.80, "Scalar RM", "reference"],
      ["REWARDANYTHING-8B", 86.40, "Reasoning GenRM", "reference"],
      ["Nemotron-49B-GenRM-Multilingual + vote@32", 85.50, "GenRM", "reference"],
      ["DeepSeek R1", 85.30, "Reasoning LLM", "reference"],
      ["Nemotron-49B-GenRM-Multilingual", 84.20, "GenRM", "reference"],
      ["Jev 1.13", 81.29, "Structured pairwise judge", "jev"],
    ],
  },
  {
    name: "RubricBench · human rubric",
    metric: "Pairwise accuracy",
    snapshot: "Paper Table 2 · 2026-03",
    sourceLabel: "论文主表 ↗",
    sourceUrl: "https://arxiv.org/abs/2603.01562",
    protocol: "均使用 human-authored rubric；Jev 未复刻 OpenRubric/TICK/CheckEval 的完整执行 pipeline。",
    jevEdge: "76.02% 明显高于论文中的 self-generated rubric 方法上限 58.1%，SAFE 达 82.50%。",
    sotaEdge: "Oracle pipeline 的 80.6–85.3% 表明执行结构仍能带来 4.58–9.28 pp；CHAT 71.96% 是 Jev 最弱领域。",
    rows: [
      ["OpenRubric + Gemini-3-Flash", 85.30, "Human-rubric oracle", "sota"],
      ["OpenRubric + DeepSeek-v3.2", 84.90, "Human-rubric oracle", "reference"],
      ["TICK + Gemini-3-Flash", 83.00, "Human-rubric oracle", "reference"],
      ["CheckEval + Gemini-3-Flash", 80.60, "Human-rubric oracle", "reference"],
      ["Jev 1.13", 76.02, "Human-rubric direct judge", "jev"],
    ],
  },
  {
    name: "PPE · Human Preference V1",
    metric: "去平局逐样本准确率",
    snapshot: "Paper Table 4 · 2024-10",
    sourceLabel: "论文主表 ↗",
    sourceUrl: "https://arxiv.org/abs/2410.14872",
    protocol: "论文快照，不是实时榜单；† 方法为 LLM-as-a-judge。",
    jevEdge: "64.40% 几乎追平 Athene-RM-8B（−0.19 pp），Spearman 92.63 高于 Athene-RM-8B 的 90.53。",
    sotaEdge: "逐样本准确率距 Ensemble Judges 4.19 pp；Jev 的置信一致率与校准仍弱于集成裁判。",
    rows: [
      ["Ensemble Judges (ArenaHard)†", 68.59, "Judge ensemble", "sota"],
      ["Ensemble Judges (AlpacaEval)†", 68.52, "Judge ensemble", "reference"],
      ["GPT-4o-2024-08-06 (ArenaHard)†", 67.71, "LLM judge", "reference"],
      ["Claude-3.5-Sonnet-20240620 (ArenaHard)†", 67.33, "LLM judge", "reference"],
      ["Athene-RM-70B", 66.56, "Scalar RM", "reference"],
      ["Athene-RM-8B", 64.59, "Scalar RM", "reference"],
      ["Jev 1.13", 64.40, "Generative API judge", "jev"],
    ],
  },
  {
    name: "ProcessBench",
    metric: "四子集 mean F1",
    snapshot: "Paper Table 3 · ACL 2025",
    sourceLabel: "论文主表 ↗",
    sourceUrl: "https://arxiv.org/abs/2412.06559",
    protocol: "论文主表为 2024 年实验快照；开源 critic 使用 8 次采样多数投票。",
    jevEdge: "69.51% 超过 GPT-4o-0806 7.61 pp，并远高于论文最强专用 PRM（56.5%）。",
    sotaEdge: "仍落后 QwQ-32B 1.99 pp、o1-mini 18.39 pp；OlympiadBench 66.01% 暴露高难错误定位不足。",
    rows: [
      ["o1-mini", 87.90, "Proprietary critic", "sota"],
      ["QwQ-32B-Preview", 71.50, "Open critic · vote@8", "reference"],
      ["Jev 1.13", 69.51, "Generative critic", "jev"],
      ["GPT-4o-0806", 61.90, "Proprietary critic", "reference"],
      ["Qwen2.5-72B-Instruct", 61.20, "Open critic · vote@8", "reference"],
      ["Llama-3.3-70B-Instruct", 58.00, "Open critic · vote@8", "reference"],
      ["Qwen2.5-Math-7B-PRM800K", 56.50, "Process reward model", "reference"],
    ],
  },
  {
    name: "PRMBench Preview",
    metric: "官方 PRM score",
    snapshot: "Official leaderboard · accessed 2026-09",
    sourceLabel: "官方榜单 ↗",
    sourceUrl: "https://prmbench.github.io/",
    protocol: "官方 Preview 榜单；Human 83.8% 仅作上界，不纳入模型排名。",
    jevEdge: "66.38% 超过 Gemini-2.0-Flash、Qwen-7B、Pure-PRM 与 Skywork-PRM，并接近 GPT-4o（−0.42 pp）。",
    sotaEdge: "距并列榜首 Gemini-thinking/o1-mini 2.42 pp；错误步骤召回仍弱于正确步骤召回。",
    rows: [
      ["Gemini-2.0-thinking-exp-1219", 68.80, "Proprietary critic", "sota"],
      ["o1-mini", 68.80, "Proprietary critic", "sota"],
      ["Qwen2.5-Math-PRM-72B", 68.20, "Process reward model", "reference"],
      ["GPT-4o", 66.80, "Proprietary critic", "reference"],
      ["Jev 1.13", 66.38, "Generative critic", "jev"],
      ["Gemini-2.0-Flash-exp", 66.00, "Proprietary critic", "reference"],
      ["Qwen2.5-Math-PRM-7B", 65.50, "Process reward model", "reference"],
    ],
  },
  {
    name: "RM-Bench · pointwise",
    metric: "官方四领域宏平均",
    snapshot: "Public leaderboard · 2026-07",
    sourceLabel: "官方公开榜 ↗",
    sourceUrl: "https://github.com/THU-KEG/RM-Bench-Leaderboard",
    protocol: "Jev 对六回答独立打分；榜单模型的推理与投票预算并不统一。* 仅报告 Overall。",
    jevEdge: "83.79% 超过 Qwen-3-Nemotron-32B（81.9%）；Hard 83.57%，难度曲线比 structured pairwise 更平稳。",
    sotaEdge: "距完整领域 REWARDANYTHING-8B 2.61 pp；若采用仅 Overall 的 Skywork 报告值，差距为 12.21 pp。",
    rows: [
      ["Skywork-Reward-V2-Llama-3.1-8B-40M*", 96.00, "Scalar RM", "sota"],
      ["Skywork-Reward-V2-Llama-3.1-8B*", 92.80, "Scalar RM", "reference"],
      ["REWARDANYTHING-8B", 86.40, "Reasoning GenRM", "reference"],
      ["Nemotron-49B-GenRM-Multilingual + vote@32", 85.50, "GenRM", "reference"],
      ["DeepSeek R1", 85.30, "Reasoning LLM", "reference"],
      ["Nemotron-49B-GenRM-Multilingual", 84.20, "GenRM", "reference"],
      ["Jev 1.13", 83.79, "Pointwise scorer", "jev"],
    ],
  },
];

function renderSotaDossiers() {
  const target = document.getElementById("sota-dossiers");
  target.innerHTML = sotaData.map((benchmark, benchmarkIndex) => {
    const sorted = [...benchmark.rows].sort((a, b) => b[1] - a[1]);
    const jevScore = benchmark.rows.find((row) => row[3] === "jev")[1];
    const rows = sorted.map((row, index) => {
      const [model, score, type, status] = row;
      const delta = score - jevScore;
      const deltaText = status === "jev" ? "—" : `${delta > 0 ? "+" : ""}${delta.toFixed(2)}`;
      return `<tr class="${status === "jev" ? "is-jev" : ""} ${status === "sota" ? "is-sota" : ""}">
        <td class="rank-number">${index + 1}</td>
        <td class="model-cell">${model}</td>
        <td class="model-type">${type}</td>
        <td>${score.toFixed(2)}</td>
        <td class="${delta > 0 ? "delta-positive" : "delta-negative"}">${deltaText}</td>
      </tr>`;
    }).join("");
    return `<article class="sota-card" id="sota-${benchmarkIndex + 1}">
      <header class="sota-card-head">
        <div>
          <div class="sota-card-title"><h3>${benchmark.name}</h3><span class="snapshot-badge">${benchmark.snapshot}</span></div>
          <p><strong>${benchmark.metric}</strong> · ${benchmark.protocol}</p>
        </div>
        <a class="sota-source" href="${benchmark.sourceUrl}" target="_blank" rel="noreferrer">${benchmark.sourceLabel}</a>
      </header>
      <div class="sota-table-wrap">
        <table class="sota-table">
          <thead><tr><th>Rank</th><th>Model / Method</th><th>Type</th><th>Score ↑</th><th>Δ vs Jev</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="sota-analysis">
        <div><span>Jev 的优势</span><p>${benchmark.jevEdge}</p></div>
        <div><span>SOTA 的优势 / Jev 缺口</span><p>${benchmark.sotaEdge}</p></div>
      </div>
    </article>`;
  }).join("");
}

function renderReleaseChart() {
  const target = document.getElementById("release-chart");
  const rows = benchmarkData.map((item) => ({
    name: item.name.replace(" · structured pairwise", " · pairwise").replace(" · Human Preference V1", " · HP v1"),
    jev: item.jev,
    reference: Math.max(...item.baselines.map((baseline) => baseline[1])),
    referenceName: item.baselines.reduce((best, baseline) => baseline[1] > best[1] ? baseline : best)[0],
  }));
  const width = 1040;
  const height = 92 + rows.length * 62;
  const labelX = 8;
  const plotLeft = 345;
  const plotRight = 900;
  const scoreX = 1030;
  let svg = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">`;
  svg += `<text x="${labelX}" y="29" fill="${COLORS.muted}" font-size="11" font-weight="800" letter-spacing="1.2">EVALUATION</text>`;
  svg += `<text x="${plotLeft}" y="29" fill="${COLORS.muted}" font-size="11" font-weight="800" letter-spacing="1.2">RELATIVE POSITION WITHIN ROW</text>`;
  svg += `<text x="${scoreX}" y="29" fill="${COLORS.muted}" text-anchor="end" font-size="11" font-weight="800" letter-spacing="1.2">JEV / REF</text>`;
  rows.forEach((row, index) => {
    const y = 68 + index * 62;
    const rowMin = Math.floor((Math.min(row.jev, row.reference) - 5) / 5) * 5;
    const rowMax = Math.min(100, Math.ceil((Math.max(row.jev, row.reference) + 3) / 5) * 5);
    const x = (value) => plotLeft + (value - rowMin) / Math.max(5, rowMax - rowMin) * (plotRight - plotLeft);
    const delta = row.jev - row.reference;
    svg += `<line x1="0" y1="${y + 28}" x2="${width}" y2="${y + 28}" stroke="#e7ebf0"/>`;
    svg += `<text x="${labelX}" y="${y - 3}" fill="${COLORS.ink}" font-size="13" font-weight="750">${row.name}</text>`;
    svg += `<text x="${labelX}" y="${y + 15}" fill="${COLORS.muted}" font-size="10">Δ ${delta.toFixed(2)} pp</text>`;
    svg += `<line x1="${plotLeft}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="#edf0f4" stroke-width="8" stroke-linecap="round"/>`;
    svg += `<line x1="${x(row.jev)}" y1="${y}" x2="${x(row.reference)}" y2="${y}" stroke="#9bc7fb" stroke-width="3"/>`;
    svg += `<circle tabindex="0" data-tooltip="<b>Jev 1.13</b><br>${row.name}: ${row.jev.toFixed(2)}%" cx="${x(row.jev)}" cy="${y}" r="8" fill="${COLORS.blueStrong}"/>`;
    svg += `<circle tabindex="0" data-tooltip="<b>${row.referenceName}</b><br>${row.name}: ${row.reference.toFixed(2)}%" cx="${x(row.reference)}" cy="${y}" r="8" fill="white" stroke="${COLORS.ink}" stroke-width="2.5"/>`;
    svg += `<text x="${scoreX}" y="${y + 4}" fill="${COLORS.ink}" text-anchor="end" font-size="12" font-weight="750">${row.jev.toFixed(1)} / ${row.reference.toFixed(1)}</text>`;
  });
  svg += `</svg>`;
  target.innerHTML = svg;
  bindPoints(target);
}

const capabilityData = [
  ["RewardBench v1", [["Chat", 93.58], ["Chat Hard", 85.75], ["Safety", 93.51], ["Reasoning", 97.48]]],
  ["RewardBench 2", [["Factuality", 80.84], ["Precise IF", 50.63], ["Math", 75.96], ["Safety", 95.33], ["Focus", 90.10], ["Ties", 94.04]]],
  ["RubricBench", [["IF", 74.19], ["STEM", 79.93], ["CODE", 76.38], ["SAFE", 82.50], ["CHAT", 71.96]]],
  ["ProcessBench", [["GSM8K", 74.63], ["MATH", 70.38], ["Olympiad", 66.01], ["Omni-MATH", 67.01]]],
  ["RM-Bench pointwise", [["Chat", 82.77], ["Code", 75.93], ["Math", 83.05], ["Safety", 93.40]]],
];

const ppeData = [
  { model: "Jev 1.13", color: COLORS.blueStrong, values: [64.40, 77.71, 83.16, 90.71, 81.05, 92.63] },
  { model: "Ensemble Judges", color: COLORS.ink, values: [68.59, 82.49, 84.21, 96.21, 87.37, 96.54] },
  { model: "Athene-RM-70B", color: COLORS.gold, values: [66.56, 80.69, 84.74, 93.94, 82.11, 93.23] },
  { model: "Athene-RM-8B", color: "#98a2b3", values: [64.59, 76.85, 83.68, 91.67, 77.89, 90.53] },
];
const ppeMetrics = ["Accuracy", "R.W. Pearson", "Separability", "Conf. agreement", "Kendall τ", "Spearman ρ"];

const efficiencyData = [
  ["RewardBench v1", .1034, 92.58, 2985],
  ["RewardBench 2", .1771, 81.15, 1865],
  ["RM-Bench pairwise", .2178, 81.29, 1327],
  ["RubricBench", .0885, 76.02, 1147],
  ["PPE", 1.0803, 64.40, 16038],
  ["ProcessBench", .2034, 69.51, 3400],
  ["PRMBench", 1.0121, 66.38, 6216],
  ["RM-Bench pointwise", .3102, 83.79, 7962],
];

const tooltip = document.getElementById("chart-tooltip");

function showTooltip(event, html) {
  tooltip.innerHTML = html;
  tooltip.style.left = `${Math.min(event.clientX, window.innerWidth - 260)}px`;
  tooltip.style.top = `${Math.min(event.clientY, window.innerHeight - 120)}px`;
  tooltip.classList.add("is-visible");
}

function hideTooltip() {
  tooltip.classList.remove("is-visible");
}

function bindPoints(container) {
  container.querySelectorAll("[data-tooltip]").forEach((node) => {
    node.addEventListener("pointermove", (event) => showTooltip(event, node.dataset.tooltip));
    node.addEventListener("pointerleave", hideTooltip);
    node.addEventListener("focus", (event) => {
      const rect = node.getBoundingClientRect();
      showTooltip({ clientX: rect.left, clientY: rect.bottom }, node.dataset.tooltip);
    });
    node.addEventListener("blur", hideTooltip);
  });
}

function pathFor(values, x, y) {
  return values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
}

function renderDifficulty(mode = "both") {
  const target = document.getElementById("difficulty-chart");
  const width = 980;
  const height = 390;
  const margin = { top: 38, right: 70, bottom: 60, left: 70 };
  const x = (i) => margin.left + i * ((width - margin.left - margin.right) / 2);
  const y = (v) => margin.top + (100 - v) / 40 * (height - margin.top - margin.bottom);
  const visible = mode === "both" ? ["structured", "pointwise"] : [mode];
  let svg = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">`;
  [60, 70, 80, 90, 100].forEach((tick) => {
    svg += `<line x1="${margin.left}" y1="${y(tick)}" x2="${width - margin.right}" y2="${y(tick)}" stroke="${COLORS.nightLine}"/>`;
    svg += `<text x="${margin.left - 18}" y="${y(tick) + 5}" fill="#7589a2" text-anchor="end" font-size="12">${tick}</text>`;
  });
  difficultyData.labels.forEach((label, i) => {
    svg += `<text x="${x(i)}" y="${height - 22}" fill="#9eb0c5" text-anchor="middle" font-size="14" font-weight="650">${label}</text>`;
  });
  const series = {
    structured: { values: difficultyData.structured, color: COLORS.blue, label: "Structured pairwise" },
    pointwise: { values: difficultyData.pointwise, color: COLORS.gold, label: "Pointwise" },
  };
  visible.forEach((key) => {
    const item = series[key];
    svg += `<path d="${pathFor(item.values, x, y)}" fill="none" stroke="${item.color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`;
    item.values.forEach((value, i) => {
      svg += `<circle tabindex="0" data-tooltip="<b>${item.label}</b><br>${difficultyData.labels[i]}: ${value.toFixed(2)}%" cx="${x(i)}" cy="${y(value)}" r="8" fill="#08111f" stroke="${item.color}" stroke-width="4"/>`;
      svg += `<text x="${x(i)}" y="${y(value) - 16}" fill="${item.color}" text-anchor="middle" font-size="13" font-weight="750">${value.toFixed(1)}</text>`;
    });
  });
  svg += `</svg>`;
  target.innerHTML = svg;
  bindPoints(target);
}

function setupDifficultyControls() {
  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".segment").forEach((other) => {
        other.classList.toggle("is-active", other === button);
        other.setAttribute("aria-pressed", String(other === button));
      });
      renderDifficulty(button.dataset.series);
    });
  });
}

function setupBenchmarkExplorer() {
  const select = document.getElementById("benchmark-select");
  benchmarkData.forEach((item, i) => {
    const option = document.createElement("option");
    option.value = String(i);
    option.textContent = item.name;
    select.appendChild(option);
  });
  select.addEventListener("change", () => renderBaseline(Number(select.value)));
  renderBaseline(0);
}

function renderBaseline(index) {
  const item = benchmarkData[index];
  const target = document.getElementById("baseline-chart");
  const all = [["Jev 1.13", item.jev, true], ...item.baselines.map(([name, score]) => [name, score, false])]
    .sort((a, b) => b[1] - a[1]);
  const width = 800;
  const height = 380;
  const left = 225;
  const plotWidth = 520;
  const minValue = Math.max(0, Math.floor((Math.min(...all.map((d) => d[1])) - 8) / 10) * 10);
  const x = (v) => left + (v - minValue) / (100 - minValue) * plotWidth;
  let svg = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">`;
  for (let tick = minValue; tick <= 100; tick += 10) {
    svg += `<line x1="${x(tick)}" y1="38" x2="${x(tick)}" y2="330" stroke="${COLORS.line}"/>`;
    svg += `<text x="${x(tick)}" y="25" fill="${COLORS.muted}" text-anchor="middle" font-size="12">${tick}</text>`;
  }
  all.forEach(([name, score, isJev], i) => {
    const y = 74 + i * 72;
    svg += `<text x="${left - 18}" y="${y + 5}" fill="${isJev ? COLORS.blueStrong : COLORS.ink}" text-anchor="end" font-size="13" font-weight="${isJev ? 800 : 600}">${name}</text>`;
    svg += `<rect x="${x(minValue)}" y="${y - 11}" width="${x(score) - x(minValue)}" height="22" rx="6" fill="${isJev ? COLORS.blueStrong : "#cbd5e1"}"/>`;
    svg += `<circle tabindex="0" data-tooltip="<b>${name}</b><br>${item.metric}: ${score.toFixed(2)}%" cx="${x(score)}" cy="${y}" r="7" fill="${isJev ? COLORS.blueStrong : COLORS.gold}"/>`;
    svg += `<text x="${Math.min(x(score) + 14, 765)}" y="${y + 5}" fill="${isJev ? COLORS.blueStrong : COLORS.muted}" font-size="13" font-weight="750">${score.toFixed(1)}</text>`;
  });
  svg += `</svg>`;
  target.innerHTML = svg;
  bindPoints(target);
  const best = Math.max(...item.baselines.map((d) => d[1]));
  const delta = item.jev - best;
  document.getElementById("baseline-note").innerHTML = `
    <span class="note-kicker">${item.metric}</span>
    <strong>${item.jev.toFixed(2)}%</strong>
    <small>Jev 1.13</small>
    <p>${item.note}</p>
    <small>相对所列最高 baseline：${delta >= 0 ? "+" : ""}${delta.toFixed(2)} pp</small>`;
}

function capabilityColor(value) {
  const t = Math.max(0, Math.min(1, (value - 45) / 55));
  const mix = (a, b) => Math.round(a + (b - a) * t);
  return `rgb(${mix(225, 35)}, ${mix(235, 105)}, ${mix(249, 220)})`;
}

function renderCapabilities() {
  const target = document.getElementById("capability-grid");
  target.innerHTML = capabilityData.map(([benchmark, values]) => {
    const cells = values.map(([label, score]) => `
      <div class="cap-cell ${score >= 76 ? "is-dark" : ""}" style="background:${capabilityColor(score)}" title="${benchmark} · ${label}: ${score.toFixed(2)}%">
        <span>${label}</span><strong>${score.toFixed(1)}%</strong>
      </div>`).join("");
    return `<div class="cap-row"><div class="cap-label">${benchmark}</div>${cells}</div>`;
  }).join("");
}

function renderPpe() {
  const target = document.getElementById("ppe-chart");
  const width = 980;
  const height = 500;
  const left = 205;
  const right = 55;
  const x = (v) => left + (v - 55) / 45 * (width - left - right);
  let svg = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">`;
  [60, 70, 80, 90, 100].forEach((tick) => {
    svg += `<line x1="${x(tick)}" y1="36" x2="${x(tick)}" y2="390" stroke="${COLORS.line}"/>`;
    svg += `<text x="${x(tick)}" y="22" fill="${COLORS.muted}" text-anchor="middle" font-size="12">${tick}</text>`;
  });
  ppeMetrics.forEach((metric, i) => {
    const y = 64 + i * 62;
    svg += `<text x="${left - 18}" y="${y + 5}" fill="${COLORS.ink}" text-anchor="end" font-size="13" font-weight="650">${metric}</text>`;
    svg += `<line x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" stroke="#e7ebf0" stroke-width="8" stroke-linecap="round"/>`;
    ppeData.forEach((model, j) => {
      const value = model.values[i];
      const cy = y + (j - 1.5) * 8;
      svg += `<circle tabindex="0" data-tooltip="<b>${model.model}</b><br>${metric}: ${value.toFixed(2)}" cx="${x(value)}" cy="${cy}" r="7" fill="${model.color}" stroke="white" stroke-width="2"/>`;
    });
  });
  ppeData.forEach((model, i) => {
    const lx = 70 + i * 225;
    svg += `<circle cx="${lx}" cy="455" r="7" fill="${model.color}"/>`;
    svg += `<text x="${lx + 14}" y="460" fill="${COLORS.ink}" font-size="12" font-weight="${i === 0 ? 750 : 500}">${model.model}</text>`;
  });
  svg += `</svg>`;
  target.innerHTML = svg;
  bindPoints(target);
}

function renderEfficiency() {
  const target = document.getElementById("efficiency-chart");
  const width = 980;
  const height = 500;
  const margin = { top: 45, right: 55, bottom: 70, left: 75 };
  const x = (v) => margin.left + v / 1.15 * (width - margin.left - margin.right);
  const y = (v) => margin.top + (100 - v) / 40 * (height - margin.top - margin.bottom);
  let svg = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">`;
  [60, 70, 80, 90, 100].forEach((tick) => {
    svg += `<line x1="${margin.left}" y1="${y(tick)}" x2="${width - margin.right}" y2="${y(tick)}" stroke="${COLORS.nightLine}"/>`;
    svg += `<text x="${margin.left - 16}" y="${y(tick) + 5}" fill="#8294aa" text-anchor="end" font-size="12">${tick}%</text>`;
  });
  [0, .25, .5, .75, 1].forEach((tick) => {
    svg += `<line x1="${x(tick)}" y1="${margin.top}" x2="${x(tick)}" y2="${height - margin.bottom}" stroke="${COLORS.nightLine}"/>`;
    svg += `<text x="${x(tick)}" y="${height - 34}" fill="#8294aa" text-anchor="middle" font-size="12">$${tick.toFixed(2)}</text>`;
  });
  svg += `<text x="${width / 2}" y="${height - 8}" fill="#9eb0c5" text-anchor="middle" font-size="13">估算输入成本（USD）</text>`;
  efficiencyData.forEach(([name, cost, score, samples], i) => {
    const r = 7 + Math.sqrt(samples / 16038) * 15;
    const color = i === 0 ? COLORS.blue : (i === 6 ? COLORS.gold : COLORS.cyan);
    const anchor = cost > .8 ? "end" : "start";
    const labelX = x(cost) + (anchor === "end" ? -14 : 14);
    svg += `<circle tabindex="0" data-tooltip="<b>${name}</b><br>主指标: ${score.toFixed(2)}%<br>成本: $${cost.toFixed(4)}<br>记录: ${samples.toLocaleString()}" cx="${x(cost)}" cy="${y(score)}" r="${r}" fill="${color}" fill-opacity=".72" stroke="${color}" stroke-width="2"/>`;
    svg += `<text x="${labelX}" y="${y(score) + 4}" fill="#c8d7e8" text-anchor="${anchor}" font-size="11">${name}</text>`;
  });
  svg += `</svg>`;
  target.innerHTML = svg;
  bindPoints(target);
}

function setupCitation() {
  const button = document.getElementById("copy-citation");
  button.addEventListener("click", async () => {
    const citation = document.getElementById("bibtex").textContent;
    try {
      await navigator.clipboard.writeText(citation);
      button.textContent = "已复制";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(document.getElementById("bibtex"));
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "已选中，请复制";
    }
    window.setTimeout(() => { button.textContent = "复制 BibTeX"; }, 1800);
  });
}

function init() {
  renderReleaseChart();
  renderDifficulty();
  setupDifficultyControls();
  renderSotaDossiers();
  renderCapabilities();
  renderPpe();
  renderEfficiency();
  setupCitation();
}

init();
