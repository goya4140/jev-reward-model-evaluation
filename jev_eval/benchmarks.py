from __future__ import annotations

import hashlib
import json
import random
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from datasets import load_dataset


RM_BENCH_URL = (
    "https://raw.githubusercontent.com/THU-KEG/RM-Bench/"
    "73c52d7b27b361621361ec959ac6c0eb9bb7a689/data/total_dataset.json"
)
RUBRIC_BENCH_URL = (
    "https://raw.githubusercontent.com/planepig/rubricbench/main/data/"
    "rubricbench_data.json"
)
RMB_ROOT = Path(".cache/sources/RMB/RMB_dataset")

PPE_CORRECTNESS_DATASETS = {
    "ppe_mmlu_pro": ("lmarena-ai/PPE-MMLU-Pro-Best-of-K", "d3a309b95d5a3a34efdd2b01a9e3ee10565bf0c7"),
    "ppe_math": ("lmarena-ai/PPE-MATH-Best-of-K", "c46ce3cda5417fe8d170e992d925f93856b5db40"),
    "ppe_gpqa": ("lmarena-ai/PPE-GPQA-Best-of-K", "2f85cea6481db81daa2c8033c51b7811b7bbf648"),
    "ppe_ifeval": ("lmarena-ai/PPE-IFEval-Best-of-K", "a4f7fae2443d96529dee6b65863a816a051b3a4d"),
    "ppe_mbpp_plus": ("lmarena-ai/PPE-MBPP-Plus-Best-of-K", "afa814632c1df94e76b6af2c1d282511114cd2b7"),
}


@dataclass
class Example:
    benchmark: str
    example_id: str
    subset: str
    prompt: str
    candidates: list[str]
    correct: list[int]
    mode: str
    rubrics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _download_json(url: str, cache_path: Path) -> Any:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if not cache_path.exists():
        with urllib.request.urlopen(url, timeout=120) as response:
            content = response.read()
        cache_path.write_bytes(content)
    return json.loads(cache_path.read_text())


def _swap(example_id: str) -> bool:
    return hashlib.sha256(example_id.encode()).digest()[0] & 1 == 1


def _permutation(key: str, size: int) -> list[int]:
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    indices = list(range(size))
    random.Random(seed).shuffle(indices)
    return indices


def _pair(
    *,
    benchmark: str,
    example_id: str,
    subset: str,
    prompt: str,
    preferred: str,
    rejected: str,
    metadata: dict[str, Any] | None = None,
    rubrics: list[str] | None = None,
) -> Example:
    if _swap(f"{benchmark}:{example_id}"):
        candidates, correct = [rejected, preferred], [1]
    else:
        candidates, correct = [preferred, rejected], [0]
    return Example(
        benchmark=benchmark,
        example_id=example_id,
        subset=subset,
        prompt=prompt,
        candidates=candidates,
        correct=correct,
        mode="pairwise",
        metadata=metadata or {},
        rubrics=rubrics or [],
    )


@lru_cache(maxsize=1)
def rewardbench1() -> list[Example]:
    rows = load_dataset("allenai/reward-bench", split="filtered")
    return [
        _pair(
            benchmark="rewardbench1",
            example_id=f"{idx}:{row['id']}",
            subset=row["subset"],
            prompt=row["prompt"],
            preferred=row["chosen"],
            rejected=row["rejected"],
            metadata={
                "original_id": str(row["id"]),
                "chosen_model": row.get("chosen_model"),
                "rejected_model": row.get("rejected_model"),
            },
        )
        for idx, row in enumerate(rows)
    ]


