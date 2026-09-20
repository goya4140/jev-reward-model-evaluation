from jev_eval.report import (
    processbench_metrics,
    prmbench_metrics,
    rm_bench_pointwise_metrics,
    rmb_pairwise_metrics,
)


def test_processbench_harmonic_macro():
    rows = [
        {"subset": "x", "metadata": {"label": -1}, "prediction": {"predicted": -1}},
        {"subset": "x", "metadata": {"label": 0}, "prediction": {"predicted": 0}},
    ]
    assert processbench_metrics(rows)["official_macro"] == 1.0


def test_prmbench_perfect_score():
    rows = [{
        "subset": "step_contradiction",
        "metadata": {"classification": "step_contradiction", "error_steps": [1]},
        "prediction": {"validity_labels": [True, False, True], "redundancy_labels": [False] * 3},
    }]
    result = prmbench_metrics(rows)
    assert result["prm_score"] == 1.0
    assert result["first_error_accuracy"] == 1.0


def test_rm_bench_reconstructs_nine_pairs():
    rows = []
    for preferred, prefix, base in ((True, "chosen", 3.0), (False, "rejected", 0.0)):
        for style in range(3):
            rows.append({
                "metadata": {"prompt_id": "p", "preferred": preferred, "style": style, "domain": "chat"},
                "prediction": {"reward": base + style / 10},
            })
    result = rm_bench_pointwise_metrics(rows)
    assert result["all_pairs_micro"] == 1.0
    assert result["complete_prompts"] == 1


def test_rmb_pairwise_strict_tie_policy():
    rows = [
        {"metadata": {"group_id": "g", "preferred": True, "objective": "o", "scenario": "s"},
         "prediction": {"reward": 2.0}},
        {"metadata": {"group_id": "g", "preferred": False, "objective": "o", "scenario": "s"},
         "prediction": {"reward": 2.0}},
    ]
    result = rmb_pairwise_metrics(rows)
    assert result["accuracy"] == 0.0
    assert result["overall"]["half_credit_accuracy"] == 0.5
