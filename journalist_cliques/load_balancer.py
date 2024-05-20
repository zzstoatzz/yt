from contextlib import asynccontextmanager

from event import Event
from fastapi import FastAPI
from redis.asyncio import Redis

redis = Redis(host="redis")


async def create_consumer_group_if_not_exists(stream: str, group: str):
    try:
        await redis.xgroup_create(stream, group, mkstream=True)
    except Exception as e:
        if "BUSYGROUP Consumer Group name already exists" not in str(e):
            raise e
        else:
            print("Consumer group already exists")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_consumer_group_if_not_exists("events", "event_workers")
        yield
    finally:
        await redis.aclose()


app = FastAPI(lifespan=lifespan)
redis = Redis(host="redis")


@app.post("/events")
async def receive_event(event: Event):
    await redis.xadd("events", {"data": event.model_dump_json()})
    print(f"Published event: {event.type} to stream: events")
    return {"message": "Event received"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
