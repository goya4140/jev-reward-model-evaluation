from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .benchmarks import LOADERS, Example
from .client import JevBillingError, JevClient
from .protocols import build_request, parse_prediction


def _read_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open() as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") == "ok":
                completed.add(row["example_id"])
    return completed


def _record(example: Example, result: Any) -> dict[str, Any]:
    prediction = parse_prediction(example, result.answers)
    if example.mode == "rm_style_grid":
        correct = all(prediction["grid_correct"])
    elif example.mode == "prm_steps":
        if example.subset in {"redundency", "circular"}:
            predicted_errors = {
                i for i, label in enumerate(prediction["redundancy_labels"]) if label
            }
        else:
            predicted_errors = {
                i for i, label in enumerate(prediction["validity_labels"]) if not label
            }
        correct = predicted_errors == set(example.correct)
    elif example.mode == "ordinal_quality":
        correct = None
    elif example.mode == "pairwise_tie" and len(example.correct) == 2:
        correct = prediction["predicted"] == -1
    else:
        correct = prediction["predicted"] in example.correct
    return {
        "status": "ok",
        "benchmark": example.benchmark,
        "example_id": example.example_id,
        "subset": example.subset,
        "mode": example.mode,
        "correct_indices": example.correct,
        "candidate_count": len(example.candidates),
        "prediction": prediction,
        "correct": None if correct is None else bool(correct),
        "metadata": example.metadata,
        "model": result.model,
        "usage": result.usage,
        "latency_ms": result.latency_ms,
    }


async def _run_one(client: JevClient, example: Example) -> dict[str, Any]:
    try:
        state, questions = build_request(example)
        result = await client.evaluate(state, questions)
        return _record(example, result)
    except Exception as exc:
        return {
            "status": "error",
            "benchmark": example.benchmark,
            "example_id": example.example_id,
            "subset": example.subset,
            "mode": example.mode,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "fatal": isinstance(exc, JevBillingError),
        }


async def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client = JevClient(model=args.model, concurrency=args.concurrency)
    try:
        for benchmark in args.benchmarks:
            print(f"Loading {benchmark}...", flush=True)
            examples = LOADERS[benchmark]()
            if args.shuffle:
                random.Random(args.seed).shuffle(examples)
            if args.limit is not None:
                examples = examples[: args.limit]

            output_path = output_dir / f"{benchmark}.jsonl"
            completed = _read_completed(output_path) if args.resume else set()
            pending = [ex for ex in examples if ex.example_id not in completed]
            print(
                f"{benchmark}: {len(examples)} selected, {len(completed)} completed, "
                f"{len(pending)} pending",
                flush=True,
            )
            if not pending:
                continue

            work_queue: asyncio.Queue[Example | None] = asyncio.Queue(
                maxsize=max(args.concurrency * 4, 16)
            )
            result_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

            async def produce() -> None:
                for example in pending:
                    await work_queue.put(example)
                for _ in range(args.concurrency):
                    await work_queue.put(None)

            async def worker() -> None:
                while True:
                    example = await work_queue.get()
                    if example is None:
                        work_queue.task_done()
                        return
                    row = await _run_one(client, example)
                    await result_queue.put(row)
                    work_queue.task_done()

            producer = asyncio.create_task(produce())
            workers = [asyncio.create_task(worker()) for _ in range(args.concurrency)]
            with output_path.open("a") as handle:
                for _ in tqdm(range(len(pending)), total=len(pending), desc=benchmark):
                    row = await result_queue.get()
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    result_queue.task_done()
                    if row.get("fatal"):
                        producer.cancel()
                        for task in workers:
                            task.cancel()
                        await asyncio.gather(producer, *workers, return_exceptions=True)
                        raise JevBillingError(row["error"])
            await producer
            await work_queue.join()
            await asyncio.gather(*workers)
    finally:
        await client.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmarks",
        nargs="+",
        choices=sorted(LOADERS),
        default=list(LOADERS),
    )
    parser.add_argument("--model", default="jev-1.13.0")
    parser.add_argument("--output-dir", default="results/raw")
    parser.add_argument("--concurrency", type=int, default=24)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=20260920)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.set_defaults(resume=True)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(run(args))
    except JevBillingError as exc:
        print(f"Run stopped: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except KeyboardInterrupt:
        print("Interrupted; completed rows are resumable.", file=sys.stderr)
        raise SystemExit(130)


if __name__ == "__main__":
    main()
