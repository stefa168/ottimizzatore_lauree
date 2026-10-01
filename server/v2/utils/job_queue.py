"""
Postgres-backed queue for optimization jobs.

Each job is a row in ``optimization_jobs``. Workers claim jobs with ``SELECT ... FOR UPDATE SKIP LOCKED`` so a job
is handed to a single worker, and keep it alive with a heartbeat. A job whose heartbeat goes stale (e.g. the worker
process was killed) is put back in the queue, so jobs are not lost when a worker dies.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from v2.db.models import OptimizationJob, JobStatus, OptimizationConfiguration

logger = structlog.stdlib.get_logger()

# Path to the directories that hold the datfiles and solutions produced.
# Inside this directory there is a directory with this structure:
# temp
# |- [problem_id] - [config_id] --- cfg.dat
# |_ ...                         |_ model.lp
#                                |_ val.xls
OPT_TMP_DIR: Final = ".temp/"

HEARTBEAT_INTERVAL: Final = timedelta(seconds=15)
STALE_AFTER: Final = timedelta(minutes=2)
RETRY_BASE_DELAY: Final = timedelta(seconds=10)


def job_dir(session_id: int, config_id: int) -> Path:
    return (Path(OPT_TMP_DIR) / str(session_id) / str(config_id)).absolute()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def enqueue(session: AsyncSession | async_scoped_session[AsyncSession], config_id: int) -> OptimizationJob:
    """
    Adds a new job for the configuration to the session. The caller owns the transaction, so the job is committed
    together with whatever else the caller changed (e.g. the configuration's run_lock).
    """
    job = OptimizationJob(opt_config_id=config_id, status=JobStatus.QUEUED)
    session.add(job)
    return job


async def claim_next(session: AsyncSession, worker: str) -> OptimizationJob | None:
    """
    Claims the oldest available job, marking it as running. Concurrent workers skip rows already being claimed.
    """
    now = _now()
    job = (await session.execute(
        select(OptimizationJob)
        .where(OptimizationJob.status == JobStatus.QUEUED, OptimizationJob.available_at <= now)
        .order_by(OptimizationJob.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )).scalar_one_or_none()

    if job is None:
        await session.rollback()
        return None

    job.status = JobStatus.RUNNING
    job.attempts += 1
    job.worker = worker
    job.locked_at = now
    job.heartbeat_at = now
    await session.commit()
    return job


async def heartbeat(session: AsyncSession, job_id: int) -> None:
    await session.execute(
        update(OptimizationJob)
        .where(OptimizationJob.id == job_id, OptimizationJob.status == JobStatus.RUNNING)
        .values(heartbeat_at=_now())
    )
    await session.commit()


async def complete(session: AsyncSession, job_id: int) -> None:
    await session.execute(
        update(OptimizationJob)
        .where(OptimizationJob.id == job_id)
        .values(status=JobStatus.DONE, heartbeat_at=_now(), last_error=None)
    )
    await session.commit()


async def fail(session: AsyncSession, job_id: int, error: str, retry: bool = True) -> None:
    """
    Records a failed attempt. The job goes back in the queue (with an increasing delay) while it has attempts left
    and ``retry`` is set; otherwise it is marked as failed and the configuration is unlocked so it can be solved again.
    """
    job = await session.get(OptimizationJob, job_id, with_for_update=True)
    if job is None:
        # The configuration (and its jobs) has been deleted in the meantime.
        await session.rollback()
        return

    await _record_failure(session, job, error, retry)
    await session.commit()


async def requeue_stale(session: AsyncSession) -> int:
    """
    Recovers running jobs whose worker stopped sending heartbeats, e.g. because the process died.
    Returns the number of recovered jobs.
    """
    stale = (await session.execute(
        select(OptimizationJob)
        .where(OptimizationJob.status == JobStatus.RUNNING, OptimizationJob.heartbeat_at < _now() - STALE_AFTER)
        .with_for_update(skip_locked=True)
    )).scalars().all()

    for job in stale:
        logger.warning("Recovering stale optimization job", job_id=job.id, worker=job.worker, attempts=job.attempts)
        await _record_failure(session, job, f"Worker {job.worker} stopped responding", retry=True)

    await session.commit()
    return len(stale)


async def _record_failure(session: AsyncSession, job: OptimizationJob, error: str, retry: bool) -> None:
    job.last_error = error
    job.worker = None
    job.locked_at = None

    if retry and job.attempts < job.max_attempts:
        job.status = JobStatus.QUEUED
        job.available_at = _now() + RETRY_BASE_DELAY * (2 ** (job.attempts - 1))
        return

    job.status = JobStatus.FAILED
    # Release the configuration lock, so that the user can request a new optimization.
    await session.execute(
        update(OptimizationConfiguration)
        .where(OptimizationConfiguration.id == job.opt_config_id)
        .values(run_lock=False)
    )
