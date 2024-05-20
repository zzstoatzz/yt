import asyncio
import random
from datetime import datetime

from httpx import AsyncClient


async def post_events():
    async with AsyncClient(base_url="http://localhost:8001") as client:
        while True:
            event_data = dict(
                id=str(random.randint(1, 1000)),
                timestamp=datetime.now().isoformat(),
                type=random.choice(
                    ["user_registered", "order_placed", "payment_processed"]
                ),
                data={"key": "value"},
            )

            try:
                response = await client.post("/events", json=event_data)
                response.raise_for_status()
                print(f"Event posted: {event_data}")
            except Exception as e:
                print(f"Error posting event: {e}")

            await asyncio.sleep(random.uniform(0.5, 2.0))


async def main():
    try:
        await post_events()
    except asyncio.CancelledError:
        print("\nShutting down...")
        return


if __name__ == "__main__":
    asyncio.run(main())
