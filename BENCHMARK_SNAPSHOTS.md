# Phase 2 benchmark snapshots

Frozen on 2026-09-20 for the full Jev evaluation.

| Benchmark | Source | Revision |
|---|---|---|
| ProcessBench | `Qwen/ProcessBench` | `3bdcd5371ed567559a78f559c01c13a6deee7604` |
| PRMBench Preview | `hitsmy/PRMBench_Preview` | `5cc7683d0ae5797f84d7aeac0607966f277c39e1` |
| RM-Bench | `THU-KEG/RM-Bench` | `73c52d7b27b361621361ec959ac6c0eb9bb7a689` |
| RMB | `Zhou-Zoey/RMB-Reward-Model-Benchmark` | `2be3180857f2190b7ffa929d43190835627f1f4d` |
| PPE scorer | `lmarena/PPE` | `173b588e100482a0e550d2923e3ba5b227fbbf45` |
| PPE MMLU-Pro | `lmarena-ai/PPE-MMLU-Pro-Best-of-K` | `d3a309b95d5a3a34efdd2b01a9e3ee10565bf0c7` |
| PPE MATH | `lmarena-ai/PPE-MATH-Best-of-K` | `c46ce3cda5417fe8d170e992d925f93856b5db40` |
| PPE GPQA | `lmarena-ai/PPE-GPQA-Best-of-K` | `2f85cea6481db81daa2c8033c51b7811b7bbf648` |
| PPE IFEval | `lmarena-ai/PPE-IFEval-Best-of-K` | `a4f7fae2443d96529dee6b65863a816a051b3a4d` |
| PPE MBPP-Plus | `lmarena-ai/PPE-MBPP-Plus-Best-of-K` | `afa814632c1df94e76b6af2c1d282511114cd2b7` |

The loaders pin the Hugging Face revisions and RM-Bench raw URL. RMB is read from
the locally cloned revision listed above. The result records also retain the model
version returned by the Jev API for every example.
