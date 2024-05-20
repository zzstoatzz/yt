import asyncio
import os

from event import Event
from redis.asyncio import Redis

worker_name = f"worker_{os.getpid()}"
redis = Redis(host="redis")


async def consume_events():
    print(f"Worker {worker_name} starting...")
    while True:
        try:
            events = await redis.xreadgroup(
                groupname="event_workers",
                consumername=worker_name,
                streams={"events": ">"},
                count=1,
            )
            if events:
                print(f"Events received: {events}")
                _, messages = events[0]
                event_id, event_data = messages[0]
                event = Event.model_validate(event_data)
                print(f"Event consumed: {event.model_dump_json(indent=2)}")
                await redis.xadd("processed_events", {"data": event.model_dump_json()})
                await redis.xack("events", "event_workers", event_id)
            else:
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error consuming events: {e}")
            await asyncio.sleep(1)


async def main():
    await consume_events()


if __name__ == "__main__":
    asyncio.run(main())
