from __future__ import annotations

import asyncio
import signal
import threading
import time
from contextlib import asynccontextmanager, suppress
from multiprocessing import Process, Event, current_process
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from typing import Final, AsyncGenerator, Any

import structlog.stdlib
from litestar import Litestar
from litestar.datastructures import State

from v2.config.log_settings import LogSettings
from v2.config.settings import Settings, settings_path
from v2.db.models import OptimizationJob, OptimizationConfiguration
from v2.domain.grad_sessions.services import solver_wrapper
from v2.utils import job_queue

logger = structlog.stdlib.get_logger()

MANAGER_LIFESPAN_KEY: Final = "opt_manager"
POLL_INTERVAL: Final = 1.0  # seconds between queue polls when idle
STALE_CHECK_INTERVAL: Final = 30.0  # seconds between checks for jobs abandoned by dead workers


class OptimizationWorkersManager:
    processes: list[Process] = []
    _stop_event = Event()

    # keep settings for respawns
    _app_settings: Settings
    _max_workers: int

    # monitor thread & backoff
    _monitor_thread: threading.Thread | None = None
    _respawn_backoff: dict[int, float] = {}  # seconds, per worker index

    def __init__(self, app_settings_path: Path, max_workers=1):
        app_settings = Settings.from_yaml(app_settings_path)
        log_settings = app_settings.log

        # persist a plain-serializable version to pass to child processes
        self._log_settings_payload: dict[str, Any] | None = log_settings.model_dump() if log_settings else None

        # configure logging in the parent process
        self._configure_logging_from_payload(self._log_settings_payload)

        # keep settings for respawns
        self._app_settings: Settings = app_settings
        self._max_workers: int = max_workers

        self.start_workers(app_settings, max_workers)
        self._start_monitor()

    def _spawn_worker(self, idx: int) -> Process:
        """
        Create and start a single worker process, returning the Process.
        """
        logger.debug("Creating worker process", idx=idx)
        p = Process(
            target=OptimizationWorkersManager._worker_entry,
            args=(self._app_settings, self._stop_event, self._log_settings_payload),
            name=f"opt-worker-{idx + 1}",
            daemon=False,
        )
        p.start()
        logger.debug("Created process", pid=p.pid, worker=p.name)
        return p

    def start_workers(self, app_settings: Settings, num_workers: int):
        if len(self.processes) > 0:
            raise RuntimeError("Workers have been already started")

        for i in range(num_workers):
            p = self._spawn_worker(i)
            self.processes.append(p)
            self._respawn_backoff[i] = 1.0

    def _start_monitor(self) -> None:
        """
        Starts a supervisor thread that watches worker processes and respawns
        them if they die unexpectedly.
        """
        if self._monitor_thread is not None:
            return

        def _monitor():
            # Small initial delay to avoid racing with startup
            time.sleep(0.5)
            while not self._stop_event.is_set():
                try:
                    for idx, p in enumerate(list(self.processes)):
                        # Skip if list changed length or idx invalid
                        if idx >= len(self.processes):
                            continue

                        p = self.processes[idx]
                        if p is None:
                            continue

                        if not p.is_alive():
                            exitcode = p.exitcode
                            logger.error(
                                "Worker process exited; attempting restart",
                                worker=p.name,
                                pid=p.pid,
                                exitcode=exitcode,
                            )
                            # basic backoff to prevent tight crash loops
                            delay = max(1.0, self._respawn_backoff.get(idx, 1.0))
                            if delay > 1.0:
                                logger.info("Backoff before respawn", seconds=delay, worker_index=idx)
                            # Sleep in small slices so we can react to stop_event promptly
                            slept = 0.0
                            slice_s = 0.2
                            while slept < delay and not self._stop_event.is_set():
                                time.sleep(slice_s)
                                slept += slice_s

                            if self._stop_event.is_set():
                                break

                            # Respawn and replace in-place
                            new_p = self._spawn_worker(idx)
                            self.processes[idx] = new_p
                            # Exponential backoff up to 60 seconds if the new one crashes again
                            self._respawn_backoff[idx] = min(delay * 2.0, 60.0)
                            logger.info(
                                "Worker restarted",
                                worker=new_p.name,
                                new_pid=new_p.pid,
                                index=idx,
                                next_backoff=self._respawn_backoff[idx],
                            )
                        else:
                            # When a worker stays healthy, gradually reset the backoff
                            if self._respawn_backoff.get(idx, 1.0) > 1.0:
                                # decay backoff slowly
                                self._respawn_backoff[idx] = max(1.0, self._respawn_backoff[idx] * 0.5)
                    # Polling interval
                    time.sleep(1.0)
                except Exception:
                    logger.exception("Monitor thread encountered an error")
                    # Avoid tight loop if monitoring fails repeatedly
                    time.sleep(2.0)

        self._monitor_thread = threading.Thread(target=_monitor, name="opt-workers-monitor", daemon=True)
        self._monitor_thread.start()
        logger.debug("Started workers monitor thread", thread=self._monitor_thread.name)

    def stop_workers(self):
        logger.debug("Sending stop signal to workers")
        self._stop_event.set()

        # Stop monitor first so it doesn't spawn new workers while we're shutting down
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.debug("Joining monitor thread")
            self._monitor_thread.join(timeout=5)

        for p in list(self.processes):
            if p is None:
                continue
            logger.debug("Joining worker", worker=p.name, pid=p.pid)
            p.join(timeout=5)
            if p.is_alive():
                logger.warning("Worker still alive after timeout, terminating", worker=p.name, pid=p.pid)
                p.terminate()

        logger.debug("Terminated all worker processes", count=len(self.processes))
        self.processes.clear()

    @staticmethod
    def _configure_logging_from_payload(payload: dict[str, Any] | None) -> None:
        """
        Configure structlog + stdlib logging for the current process,
        using LogSettings serialized payload.
        """
        try:
            ls = LogSettings.model_validate(payload) if payload else LogSettings()
            # Apply Structlog / stdlib config (Litestar-compatible)
            structlog_cfg = ls.structlog_config().structlog_logging_config
            structlog_cfg.configure()
        except Exception:
            # As a safeguard, avoid breaking the process on logging config errors.
            # Fall back to the default structlog setup.
            structlog.stdlib.get_logger().warning("Failed to apply LogSettings; using default logging")

    @staticmethod
    def _worker_entry(
            app_settings: Settings,
            stop_event: EventType,
            log_settings_payload: dict[str, Any] | None
    ) -> None:
        """
        Synchronous entry-point executed by multiprocessing.Process.
        Spins up an event loop and runs the *real* async worker inside it.
        """
        # Configure logging in the child process before doing anything else
        OptimizationWorkersManager._configure_logging_from_payload(log_settings_payload)

        # Child must not die on Ctrl-C coming from the terminal
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        try:
            asyncio.run(OptimizationWorkersManager._async_worker(app_settings, stop_event, log_settings_payload))
        except Exception:
            # Log any unhandled exceptions at the top level so we know why the worker died
            structlog.stdlib.get_logger().exception("Worker crashed with an unhandled exception")
            # Re-raise to ensure non-zero exit code (supervisor will see and respawn)
            raise

    @staticmethod
    async def _async_worker(app_settings: Settings, stop_event: EventType, log_settings_payload: dict[str, Any] | None):
        OptimizationWorkersManager._configure_logging_from_payload(log_settings_payload)

        # noinspection PyShadowingNames
        logger = structlog.stdlib.get_logger()
        db_conf = app_settings.db.config()
        worker_name = f"{current_process().name}:{current_process().pid}"

        loop = asyncio.get_running_loop()
        loop.set_exception_handler(lambda _loop, ctx: logger.error("Unhandled task exception", exc_info=ctx.get("exception")))

        last_stale_check = 0.0
        try:
            while not stop_event.is_set():
                try:
                    if time.monotonic() - last_stale_check >= STALE_CHECK_INTERVAL:
                        last_stale_check = time.monotonic()
                        async with db_conf.get_session() as db_session:
                            await job_queue.requeue_stale(db_session)

                    async with db_conf.get_session() as db_session:
                        job = await job_queue.claim_next(db_session, worker_name)

                    if job is None:
                        await asyncio.sleep(POLL_INTERVAL)
                        continue

                    await OptimizationWorkersManager._run_job(db_conf, job)

                except Exception:
                    # Errors while talking to the queue (e.g. the database is down): wait and try again
                    logger.exception("Error while polling the optimization queue")
                    await asyncio.sleep(POLL_INTERVAL)
        finally:
            logger.info("Shutting down")
            await db_conf.get_engine().dispose()

    @staticmethod
    async def _run_job(db_conf, job: OptimizationJob) -> None:
        logg = structlog.stdlib.get_logger().bind(job_id=job.id, opt_id=job.opt_config_id, attempt=job.attempts)
        logg.info("Claimed optimization job")

        async def _heartbeat():
            while True:
                await asyncio.sleep(job_queue.HEARTBEAT_INTERVAL.total_seconds())
                try:
                    async with db_conf.get_session() as hb_session:
                        await job_queue.heartbeat(hb_session, job.id)
                except Exception:
                    logg.exception("Failed to send job heartbeat")

        heartbeat_task = asyncio.create_task(_heartbeat())
        try:
            async with db_conf.get_session() as db_session:
                config = await db_session.get(OptimizationConfiguration, job.opt_config_id)
                session_id = config.session_id if config is not None else None

            if session_id is None:
                ok, error, retry = False, "Configuration no longer exists", False
            else:
                cc_path = job_queue.job_dir(session_id, job.opt_config_id)
                # A False result means the solver ran but produced no usable solution: retrying would give the
                # same outcome, so only unexpected exceptions are retried.
                ok = await solver_wrapper(db_conf, job.opt_config_id, session_id, cc_path)
                error, retry = "Solver did not produce a solution", False
        except Exception as e:
            logg.exception("Optimization job raised an exception")
            ok, error, retry = False, f"{type(e).__name__}: {e}", True
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

        async with db_conf.get_session() as db_session:
            if ok:
                await job_queue.complete(db_session, job.id)
                logg.info("Optimization job completed")
            else:
                await job_queue.fail(db_session, job.id, error, retry=retry)
                logg.warning("Optimization job failed", error=error, will_retry=retry)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop_workers()

    @staticmethod
    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
        async with OptimizationWorkersManager(settings_path) as manager:
            app.state[MANAGER_LIFESPAN_KEY] = manager
            yield

    @staticmethod
    async def provide(state: State) -> AsyncGenerator[OptimizationWorkersManager, None]:
        manager = state.get(MANAGER_LIFESPAN_KEY)
        if manager is None:
            raise RuntimeError("Optimization Processes Manager is missing in app State")

        return manager
