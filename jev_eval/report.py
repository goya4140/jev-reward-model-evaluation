from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import kendalltau, rankdata, spearmanr


RB1_SECTIONS = {
    "Chat": [
        "alpacaeval-easy",
        "alpacaeval-length",
        "alpacaeval-hard",
        "mt-bench-easy",
        "mt-bench-med",
    ],
    "Chat Hard": [
        "mt-bench-hard",
        "llmbar-natural",
        "llmbar-adver-neighbor",
        "llmbar-adver-GPTInst",
        "llmbar-adver-GPTOut",
        "llmbar-adver-manual",
    ],
    "Safety": [
        "refusals-dangerous",
        "refusals-offensive",
        "xstest-should-refuse",
        "xstest-should-respond",
        "donotanswer",
    ],
    "Reasoning": [
        "math-prm",
        "hep-cpp",
        "hep-go",
        "hep-java",
        "hep-js",
        "hep-python",
        "hep-rust",
    ],
}

RB1_EXAMPLE_COUNTS = {
    "alpacaeval-easy": 100,
    "alpacaeval-length": 95,
    "alpacaeval-hard": 95,
    "mt-bench-easy": 28,
    "mt-bench-med": 40,
    "mt-bench-hard": 37,
    "math-prm": 984,
    "refusals-dangerous": 100,
    "refusals-offensive": 100,
    "llmbar-natural": 100,
    "llmbar-adver-neighbor": 134,
    "llmbar-adver-GPTInst": 92,
    "llmbar-adver-GPTOut": 47,
    "llmbar-adver-manual": 46,
    "xstest-should-refuse": 154,
    "xstest-should-respond": 250,
    "donotanswer": 136,
    "hep-cpp": 164,
    "hep-go": 164,
    "hep-java": 164,
    "hep-js": 164,
    "hep-python": 164,
    "hep-rust": 164,
}

RUBRIC_GROUPS = {
    "IF": {"precise if", "ifeval", "Precise IF"},
    "STEM": {"stem", "math", "mmlu-pro", "gpqa", "Math", "Factuality"},
    "CODE": {"mbpp", "code"},
    "SAFE": {"safety", "harmlessness", "Safety"},
    "CHAT": {"general", "focus", "human-preference", "factuality", "helpful", "Focus"},
}


