import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Generic, TypeVar

import anyio
import redis.asyncio as redis
from config import (
    CONSUMER_NAME,
    GROUP_NAME,
    STATE_GROUP_NAME,
    STATE_STREAM_NAME,
    STREAM_NAME,
    get_redis_client,
)
from pydantic import BaseModel

logger = logging.getLogger("🧱")

SupportedType = int | float | str
T = TypeVar("T", bound=SupportedType)


class State(BaseModel, Generic[T]):
    data: T | None = None


@asynccontextmanager
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    try:
        yield (client := get_redis_client())
    finally:
        await client.aclose()


@dataclass
class RedisSubsystem(Generic[T]):
    name: str
    handler: Callable[[dict[str, Any]], T]
    state: State[T] = field(default_factory=lambda: State[T](data=None))
    state_updated: anyio.Event = field(default_factory=anyio.Event)

    async def process_input(self, input_data: dict[str, Any]) -> State[T]:
        logger.info(f"{self.name} processing input: {input_data}")
        processed_data = self.handler(input_data)
        return State[T](data=processed_data)

    async def send_output(self, output_data: State[T]) -> bool:
        logger.info(f"{self.name} sending output: {output_data}")
        async with redis_client() as client:
            try:
                await client.xadd(STREAM_NAME, {"data": output_data.model_dump_json()})
                return True
            except redis.ResponseError as e:
                logger.error(f"Error sending output: {e}")
                return False

    async def update_state(self):
        async with redis_client() as client:
            consumer_group = f"{STATE_GROUP_NAME}-{self.name}"
            try:
                await client.xgroup_create(
                    STATE_STREAM_NAME, consumer_group, "$", mkstream=True
                )
                logger.info(
                    f"Created consumer group '{consumer_group}' for state updates"
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.warning(
                        f"Consumer group '{consumer_group}' already exists for state updates"
                    )
                else:
                    raise

            while True:
                try:
                    messages = await asyncio.wait_for(
                        client.xreadgroup(
                            consumer_group,
                            self.name,
                            {STATE_STREAM_NAME: ">"},
                            count=1,
                            block=1,
                        ),
                        timeout=1,
                    )
                    if not messages:
                        continue

                    for _, message in messages:
                        for message_id, data in message:
                            logger.info(
                                f"{self.name} processing state update: {message_id}: {data}"
                            )
                            self.state = State[T].model_validate_json(data[b"data"])
                            logger.info(f"{self.name} updated state to: {self.state}")
                            await client.xack(
                                STATE_STREAM_NAME, consumer_group, message_id
                            )
                            await self.state_updated.set()

                except TimeoutError:
                    continue


@dataclass
class RedisAggregator(Generic[T]):
    merge_fn: Callable[[list[T]], T]

    state: State[T] = field(default_factory=lambda: State[T](data=None))

    async def _aggregate_outputs(self) -> State[T]:
        async with redis_client() as client:
            try:
                await client.xgroup_create(STREAM_NAME, GROUP_NAME, "$", mkstream=True)
                logger.info(f"Created consumer group '{GROUP_NAME}'")
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.warning(f"Consumer group '{GROUP_NAME}' already exists")
                else:
                    raise

            values = []
            while True:
                messages = await client.xreadgroup(
                    GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, count=10, block=1000
                )
                if not messages:
                    logger.info("No more messages to read")
                    break

                logger.info(f"Messages received: {messages}")
                for _, message in messages:
                    for message_id, data in message:
                        logger.info(f"Processing message {message_id}: {data}")
                        await client.xack(STREAM_NAME, GROUP_NAME, message_id)
                        message_data = State[T].model_validate_json(data[b"data"]).data
                        values.append(message_data)
                        logger.info(
                            f"Aggregated message {message_id} with value: {message_data}"
                        )

            aggregated_value = self.merge_fn(values)
            if inspect.iscoroutine(aggregated_value):
                aggregated_value = await aggregated_value

            logger.info(f"Aggregated value: {aggregated_value}")
            return State[T](data=aggregated_value)

    async def update_state(self):
        self.state = await self._aggregate_outputs()

        logger.info(f"Updating state with aggregated data: {self.state}")
        async with redis_client() as client:
            await client.xadd(STATE_STREAM_NAME, {"data": self.state.model_dump_json()})