@lru_cache(maxsize=1)
def rewardbench2() -> list[Example]:
    rows = load_dataset("allenai/reward-bench-2", split="test")
    examples: list[Example] = []
    for idx, row in enumerate(rows):
        original = list(row["chosen"]) + list(row["rejected"])
        order = _permutation(f"rewardbench2:{idx}:{row['id']}", len(original))
        candidates = [original[i] for i in order]
        correct = [new_idx for new_idx, old_idx in enumerate(order) if old_idx < int(row["num_correct"])]
        examples.append(
            Example(
                benchmark="rewardbench2",
                example_id=f"{idx}:{row['id']}",
                subset=row["subset"],
                prompt=row["prompt"],
                candidates=candidates,
                correct=correct,
                mode="ratings" if row["subset"].lower() == "ties" else "listwise",
                metadata={
                    "num_correct": int(row["num_correct"]),
                    "total_completions": int(row["total_completions"]),
                    "original_id": str(row["id"]),
                    "additional_metadata": row.get("additional_metadata"),
                },
            )
        )
    return examples


@lru_cache(maxsize=1)
def rm_bench(cache_dir: str = ".cache") -> list[Example]:
    rows = _download_json(RM_BENCH_URL, Path(cache_dir) / "rm_bench.json")
    examples: list[Example] = []
    for row in rows:
        original = list(row["chosen"]) + list(row["rejected"])
        order = _permutation(f"rm_bench:{row['id']}", 6)
        inverse = {old_idx: new_idx for new_idx, old_idx in enumerate(order)}
        grid_pairs = [
            [inverse[chosen_style], inverse[3 + rejected_style]]
            for chosen_style in range(3)
            for rejected_style in range(3)
        ]
        examples.append(
            Example(
                benchmark="rm_bench",
                example_id=str(row["id"]),
                subset=row["domain"],
                prompt=row["prompt"],
                candidates=[original[i] for i in order],
                correct=[inverse[i] for i in range(3)],
                mode="rm_style_grid",
                metadata={"grid_pairs": grid_pairs},
            )
        )
    return examples


@lru_cache(maxsize=1)
def rubric_bench(cache_dir: str = ".cache") -> list[Example]:
    rows = _download_json(RUBRIC_BENCH_URL, Path(cache_dir) / "rubric_bench.json")
    examples: list[Example] = []
    for row in rows:
        label = int(row["label"])
        preferred = row["response_a"] if label == 0 else row["response_b"]
        rejected = row["response_b"] if label == 0 else row["response_a"]
        examples.append(
            _pair(
                benchmark="rubric_bench",
                example_id=row["case_id"],
                subset=row["domain"],
                prompt=row["instruction"],
                preferred=preferred,
                rejected=rejected,
                rubrics=[x.strip() for x in row["rubrics"].splitlines() if x.strip()],
                metadata={"source": row["source"], "original_label": label},
            )
        )
    return examples


@lru_cache(maxsize=1)
def ppe() -> list[Example]:
    rows = load_dataset("lmarena-ai/PPE-Human-Preference-V1", split="test")
    examples: list[Example] = []
    for idx, row in enumerate(rows):
        winner = row["winner"]
        correct = [0] if winner == "model_a" else [1] if winner == "model_b" else [0, 1]
        examples.append(
            Example(
                benchmark="ppe",
                example_id=f"{row['question_id']}:{idx}",
                subset=row["language"],
                prompt=row["prompt"],
                candidates=[row["response_1"], row["response_2"]],
                correct=correct,
                mode="pairwise_tie",
                metadata={
                    "question_id": row["question_id"],
                    "model_a": row["model_a"],
                    "model_b": row["model_b"],
                    "winner": winner,
                    "language": row["language"],
                    "is_code": bool(row["is_code"]),
                    "is_refusal": bool(row["is_refusal"]),
                    "hard_prompt": bool(row["hard_prompt"]),
                    "easy_prompt": bool(row["easy_prompt"]),
                    "if_prompt": bool(row["if_prompt"]),
                    "math_prompt": bool(row["math_prompt"]),
                    "length_a": int(row["length_a"]),
                    "length_b": int(row["length_b"]),
                },
            )
        )
    return examples


