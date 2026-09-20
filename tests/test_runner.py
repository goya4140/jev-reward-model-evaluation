import asyncio

from jev_eval.benchmarks import Example
from jev_eval.client import JevBillingError
from jev_eval.runner import _run_one


class _BillingClient:
    async def evaluate(self, state, questions):
        raise JevBillingError("API returned 402: no credits")


def test_billing_failure_is_marked_fatal() -> None:
    example = Example("x", "1", "s", "prompt", ["a"], [], "ordinal_quality")
    row = asyncio.run(_run_one(_BillingClient(), example))
    assert row["status"] == "error"
    assert row["fatal"] is True
    assert row["error_type"] == "JevBillingError"
