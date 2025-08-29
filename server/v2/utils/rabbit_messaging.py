from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass

from typing import Final, AsyncGenerator

import aio_pika
import structlog
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractRobustQueue
from litestar import Litestar
from litestar.datastructures import State

from v2.config.settings import Settings

PIKA_LIFETIME_KEY: Final = "pika"
OPTIMIZATION_CHANNEL_NAME: Final = "optimization"

logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger()


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
        # Toggle robust vs non-robust via env for debugging.
        # Set MQ_DEBUG_NO_ROBUST=1 to see clean, direct exceptions without auto-recovery noise.
        debug_no_robust = os.getenv("MQ_DEBUG_NO_ROBUST", "0") == "1"
        debug_no_robust = True

        # todo add configuration
        if debug_no_robust:
            connection = await aio_pika.connect("amqp://localhost/")
        else:
            # You can also tune heartbeat and reconnect interval here if needed:
            connection = await aio_pika.connect_robust("amqp://localhost/")

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        opt_queue = await channel.declare_queue(name=OPTIMIZATION_CHANNEL_NAME, durable=True)

        return cls(connection, channel, opt_queue)  # type: ignore

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
        async with await RabbitMessaging.create(app.state["settings"]) as pika:
            app.state[PIKA_LIFETIME_KEY] = pika
            yield

    @staticmethod
    async def provide(state: State) -> AsyncGenerator[RabbitMessaging, None]:
        pika = state.get(PIKA_LIFETIME_KEY)
        if pika is None:
            raise RuntimeError("Pika is missing in app State")

        return pika
