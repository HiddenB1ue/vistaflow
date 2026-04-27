from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.tasks.worker import build_worker_slot_id, normalize_worker_concurrency, run_consumer_loop


def test_normalize_worker_concurrency_enforces_minimum() -> None:
    assert normalize_worker_concurrency(-1) == 1
    assert normalize_worker_concurrency(0) == 1
    assert normalize_worker_concurrency(3) == 3


def test_build_worker_slot_id_adds_slot_suffix() -> None:
    assert build_worker_slot_id("host-100", 0) == "host-100-slot-1"
    assert build_worker_slot_id("host-100", 2) == "host-100-slot-3"


@pytest.mark.asyncio
async def test_run_consumer_loop_claims_and_executes_run_once() -> None:
    run_repo = AsyncMock()
    runner = AsyncMock()
    log_repo = AsyncMock()
    run = object()
    run_repo.claim_next_pending_run.return_value = run

    await run_consumer_loop(
        worker_id="worker-1-slot-1",
        run_repo=run_repo,
        runner=runner,
        log_repo=log_repo,
        poll_interval_seconds=0,
        stop_after_runs=1,
    )

    run_repo.claim_next_pending_run.assert_awaited_once_with("worker-1-slot-1")
    runner.execute.assert_awaited_once_with(run)