@lru_cache(maxsize=1)
def processbench() -> list[Example]:
    examples: list[Example] = []
    for split in ("gsm8k", "math", "olympiadbench", "omnimath"):
        rows = load_dataset(
            "Qwen/ProcessBench",
            revision="3bdcd5371ed567559a78f559c01c13a6deee7604",
            split=split,
        )
        for row in rows:
            examples.append(
                Example(
                    benchmark="processbench",
                    example_id=str(row["id"]),
                    subset=split,
                    prompt=row["problem"],
                    candidates=list(row["steps"]),
                    correct=[int(row["label"])],
                    mode="process_first_error",
                    metadata={
                        "label": int(row["label"]),
                        "step_count": len(row["steps"]),
                    },
                )
            )
    return examples


@lru_cache(maxsize=1)
def prmbench() -> list[Example]:
    rows = load_dataset(
        "hitsmy/PRMBench_Preview",
        revision="5cc7683d0ae5797f84d7aeac0607966f277c39e1",
        split="train",
    )
    return [
        Example(
            benchmark="prmbench",
            # The preview contains five duplicated `idx` values.  Prefixing the
            # physical row index preserves every official example and makes
            # resume semantics unambiguous.
            example_id=f"{row_idx}:{row['idx']}",
            subset=str(row["classification"]),
            prompt=row["modified_question"],
            candidates=list(row["modified_process"]),
            correct=[int(i) - 1 for i in row["error_steps"]],
            mode="prm_steps",
            metadata={
                "classification": str(row["classification"]),
                "error_steps": [int(i) - 1 for i in row["error_steps"]],
                "step_count": len(row["modified_process"]),
            },
        )
        for row_idx, row in enumerate(rows)
    ]


@lru_cache(maxsize=1)
def rm_bench_pointwise(cache_dir: str = ".cache") -> list[Example]:
    rows = _download_json(RM_BENCH_URL, Path(cache_dir) / "rm_bench.json")
    examples: list[Example] = []
    for row in rows:
        for preferred, prefix in ((True, "chosen"), (False, "rejected")):
            for style, response in enumerate(row[prefix]):
                examples.append(
                    Example(
                        benchmark="rm_bench_pointwise",
                        example_id=f"{row['id']}:{prefix}:{style}",
                        subset=row["domain"],
                        prompt=row["prompt"],
                        candidates=[response],
                        correct=[],
                        mode="ordinal_quality",
                        metadata={
                            "prompt_id": str(row["id"]),
                            "preferred": preferred,
                            "style": style,
                            "domain": row["domain"],
                        },
                    )
                )
    return examples


def _conversation_prompt(turns: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"{str(turn.get('role', 'user')).upper()}: {turn.get('content', '')}"
        for turn in turns
    )


def _rmb_files(part: str, root: Path = RMB_ROOT) -> list[Path]:
    part_root = root / part
    if not part_root.exists():
        raise FileNotFoundError(
            f"RMB data not found at {part_root}. Clone the official repository to "
            ".cache/sources/RMB before running RMB."
        )
    return sorted(part_root.rglob("*.json"))


@lru_cache(maxsize=1)
def rmb_pairwise() -> list[Example]:
    examples: list[Example] = []
    for path in _rmb_files("Pairwise_set"):
        scenario = str(path.relative_to(RMB_ROOT / "Pairwise_set").with_suffix(""))
        objective = scenario.split("/", 1)[0]
        for row in json.loads(path.read_text()):
            group_id = f"{scenario}:{row['pair_uid']}"
            prompt = _conversation_prompt(row["conversation_input"])
            for preferred, item in ((True, row["chosen"]), (False, row["reject"])):
                examples.append(
                    Example(
                        benchmark="rmb_pairwise",
                        example_id=f"{group_id}:{'winner' if preferred else 'loser'}",
                        subset=scenario,
                        prompt=prompt,
                        candidates=[item["answer"]],
                        correct=[],
                        mode="ordinal_quality",
                        metadata={
                            "group_id": group_id,
                            "preferred": preferred,
                            "objective": objective,
                            "scenario": scenario,
                        },
                    )
                )
    return examples