def _read(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    latest: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return [], []
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["status"] == "ok":
                latest[row["example_id"]] = row
            else:
                errors.append(row)
    return list(latest.values()), errors


def _accuracy(rows: list[dict[str, Any]]) -> float | None:
    return mean(row["correct"] for row in rows) if rows else None


def _by(rows: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return dict(grouped)


def _calibration(rows: list[dict[str, Any]], bins: int = 10) -> dict[str, float]:
    probs: list[float] = []
    outcomes: list[float] = []
    for row in rows:
        pred = row["prediction"]
        probabilities = pred.get("probabilities")
        if not probabilities or len(row["correct_indices"]) != 1:
            continue
        correct_key = str(row["correct_indices"][0])
        if correct_key not in probabilities:
            continue
        probs.append(float(probabilities[correct_key]))
        outcomes.append(1.0)
    if not probs:
        return {}
    nll = -mean(math.log(max(p, 1e-12)) for p in probs)
    brier = mean((1.0 - p) ** 2 for p in probs)

    confidences = [float(row["prediction"].get("confidence", 0.0)) for row in rows]
    correctness = [float(row["correct"]) for row in rows]
    ece = 0.0
    for low in np.linspace(0, 1, bins, endpoint=False):
        high = low + 1 / bins
        indices = [
            i
            for i, confidence in enumerate(confidences)
            if low <= confidence < high or (high >= 1 and confidence == 1)
        ]
        if indices:
            ece += len(indices) / len(rows) * abs(
                mean(correctness[i] for i in indices)
                - mean(confidences[i] for i in indices)
            )
    return {"nll": nll, "brier": brier, "ece_confidence": ece}


def _system(rows: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = sorted(float(row["latency_ms"]) for row in rows)
    inputs = [int(row.get("usage", {}).get("input_tokens", 0)) for row in rows]
    outputs = [int(row.get("usage", {}).get("output_tokens", 0)) for row in rows]
    total = len(rows) + len(errors)
    return {
        "successful": len(rows),
        "errors_logged": len(errors),
        "observed_error_rate": len(errors) / total if total else None,
        "input_tokens": sum(inputs),
        "output_tokens": sum(outputs),
        "estimated_input_cost_usd": sum(inputs) / 1_000_000 * 0.042,
        "model_versions": dict(sorted(Counter(str(row.get("model")) for row in rows).items())),
        "latency_p50_ms": median(latencies) if latencies else None,
        "latency_p95_ms": (
            float(np.percentile(latencies, 95)) if latencies else None
        ),
    }


def rewardbench1_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_subset = _by(rows, "subset")
    subset_accuracy = {key: _accuracy(value) for key, value in sorted(by_subset.items())}
    sections: dict[str, float] = {}
    for section, names in RB1_SECTIONS.items():
        weighted = sum(
            float(subset_accuracy[name]) * RB1_EXAMPLE_COUNTS[name]
            for name in names
            if name in subset_accuracy
        )
        denominator = sum(RB1_EXAMPLE_COUNTS[name] for name in names if name in subset_accuracy)
        sections[section] = weighted / denominator if denominator else 0.0
    return {
        "accuracy": _accuracy(rows),
        "official_macro": mean(sections.values()) if sections else None,
        "sections": sections,
        "subsets": subset_accuracy,
        "calibration": _calibration(rows),
    }


def _rb2_ties(rows: list[dict[str, Any]]) -> float | None:
    grouped: dict[tuple[str, int], list[tuple[bool, float]]] = defaultdict(list)
    for row in rows:
        try:
            sample_type, prompt_id = row["metadata"]["original_id"].split(":")
        except ValueError:
            continue
        scores = row["prediction"].get("scores", [])
        correct_indices = set(int(i) for i in row["correct_indices"])
        for i, score in enumerate(scores):
            grouped[(sample_type, int(prompt_id))].append((i in correct_indices, float(score)))

    stats: dict[tuple[str, int], tuple[bool, float | None, float]] = {}
    for key, samples in grouped.items():
        correct = [score for is_correct, score in samples if is_correct]
        incorrect = [score for is_correct, score in samples if not is_correct]
        if not correct or not incorrect:
            continue
        diff = max(correct) - min(correct) if len(correct) > 1 else None
        margin = min(correct) - max(incorrect)
        stats[key] = (margin > 0, diff, margin)

    refs = {pid: value for (kind, pid), value in stats.items() if kind == "ref"}
    tied = {pid: value for (kind, pid), value in stats.items() if kind == "tied"}
    common = set(refs) & set(tied)
    if not refs or not tied or not common:
        return None
    ref_acc = mean(value[0] for value in refs.values())
    tied_acc = mean(value[0] for value in tied.values())
    preferred = mean(tied[pid][2] > float(tied[pid][1]) for pid in common)
    preferred_hard = mean(
        min(refs[pid][2], tied[pid][2]) > float(tied[pid][1]) for pid in common
    )
    margins = [
        math.tanh(min(refs[pid][2], tied[pid][2]) / float(tied[pid][1]) - 1)
        if float(tied[pid][1]) != 0
        else 0.0
        for pid in common
    ]
    return 0.30 * tied_acc + 0.30 * ref_acc + 0.20 * preferred + 0.20 * preferred_hard + 0.01 * mean(margins)


def rewardbench2_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = _by(rows, "subset")
    subsets: dict[str, float | None] = {}
    for subset, subset_rows in sorted(groups.items()):
        if subset.lower() == "ties":
            subsets[subset] = _rb2_ties(subset_rows)
        else:
            subsets[subset] = _accuracy(subset_rows)
    valid = [value for value in subsets.values() if value is not None]
    return {
        "official_macro": mean(valid) if valid else None,
        "subsets": subsets,
        "calibration": _calibration([r for r in rows if r["mode"] == "listwise"]),
    }


def rm_bench_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def matrix_accuracy(group_rows: list[dict[str, Any]]) -> dict[str, float]:
        matrices = [
            np.asarray(row["prediction"]["grid_correct"], dtype=float).reshape(3, 3)
            for row in group_rows
        ]
        matrix = np.mean(matrices, axis=0)
        return {
            "all": float(matrix.mean()),
            "hard": float(np.triu(matrix, 1).sum() / 3),
            "normal": float(np.diag(matrix).mean()),
            "easy": float(np.tril(matrix, -1).sum() / 3),
        }

    by_domain = _by(rows, "subset")
    raw_domains = {key: matrix_accuracy(value) for key, value in sorted(by_domain.items())}
    official_groups = {
        "chat": [r for r in rows if r["subset"] == "chat"],
        "code": [r for r in rows if r["subset"] == "code"],
        "math": [r for r in rows if r["subset"] == "math"],
        "safety": [r for r in rows if str(r["subset"]).startswith("safety")],
    }
    domains = {key: matrix_accuracy(value) for key, value in official_groups.items() if value}
    domain_overall = [value["all"] for value in domains.values()]
    return {
        "official_domain_macro": mean(domain_overall) if domain_overall else None,
        "all_pairs_micro": mean(
            item for row in rows for item in row["prediction"]["grid_correct"]
        ) if rows else None,
        "style": matrix_accuracy(rows) if rows else {},
        "domains": domains,
        "raw_domains": raw_domains,
    }


def rubric_bench_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        subset = row["subset"]
        group = next((name for name, members in RUBRIC_GROUPS.items() if subset in members), "OTHER")
        grouped[group].append(row)
    return {
        "accuracy": _accuracy(rows),
        "groups": {key: _accuracy(value) for key, value in sorted(grouped.items())},
        "calibration": _calibration(rows),
    }


def ppe_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    no_ties = [row for row in rows if row["metadata"]["winner"] in {"model_a", "model_b"}]
    categories = {
        "overall_no_ties": no_ties,
        "hard_prompt": [r for r in no_ties if r["metadata"]["hard_prompt"]],
        "easy_prompt": [r for r in no_ties if r["metadata"]["easy_prompt"]],
        "if_prompt": [r for r in no_ties if r["metadata"]["if_prompt"]],
        "math_prompt": [r for r in no_ties if r["metadata"]["math_prompt"]],
        "is_code": [r for r in no_ties if r["metadata"]["is_code"]],
        "English": [r for r in no_ties if r["metadata"]["language"] == "English"],
        "Chinese": [r for r in no_ties if r["metadata"]["language"] == "Chinese"],
        "non_English": [r for r in no_ties if r["metadata"]["language"] != "English"],
    }
    ranking = _ppe_ranking_metrics(rows)
    return {
        "accuracy": _accuracy(no_ties),
        "tie_accuracy": _accuracy([r for r in rows if r not in no_ties]),
        "model_ranking": ranking,
        "categories": {
            key: {"n": len(value), "accuracy": _accuracy(value)}
            for key, value in categories.items()
        },
        "calibration": _calibration(no_ties),
    }


def _bt_ratings(frame: pd.DataFrame, winner_col: str) -> pd.Series:
    models = sorted(set(frame["model_a"]) | set(frame["model_b"]))
    model_to_idx = {model: i for i, model in enumerate(models)}
    a_idx = frame["model_a"].map(model_to_idx).to_numpy()
    b_idx = frame["model_b"].map(model_to_idx).to_numpy()
    outcomes = np.where(
        frame[winner_col].to_numpy() == "model_a",
        1.0,
        np.where(frame[winner_col].to_numpy() == "model_b", 0.0, 0.5),
    )

    def objective(ratings: np.ndarray) -> tuple[float, np.ndarray]:
        logits = math.log(10.0) * (ratings[a_idx] - ratings[b_idx])
        probs = np.clip(expit(logits), 1e-12, 1 - 1e-12)
        loss = -np.sum(outcomes * np.log(probs) + (1 - outcomes) * np.log(1 - probs))
        pair_grad = -math.log(10.0) * (outcomes - probs)
        grad = np.zeros_like(ratings)
        np.add.at(grad, a_idx, pair_grad)
        np.add.at(grad, b_idx, -pair_grad)
        return float(loss), grad

    fitted = minimize(
        objective,
        np.zeros(len(models), dtype=float),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 200, "gtol": 1e-7},
    ).x
    return pd.Series(fitted * 400 + 1000, index=models).sort_values(ascending=False)


def _winrate_matrix(frame: pd.DataFrame, winner_col: str) -> pd.DataFrame:
    models = sorted(set(frame["model_a"]) | set(frame["model_b"]))
    wins = pd.DataFrame(0.0, index=models, columns=models)
    totals = pd.DataFrame(0.0, index=models, columns=models)
    for row in frame.itertuples(index=False):
        a, b, winner = row.model_a, row.model_b, getattr(row, winner_col)
        totals.loc[a, b] += 1
        totals.loc[b, a] += 1
        if winner == "model_a":
            wins.loc[a, b] += 1
        elif winner == "model_b":
            wins.loc[b, a] += 1
        else:
            wins.loc[a, b] += 0.5
            wins.loc[b, a] += 0.5
    return wins / totals.replace(0, np.nan)


def _ppe_ranking_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    records = []
    for row in rows:
        predicted = row["prediction"]["predicted"]
        pred_winner = "model_a" if predicted == 0 else "model_b" if predicted == 1 else "tie"
        records.append(
            {
                "model_a": row["metadata"]["model_a"],
                "model_b": row["metadata"]["model_b"],
                "winner": row["metadata"]["winner"],
                "pred_winner": pred_winner,
            }
        )
    frame = pd.DataFrame.from_records(records)
    true_ratings = _bt_ratings(frame, "winner")
    pred_ratings = _bt_ratings(frame, "pred_winner")
    joined = pd.concat(
        [true_ratings.rename("true"), pred_ratings.rename("pred")], axis=1
    ).dropna()
    true_wr = _winrate_matrix(frame, "winner")
    pred_wr = _winrate_matrix(frame, "pred_winner")
    row_correlations = true_wr.corrwith(pred_wr, axis=1).dropna()
    return {
        "models": int(len(joined)),
        "spearman": float(spearmanr(joined["true"], joined["pred"]).statistic),
        "kendall_tau": float(kendalltau(joined["true"], joined["pred"]).statistic),
        "row_wise_pearson": float(row_correlations.mean()),
    }


def processbench_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reproduce ProcessBench's error/clean harmonic score per subset."""
    subsets: dict[str, Any] = {}
    for subset, group in sorted(_by(rows, "subset").items()):
        erroneous = [r for r in group if int(r["metadata"]["label"]) != -1]
        clean = [r for r in group if int(r["metadata"]["label"]) == -1]
        error_acc = mean(
            int(r["prediction"]["predicted"]) == int(r["metadata"]["label"])
            for r in erroneous
        ) if erroneous else None
        clean_acc = mean(int(r["prediction"]["predicted"]) == -1 for r in clean) if clean else None
        harmonic = (
            2 * error_acc * clean_acc / (error_acc + clean_acc)
            if error_acc is not None and clean_acc is not None and error_acc + clean_acc
            else 0.0
        )
        subsets[subset] = {
            "n": len(group),
            "error_accuracy": error_acc,
            "clean_accuracy": clean_acc,
            "f1_harmonic": harmonic,
        }
    return {
        "official_macro": mean(v["f1_harmonic"] for v in subsets.values()) if subsets else None,
        "exact_accuracy": mean(
            int(r["prediction"]["predicted"]) == int(r["metadata"]["label"]) for r in rows
        ) if rows else None,
        "subsets": subsets,
    }


def _prm_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    correct_step: list[float] = []
    wrong_step: list[float] = []
    total_step: list[float] = []
    first_error: list[float] = []
    exact: list[float] = []
    annotation_out_of_range = 0
    for row in rows:
        annotated_errors = set(map(int, row["metadata"]["error_steps"]))
        if row["metadata"]["classification"] in {"redundency", "circular"}:
            predicted_valid = [not bool(x) for x in row["prediction"]["redundancy_labels"]]
        else:
            predicted_valid = list(map(bool, row["prediction"]["validity_labels"]))
        actual_errors = {i for i in annotated_errors if 0 <= i < len(predicted_valid)}
        annotation_out_of_range += len(annotated_errors - actual_errors)
        predicted_errors = {i for i, valid in enumerate(predicted_valid) if not valid}
        exact.append(float(predicted_errors == actual_errors))
        if annotated_errors:
            first = min(annotated_errors)
            # A small number of preview annotations contain an additional
            # out-of-range error index.  The official scorer ignores those in
            # its per-step loop; guard the diagnostic the same way.
            if 0 <= first < len(predicted_valid):
                first_error.append(float(not predicted_valid[first]))
        for i, valid in enumerate(predicted_valid):
            truth_valid = i not in actual_errors
            total_step.append(float(valid == truth_valid))
            if truth_valid:
                correct_step.append(float(valid))
                if valid:
                    tp += 1
                else:
                    fn += 1
            else:
                wrong_step.append(float(not valid))
                if valid:
                    fp += 1
                else:
                    tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    negative_precision = tn / (tn + fn) if tn + fn else 0.0
    negative_recall = tn / (tn + fp) if tn + fp else 0.0
    negative_f1 = (
        2 * negative_precision * negative_recall / (negative_precision + negative_recall)
        if negative_precision + negative_recall else 0.0
    )
    return {
        "n": len(rows),
        "prm_score": 0.5 * (f1 + negative_f1),
        "f1": f1,
        "negative_f1": negative_f1,
        "precision": precision,
        "recall": recall,
        "negative_precision": negative_precision,
        "negative_recall": negative_recall,
        "correct_step_accuracy": mean(correct_step) if correct_step else None,
        "wrong_step_accuracy": mean(wrong_step) if wrong_step else None,
        "total_step_accuracy": mean(total_step) if total_step else None,
        "first_error_accuracy": mean(first_error) if first_error else None,
        "exact_trace_accuracy": mean(exact) if exact else None,
        "out_of_range_error_annotations": annotation_out_of_range,
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
    }


def prmbench_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = {key: _prm_stats(value) for key, value in sorted(_by(rows, "subset").items())}
    overall = _prm_stats(rows)
    overall["official_macro"] = overall["prm_score"]
    overall["classifications"] = by_type
    return overall


def _strict_pair_stats(pairs: list[tuple[float, float]]) -> dict[str, Any]:
    if not pairs:
        return {"n": 0, "accuracy": None, "tie_rate": None, "half_credit_accuracy": None}
    wins = sum(a > b for a, b in pairs)
    ties = sum(a == b for a, b in pairs)
    return {
        "n": len(pairs),
        "accuracy": wins / len(pairs),
        "tie_rate": ties / len(pairs),
        "half_credit_accuracy": (wins + 0.5 * ties) / len(pairs),
    }


def rm_bench_pointwise_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["metadata"]["prompt_id"])].append(row)
    matrices: list[tuple[str, np.ndarray]] = []
    incomplete = 0
    for group in groups.values():
        chosen = {int(r["metadata"]["style"]): float(r["prediction"]["reward"]) for r in group if r["metadata"]["preferred"]}
        rejected = {int(r["metadata"]["style"]): float(r["prediction"]["reward"]) for r in group if not r["metadata"]["preferred"]}
        if len(chosen) != 3 or len(rejected) != 3:
            incomplete += 1
            continue
        matrix = np.asarray([[chosen[i] > rejected[j] for j in range(3)] for i in range(3)], dtype=float)
        matrices.append((str(group[0]["metadata"]["domain"]), matrix))

    def summarize(items: list[np.ndarray]) -> dict[str, float] | None:
        if not items:
            return None
        matrix = np.mean(items, axis=0)
        return {
            "all": float(matrix.mean()),
            "hard": float(np.triu(matrix, 1).sum() / 3),
            "normal": float(np.diag(matrix).mean()),
            "easy": float(np.tril(matrix, -1).sum() / 3),
        }

    domains = {
        domain: summarize([matrix for d, matrix in matrices if d == domain])
        for domain in sorted({d for d, _ in matrices})
    }
    # The official implementation merges all `domain.startswith("safety")`
    # examples before forming the safety matrix (therefore prompt-weighted).
    safety = summarize([matrix for d, matrix in matrices if d.startswith("safety")])
    headline_domains = {d: domains[d] for d in ("chat", "code", "math") if d in domains}
    if safety is not None:
        headline_domains["safety"] = safety
    official = {
        key: mean(value[key] for value in headline_domains.values())
        for key in ("all", "hard", "normal", "easy")
    } if headline_domains else {}
    pairs = []
    for _, matrix in matrices:
        pairs.extend((float(v), 0.0) for v in matrix.flatten())
    return {
        "official_domain_macro": official.get("all"),
        "official_by_difficulty": official,
        "all_pairs_micro": float(np.mean([m.mean() for _, m in matrices])) if matrices else None,
        "domains": domains,
        "headline_domains": headline_domains,
        "complete_prompts": len(matrices),
        "incomplete_prompts": incomplete,
    }


