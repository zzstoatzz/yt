import asyncio
import logging
from typing import TypeVar

import anyio
from components import RedisAggregator, RedisSubsystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("🧱")

T = TypeVar("T", bound=int | float | str)


async def subsystem_task(subsystem: RedisSubsystem[T], value: T):
    assert await subsystem.send_output(
        await subsystem.process_input({"value": value})
    ), "Failed to send output"


async def main():
    subsystem_1 = RedisSubsystem[int](
        name="redis-subsystem-1",
        handler=lambda x: x.get("value", x),
    )
    subsystem_2 = RedisSubsystem[float](
        name="redis-subsystem-2",
        handler=lambda x: x.get("value", x),
    )
    aggregator = RedisAggregator[float](
        merge_fn=lambda values: sum(values) / len(values)
    )

    async with anyio.create_task_group() as tg:
        # Start subsystems' state update tasks
        tg.start_soon(subsystem_1.update_state)
        tg.start_soon(subsystem_2.update_state)

        # Send inputs to subsystems
        await asyncio.gather(
            subsystem_task(subsystem_1, 10),
            subsystem_task(subsystem_2, 3.14),
            subsystem_task(subsystem_1, 15),
            subsystem_task(subsystem_2, 2.71),
        )

        # Aggregate outputs and update state
        await aggregator.update_state()

        logger.info(f"Final aggregated value: {aggregator.state.data}")

        # Wait for subsystems to receive and process state updates
        await asyncio.gather(
            subsystem_1.state_updated.wait(),
            subsystem_2.state_updated.wait(),
        )

        # Log the updated state of subsystems
        logger.info(
            f"Subsystems now have the following states: {subsystem_1.state.data=}, {subsystem_2.state.data=}"
        )

        # Cancel the subsystems' state update tasks
        tg.cancel_scope.cancel()


asyncio.run(main())
