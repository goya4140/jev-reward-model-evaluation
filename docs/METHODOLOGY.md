# Methodology and comparability notes

## Scope

The report covers eight completed evaluation tracks:

1. RewardBench v1
2. RewardBench 2
3. RM-Bench structured pairwise
4. RubricBench with benchmark-provided human rubrics
5. PPE Human Preference V1
6. ProcessBench
7. PRMBench Preview
8. RM-Bench pointwise

They represent seven benchmark families because RM-Bench is measured under two distinct inference protocols.

## Model and inference controls

- The API-reported model version is `jev-1.13.0` for every successful record.
- Preferred-response position is randomized deterministically by sample identity.
- Labels are excluded from candidate names and prompt-visible metadata.
- Requests return structured choices, scores, or step labels rather than free-form prose.
- Interrupted runs resume from JSONL records keyed by unique sample identity.
- Aggregate reports count only records with `status == "ok"`.

## Primary metrics

| Track | Primary metric | Interpretation |
|---|---|---|
| RewardBench v1 | Macro mean of Chat, Chat Hard, Safety, Reasoning | Pairwise preference accuracy with benchmark section weighting |
| RewardBench 2 | Macro mean of Factuality, Precise IF, Math, Safety, Focus, Ties | Multi-skill reward-model accuracy |
| RM-Bench | Macro mean of Chat, Code, Math, merged Safety | Robustness to content subtlety and style bias |
| RubricBench | Pairwise accuracy | Agreement with labeled preference when given the human rubric |
| PPE Human Preference V1 | No-tie pairwise accuracy | Agreement with real Chatbot Arena preferences |
| ProcessBench | Mean of per-split harmonic F1 | Balance between detecting erroneous and fully correct traces |
| PRMBench | Mean of positive-step and negative-step F1 | Fine-grained process reward quality |

## RM-Bench protocols

The structured-pairwise protocol asks Jev for all required comparisons for one prompt in a single structured response. The pointwise protocol independently scores each response and derives pairwise order from those scores. Both are reduced with the official four-domain formula after merging the two raw Safety subsets.

The two tracks answer different questions. Structured pairwise measures direct comparative judging efficiency. Pointwise more closely resembles a scalar reward model and reduces cross-candidate context effects, but requires six calls per prompt in this implementation.

## RubricBench protocol

The benchmark's human-authored rubric is supplied directly to Jev. This makes the input condition an Oracle Rubric setting. The implementation does not reproduce the paper's full CheckEval, TICK, or OpenRubric oracle pipelines. Paper values are therefore protocol-adjacent references, not exact apples-to-apples replications.

## PPE metrics

- **Accuracy:** no-tie pairwise agreement with human preference.
- **Row-wise Pearson:** average correlation between predicted and human model win-rate rows.
- **Separability:** share of model-ranking pairs separated at the benchmark's confidence criterion.
- **Confidence agreement:** agreement on confidently ordered model pairs.
- **Kendall tau / Spearman:** rank correlation over the 20 evaluated models.
- **Brier score:** probabilistic forecast error; lower is better.

The original PPE pipeline uses repeated bootstrap estimation for some ranking statistics. This evaluation uses deterministic Bradley–Terry fitting and benchmark-compatible aggregate calculations. Values are close enough for diagnostic comparison but are not an official PPE leaderboard submission.

## Baseline selection

Baseline values come from official benchmark leaderboards or papers and are stored with source URLs in [`data/baselines.csv`](../data/baselines.csv). The headline chart selects one strong, reasonably protocol-adjacent model reference per track. It does not imply a globally consistent model suite.

Important comparison limitations:

- model sizes and inference budgets differ;
- some methods use ensembles, voting, or long reasoning;
- leaderboard snapshots were published at different times;
- some leaderboard entries may be benchmark-contaminated;
- no statistical significance claim is made for small differences.

## Cost and latency

The report estimates input cost at `$0.042 / 1M input tokens`, matching the project assumption used during evaluation. It does not include unreported output-token or platform charges. Latency is measured wall-clock API request latency and therefore includes network and service variability.

## Data release policy

The public repository includes aggregate results, selected baseline values, charts, code, and tests. Raw benchmark prompts, responses, per-example model outputs, local caches, and API credentials are excluded.