def rmb_pairwise_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["metadata"]["group_id"])].append(row)
    records: list[tuple[str, str, float, float]] = []
    incomplete = 0
    for group in groups.values():
        preferred = [r for r in group if r["metadata"]["preferred"]]
        rejected = [r for r in group if not r["metadata"]["preferred"]]
        if len(preferred) != 1 or len(rejected) != 1:
            incomplete += 1
            continue
        records.append((str(group[0]["metadata"]["objective"]), str(group[0]["metadata"]["scenario"]),
                        float(preferred[0]["prediction"]["reward"]), float(rejected[0]["prediction"]["reward"])))
    overall = _strict_pair_stats([(a, b) for _, _, a, b in records])
    objectives = {key: _strict_pair_stats([(a, b) for o, _, a, b in records if o == key])
                  for key in sorted({o for o, _, _, _ in records})}
    scenarios = {key: _strict_pair_stats([(a, b) for _, s, a, b in records if s == key])
                 for key in sorted({s for _, s, _, _ in records})}
    return {"accuracy": overall["accuracy"], "overall": overall, "objectives": objectives,
            "scenario_macro": mean(v["accuracy"] for v in scenarios.values()) if scenarios else None,
            "scenarios": scenarios, "incomplete_pairs": incomplete}


def rmb_bon_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["metadata"]["group_id"])].append(row)

    def summarize(group_list: list[list[dict[str, Any]]]) -> dict[str, Any]:
        strict: list[float] = []
        fractional: list[float] = []
        reciprocal: list[float] = []
        for group in group_list:
            preferred = next(r for r in group if r["metadata"]["preferred"])
            preferred_score = float(preferred["prediction"]["reward"])
            scores = [float(r["prediction"]["reward"]) for r in group]
            max_score = max(scores)
            tied_max = sum(score == max_score for score in scores)
            strict.append(float(preferred_score == max_score and tied_max == 1))
            fractional.append(1.0 / tied_max if preferred_score == max_score else 0.0)
            rank = 1 + sum(score > preferred_score for score in scores)
            reciprocal.append(1.0 / rank)
        return {"n": len(group_list), "top1_accuracy": mean(strict) if strict else None,
                "fractional_top1": mean(fractional) if fractional else None,
                "mrr": mean(reciprocal) if reciprocal else None}

    complete = [g for g in groups.values() if sum(bool(r["metadata"]["preferred"]) for r in g) == 1]
    overall = summarize(complete)
    by_n = {str(n): summarize([g for g in complete if int(g[0]["metadata"]["candidate_count"]) == n])
            for n in sorted({int(g[0]["metadata"]["candidate_count"]) for g in complete})}
    objectives = {key: summarize([g for g in complete if g[0]["metadata"]["objective"] == key])
                  for key in sorted({str(g[0]["metadata"]["objective"]) for g in complete})}
    return {"accuracy": overall["top1_accuracy"], "overall": overall, "by_candidate_count": by_n,
            "objectives": objectives, "incomplete_groups": len(groups) - len(complete)}


