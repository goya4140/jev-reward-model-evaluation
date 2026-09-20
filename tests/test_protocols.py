from jev_eval.benchmarks import Example
from jev_eval.protocols import build_request, parse_prediction


def test_pairwise_protocol() -> None:
    example = Example("x", "1", "s", "p", ["a", "b"], [0], "pairwise")
    state, questions = build_request(example)
    assert state["responses"] == {"A": "a", "B": "b"}
    assert set(questions["preference"]["criteria"]) == {"A", "B"}
    parsed = parse_prediction(
        example,
        {
            "preference": {
                "choice": "A",
                "probabilities": {"A": 0.8, "B": 0.2},
                "confidence": 0.6,
            }
        },
    )
    assert parsed["predicted"] == 0
    assert parsed["probabilities"]["0"] == 0.8


def test_rm_grid_has_nine_questions() -> None:
    example = Example(
        "rm_bench",
        "1",
        "chat",
        "p",
        [str(i) for i in range(6)],
        [0, 1, 2],
        "rm_style_grid",
        metadata={"grid_pairs": [[i, j] for i in range(3) for j in range(3, 6)]},
    )
    _, questions = build_request(example)
    assert len(questions) == 9


def test_ratings_parse() -> None:
    example = Example("rb2", "1", "Ties", "p", ["a", "b"], [0], "ratings")
    answers = {
        "quality_0": {"score": 3.5, "confidence": 0.8},
        "quality_1": {"score": 1.0, "confidence": 0.9},
    }
    parsed = parse_prediction(example, answers)
    assert parsed["predicted"] == 0
    assert parsed["scores"] == [3.5, 1.0]


def test_process_first_error_protocol() -> None:
    example = Example("processbench", "1", "math", "p", ["s0", "s1"], [1], "process_first_error")
    state, questions = build_request(example)
    assert set(state["reasoning_steps"]) == {"STEP_0", "STEP_1"}
    assert set(questions["first_error"]["criteria"]) == {"CLEAN", "STEP_0", "STEP_1"}
    parsed = parse_prediction(
        example,
        {
            "first_error": {
                "choice": "STEP_1",
                "probabilities": {"CLEAN": 0.1, "STEP_0": 0.2, "STEP_1": 0.7},
                "confidence": 0.8,
            }
        },
    )
    assert parsed["predicted"] == 1


def test_ordinal_quality_expected_reward() -> None:
    example = Example("rm_bench_pointwise", "1", "chat", "p", ["a"], [], "ordinal_quality")
    _, questions = build_request(example)
    assert set(questions["quality"]["criteria"]) == {"Q0", "Q1", "Q2", "Q3", "Q4"}
    parsed = parse_prediction(
        example,
        {
            "quality": {
                "choice": "Q3",
                "probabilities": {"Q0": 0.0, "Q1": 0.0, "Q2": 0.2, "Q3": 0.5, "Q4": 0.3},
                "confidence": 0.7,
            }
        },
    )
    assert parsed["reward"] == 3.1


def test_prm_step_protocol() -> None:
    example = Example("prmbench", "1", "circular", "p", ["s0"], [0], "prm_steps")
    _, questions = build_request(example)
    assert set(questions) == {"validity_0", "redundancy_0"}
    parsed = parse_prediction(
        example,
        {
            "validity_0": {
                "choice": "VALID",
                "probabilities": {"VALID": 0.7, "INVALID": 0.3},
                "confidence": 0.6,
            },
            "redundancy_0": {
                "choice": "REDUNDANT",
                "probabilities": {"NECESSARY": 0.1, "REDUNDANT": 0.9},
                "confidence": 0.8,
            },
        },
    )
    assert parsed["redundancy_labels"] == [True]
    assert parsed["invalid_probabilities"] == [0.3]
