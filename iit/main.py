import asyncio
import logging
from typing import Any, Generic, Protocol, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import to_json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ø")

T = TypeVar("T")


class State(BaseModel, Generic[T]):
    integrated_data: T = Field(...)
    model_config = ConfigDict(extra="allow")


class Subsystem(Protocol, Generic[T]):
    async def process_input(self, input_data: dict[str, Any]) -> T:
        ...

    async def send_output(self, output_data: T):
        ...


class Aggregator(Protocol, Generic[T]):
    async def aggregate_outputs(self) -> T:
        ...

    async def update_state(self, aggregated_data: T):
        ...

    async def distribute_state(self):
        ...


class RedisSubsystem(Subsystem[State[int]]):
    def __init__(self, name: str, redis_client: redis.Redis):
        self.name = name
        self.redis_client = redis_client
        logger.info(f"Initialized {self.name}")

    async def process_input(self, input_data: dict[str, Any]) -> State[int]:
        value = input_data.get("value", 0)
        logger.info(f"{self.name} processing input: {input_data} with value: {value}")
        return State(integrated_data=value)

    async def send_output(self, output_data: State[int]):
        logger.info(f"{self.name} sending output: {output_data}")
        await self.redis_client.xadd(
            "mystream", {"data": to_json(output_data.model_dump())}
        )


class RedisAggregator(Aggregator[State[int]]):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        logger.info("Initialized RedisAggregator")

    async def aggregate_outputs(self) -> State[int]:
        try:
            await self.redis_client.xgroup_create(
                "mystream", "mygroup", "$", mkstream=True
            )
            logger.info("Created consumer group 'mygroup'")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info("Consumer group 'mygroup' already exists")
            else:
                raise

        total = 0
        while True:
            messages = await self.redis_client.xreadgroup(
                "mygroup", "consumer1", {"mystream": ">"}, count=10, block=1000
            )
            if not messages:
                logger.info("No more messages to read")
                break

            logger.info(f"Messages received: {messages}")
            for stream, message in messages:
                for message_id, data in message:
                    logger.info(f"Processing message {message_id}: {data}")
                    await self.redis_client.xack("mystream", "mygroup", message_id)
                    message_data = (
                        State[int].model_validate_json(data[b"data"]).integrated_data
                    )
                    total += message_data
                    logger.info(
                        f"Aggregated message {message_id} with value: {message_data}"
                    )

        logger.info(f"Total aggregated value: {total}")
        return State(integrated_data=total)

    async def update_state(self, aggregated_data: State[int]):
        logger.info(f"Updating state with aggregated data: {aggregated_data}")
        await self.redis_client.set("state", aggregated_data.model_dump_json())

    async def distribute_state(self):
        state = await self.redis_client.get("state")
        logger.info(f"Distributing state: {state}")
        await self.redis_client.publish("state_channel", state)


async def subsystem_task(subsystem: RedisSubsystem, value: int):
    processed_data = await subsystem.process_input({"value": value})
    await subsystem.send_output(processed_data)


async def main():
    redis_client = redis.Redis()
    subsystem1 = RedisSubsystem(name="subsystem1", redis_client=redis_client)
    subsystem2 = RedisSubsystem(name="subsystem2", redis_client=redis_client)
    aggregator = RedisAggregator(redis_client=redis_client)

    # Run multiple subsystems with different values
    await asyncio.gather(
        subsystem_task(subsystem1, 10),
        subsystem_task(subsystem2, 20),
        subsystem_task(subsystem1, 15),
        subsystem_task(subsystem2, 5),
    )

    # Aggregator processes the inputs from subsystems
    aggregated_data = await aggregator.aggregate_outputs()
    await aggregator.update_state(aggregated_data)
    await aggregator.distribute_state()

    logger.info(f"Final aggregated value: {aggregated_data.integrated_data}")

    # Properly close the Redis client
    await redis_client.aclose()
    await redis_client.connection_pool.disconnect()


asyncio.run(main())
