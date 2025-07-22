from __future__ import annotations

import asyncio
import signal
from contextlib import asynccontextmanager
from dataclasses import dataclass
from multiprocessing import Process, Event
from pathlib import Path
from typing import Final, AsyncGenerator

import aio_pika
import structlog.stdlib
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection, AbstractRobustChannel, AbstractRobustQueue
from litestar import Litestar
from litestar.datastructures import State

from v2.config.settings import Settings, settings_path

logger = structlog.stdlib.get_logger()

MANAGER_LIFESPAN_KEY: Final = "opt_manager"
PIKA_LIFETIME_KEY: Final = "pika"
OPTIMIZATION_CHANNEL_NAME: Final = "optimization"


class OptimizationWorkersManager:
    processes: list[Process] = []
    stop_event = Event()

    def __init__(self, app_settings_path: Path, max_workers=1):
        app_settings = Settings.from_yaml(app_settings_path)
        self.start_workers(app_settings, max_workers)

    def start_workers(self, app_settings: Settings, num_workers: int):
        if len(self.processes) > 0:
            raise RuntimeError("Workers have been already started")

        for i in range(num_workers):
            logger.debug("Creating worker process", idx=i)
            p = Process(
                target=OptimizationWorkersManager._worker_entry,
                args=(app_settings, self.stop_event),
                name=f"opt-worker-{i + 1}",
                daemon=False)
            p.start()
            self.processes.append(p)

    def stop_workers(self):
        logger.debug("Sending stop signal to workers")
        self.stop_event.set()
        for p in self.processes:
            logger.debug("Joining worker", worker=p.name)
            p.join(timeout=5)
            if p.is_alive():
                logger.warning("Worker still alive after timeout, terminating", worker=p.name)
                p.terminate()
        logger.debug("Terminated all worker processes", count=len(self.processes))

    @staticmethod
    def _worker_entry(app_settings: Settings, stop_event: Event) -> None:
        """
        Synchronous entry-point executed by multiprocessing.Process.
        Spins up an event loop and runs the *real* async worker inside it.
        """
        # Child must not die on Ctrl-C coming from the terminal
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        asyncio.run(OptimizationWorkersManager._async_worker(app_settings, stop_event))

    @staticmethod
    async def _async_worker(app_settings: Settings, stop_event: Event):
        # noinspection PyShadowingNames
        logger = structlog.stdlib.get_logger()

        async with await RabbitMessaging.create(app_settings) as mq:
            async def test(message: AbstractIncomingMessage):
                logger.info("Got a message", info=message.info())
                await message.ack()

            await mq.opt_queue.consume(test)
            # await stop_event.wait()
            loop = asyncio.get_running_loop()

            # turn the multiprocessing.Event into an awaitable
            await loop.run_in_executor(None, stop_event.wait)
            logger.info("Shutting down")

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


@dataclass
class RabbitMessaging:
    """
    Handles messaging with RabbitMQ.

    This class provides utilities to handle connections, channels, and queue
    declarations with RabbitMQ using aio-pika, enabling robust messaging for async
    applications. It includes methods for resource management, particularly through
    asynchronous context management.

    :ivar connection: Represents the robust connection to RabbitMQ.
    :type connection: AbstractRobustConnection
    :ivar channel: Represents the robust channel for communication in RabbitMQ.
    :type channel: AbstractRobustChannel
    :ivar opt_queue: Represents the declared queue for optimization tasks.
    :type opt_queue: AbstractRobustQueue
    """
    connection: AbstractRobustConnection
    channel: AbstractRobustChannel
    opt_queue: AbstractRobustQueue

    @classmethod
    async def create(cls, settings: Settings) -> RabbitMessaging:
        # todo add configuration
        connection = await aio_pika.connect_robust("amqp://localhost/")

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        opt_queue = await channel.declare_queue(name=OPTIMIZATION_CHANNEL_NAME, durable=True)

        return cls(connection, channel, opt_queue)

    async def close(self):
        await self.channel.close()
        await self.connection.close()

    async def __aenter__(self) -> RabbitMessaging:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @staticmethod
    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
        async with await RabbitMessaging.create(app.state.get("settings")) as pika:
            app.state[PIKA_LIFETIME_KEY] = pika
            yield

    @staticmethod
    async def provide(state: State) -> AsyncGenerator[RabbitMessaging, None]:
        pika = state.get(PIKA_LIFETIME_KEY)
        if pika is None:
            raise RuntimeError("Pika is missing in app State")

        return pika