@lru_cache(maxsize=1)
def rmb_bon() -> list[Example]:
    examples: list[Example] = []
    for path in _rmb_files("BoN_set"):
        scenario = str(path.relative_to(RMB_ROOT / "BoN_set").with_suffix(""))
        objective = scenario.split("/", 1)[0]
        for row in json.loads(path.read_text()):
            group_id = f"{scenario}:{row['bon_uid']}"
            prompt = _conversation_prompt(row["conversation_input"])
            candidates = [row["bon_best"], *row["loser_list"]]
            order = _permutation(f"rmb_bon:{group_id}", len(candidates))
            for position, source_idx in enumerate(order):
                item = candidates[source_idx]
                examples.append(
                    Example(
                        benchmark="rmb_bon",
                        example_id=f"{group_id}:{position}",
                        subset=scenario,
                        prompt=prompt,
                        candidates=[item["answer"]],
                        correct=[],
                        mode="ordinal_quality",
                        metadata={
                            "group_id": group_id,
                            "candidate_index": position,
                            "preferred": source_idx == 0,
                            "candidate_count": len(candidates),
                            "objective": objective,
                            "scenario": scenario,
                        },
                    )
                )
    return examples


def _ppe_correctness(name: str, source: tuple[str, str]) -> list[Example]:
    dataset_name, revision = source
    rows = load_dataset(dataset_name, revision=revision, split="train")
    examples: list[Example] = []
    for row_idx, row in enumerate(rows):
        labels = list(row["scores"])
        for response_idx in range(32):
            response = row[f"response_{response_idx + 1}"]
            examples.append(
                Example(
                    benchmark=name,
                    example_id=f"{row['question_id']}:{row_idx}:{response_idx}",
                    subset=name.removeprefix("ppe_"),
                    prompt=row["prompt"],
                    candidates=[response],
                    correct=[1 if bool(labels[response_idx]) else 0],
                    mode="binary_correctness",
                    metadata={
                        "question_id": str(row["question_id"]),
                        "row_index": row_idx,
                        "response_index": response_idx,
                        "ground_truth": bool(labels[response_idx]),
                        "model_name": row.get("model_name"),
                        "sampled_conflict_pairs": row.get("sampled_conflict_pairs", []),
                    },
                )
            )
    return examples


def ppe_mmlu_pro() -> list[Example]:
    return _ppe_correctness("ppe_mmlu_pro", PPE_CORRECTNESS_DATASETS["ppe_mmlu_pro"])


def ppe_math() -> list[Example]:
    return _ppe_correctness("ppe_math", PPE_CORRECTNESS_DATASETS["ppe_math"])


def ppe_gpqa() -> list[Example]:
    return _ppe_correctness("ppe_gpqa", PPE_CORRECTNESS_DATASETS["ppe_gpqa"])


def ppe_ifeval() -> list[Example]:
    return _ppe_correctness("ppe_ifeval", PPE_CORRECTNESS_DATASETS["ppe_ifeval"])


def ppe_mbpp_plus() -> list[Example]:
    return _ppe_correctness("ppe_mbpp_plus", PPE_CORRECTNESS_DATASETS["ppe_mbpp_plus"])


LOADERS = {
    "rewardbench1": rewardbench1,
    "rewardbench2": rewardbench2,
    "rm_bench": rm_bench,
    "rubric_bench": rubric_bench,
    "ppe": ppe,
    "processbench": processbench,
    "prmbench": prmbench,
    "rm_bench_pointwise": rm_bench_pointwise,
    "rmb_pairwise": rmb_pairwise,
    "rmb_bon": rmb_bon,
    "ppe_mmlu_pro": ppe_mmlu_pro,
    "ppe_math": ppe_math,
    "ppe_gpqa": ppe_gpqa,
    "ppe_ifeval": ppe_ifeval,
    "ppe_mbpp_plus": ppe_mbpp_plus,
}


def load_examples(names: Iterable[str]) -> dict[str, list[Example]]:
    return {name: LOADERS[name]() for name in names}