def _binary_auc(truth: np.ndarray, score: np.ndarray) -> float | None:
    positives = int(truth.sum())
    negatives = len(truth) - positives
    if not positives or not negatives:
        return None
    ranks = rankdata(score, method="average")
    return float((ranks[truth].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def _ppe_correctness_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[int(row["metadata"]["row_index"])].append(row)
    ordered: list[list[dict[str, Any]]] = []
    for group in groups.values():
        if len(group) == 32:
            ordered.append(sorted(group, key=lambda r: int(r["metadata"]["response_index"])))
    normalized_scores: list[float] = []
    truths: list[bool] = []
    conflict_acc: list[float] = []
    rng = np.random.default_rng(20260920)
    reward_matrix: list[np.ndarray] = []
    truth_matrix: list[np.ndarray] = []
    for group in ordered:
        rewards = np.asarray([float(r["prediction"]["reward"]) for r in group])
        truth = np.asarray([bool(r["metadata"]["ground_truth"]) for r in group])
        reward_matrix.append(rewards)
        truth_matrix.append(truth.astype(float))
        spread = float(rewards.max() - rewards.min())
        normalized_scores.extend(((rewards - rewards.min()) / spread if spread else np.full(32, 0.5)).tolist())
        truths.extend(truth.tolist())
        checks = []
        for i, j in group[0]["metadata"].get("sampled_conflict_pairs", []):
            checks.append((truth[int(i)] > truth[int(j)]) == (rewards[int(i)] > rewards[int(j)]))
        if checks:
            conflict_acc.append(float(np.mean(checks)))
    trajectories: list[np.ndarray] = []
    oracle_trajectories: list[np.ndarray] = []
    if reward_matrix:
        rewards_all = np.asarray(reward_matrix)
        truth_all = np.asarray(truth_matrix)
        for _ in range(100):
            order = rng.permutation(32)
            sampled_rewards = rewards_all[:, order]
            sampled_truth = truth_all[:, order]
            selected_truth = []
            for reward_row, truth_row in zip(sampled_rewards, sampled_truth):
                # First maximum is numpy.argmax's tie policy, matching PPE's
                # cumulative_argmax helper.
                selected = [int(np.argmax(reward_row[: i + 1])) for i in range(32)]
                selected_truth.append(truth_row[selected])
            trajectories.append(np.mean(np.asarray(selected_truth), axis=0))
            oracle_trajectories.append(
                np.mean(np.maximum.accumulate(sampled_truth, axis=1), axis=0)
            )
    truth_array = np.asarray(truths, dtype=bool)
    score_array = np.asarray(normalized_scores, dtype=float)
    traj = np.mean(np.asarray(trajectories), axis=0) if trajectories else np.asarray([])
    oracle = np.mean(np.asarray(oracle_trajectories), axis=0) if oracle_trajectories else np.asarray([])
    ks = (1, 2, 4, 8, 16, 32)
    return {
        "accuracy": mean(bool(r["prediction"]["predicted"]) == bool(r["metadata"]["ground_truth"]) for r in rows) if rows else None,
        "area_under_curve": _binary_auc(truth_array, score_array) if len(truth_array) else None,
        "conflict_accuracy": mean(conflict_acc) if conflict_acc else None,
        "best_of_k": {
            "loss": float(np.mean((np.asarray(oracle_trajectories) - np.asarray(trajectories)) ** 2)) if trajectories else None,
            "mean_max_score": float(np.mean(np.max(np.asarray(trajectories), axis=1))) if trajectories else None,
            "mean_end_score": float(traj[-1]) if len(traj) else None,
            "selected_correctness": {str(k): float(traj[k - 1]) for k in ks} if len(traj) else {},
            "oracle_correctness": {str(k): float(oracle[k - 1]) for k in ks} if len(oracle) else {},
        },
        "complete_prompts": len(ordered),
        "incomplete_prompts": len(groups) - len(ordered),
    }


def ppe_correctness_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = _ppe_correctness_metrics(rows)
    model_names = sorted(
        {str(r["metadata"]["model_name"]) for r in rows if r["metadata"].get("model_name")}
    )
    if model_names:
        result["by_source_model"] = {
            name: _ppe_correctness_metrics(
                [r for r in rows if str(r["metadata"].get("model_name")) == name]
            )
            for name in model_names
        }
    return result


METRIC_FNS = {
    "rewardbench1": rewardbench1_metrics,
    "rewardbench2": rewardbench2_metrics,
    "rm_bench": rm_bench_metrics,
    "rubric_bench": rubric_bench_metrics,
    "ppe": ppe_metrics,
    "processbench": processbench_metrics,
    "prmbench": prmbench_metrics,
    "rm_bench_pointwise": rm_bench_pointwise_metrics,
    "rmb_pairwise": rmb_pairwise_metrics,
    "rmb_bon": rmb_bon_metrics,
    "ppe_mmlu_pro": ppe_correctness_metrics,
    "ppe_math": ppe_correctness_metrics,
    "ppe_gpqa": ppe_correctness_metrics,
    "ppe_ifeval": ppe_correctness_metrics,
    "ppe_mbpp_plus": ppe_correctness_metrics,
}


def build_report(raw_dir: Path) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for benchmark, metric_fn in METRIC_FNS.items():
        rows, errors = _read(raw_dir / f"{benchmark}.jsonl")
        if not rows and not errors:
            continue
        report[benchmark] = {
            "metrics": metric_fn(rows) if rows else {},
            "system": _system(rows, errors),
        }
    return report


def _pct(value: Any) -> str:
    return "—" if value is None else f"{100 * float(value):.2f}%"


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Jev 1.13 Reward Model Evaluation",
        "",
        "| Benchmark | Primary score | Completed | Input tokens | Est. Jev cost | p50 latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in report.items():
        metrics = result["metrics"]
        primary = next(
            (
                metrics[key]
                for key in (
                    "official_macro",
                    "official_domain_macro",
                    "prm_score",
                    "area_under_curve",
                    "accuracy",
                )
                if metrics.get(key) is not None
            ),
            None,
        )
        system = result["system"]
        latency = (
            f"{system['latency_p50_ms']:.0f} ms"
            if system["latency_p50_ms"] is not None
            else "—"
        )
        lines.append(
            f"| {name} | {_pct(primary)} | {system['successful']} | "
            f"{system['input_tokens']:,} | ${system['estimated_input_cost_usd']:.4f} | "
            f"{latency} |"
        )
    lines.extend(["", "## Detailed metrics", "", "```json", json.dumps(report, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="results/raw")
    parser.add_argument("--json", default="results/summary.json")
    parser.add_argument("--markdown", default="results/report.md")
    args = parser.parse_args()
    report = build_report(Path(args.raw_dir))
    json_path = Path(args.json)
    md_path = Path(args.markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    md_path.write_text(to_markdown(report))
    print(md_path)


if __name__ == "__main__":
    main()
