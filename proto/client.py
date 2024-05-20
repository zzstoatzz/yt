import asyncio
import logging
import os

import chat_pb2
import chat_pb2_grpc
import grpc

logging.basicConfig(level=logging.INFO if not os.getenv("DEBUG") else logging.DEBUG)
logger = logging.getLogger(__name__)


async def join_chat():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)

        user_name = input("Enter your name: ")

        stream = stub.JoinChat()
        logger.debug(f"Connected to server: {channel}")

        while True:
            message = input(f"{user_name}: ")
            logger.debug(f"Sending message: {message}")
            await stream.write(chat_pb2.ChatMessage(user=user_name, message=message))

            response = await stream.read()
            logger.debug(f"Received message from {response.user}: {response.message}")
            print(f"{response.user}: {response.message}")


if __name__ == "__main__":
    asyncio.run(join_chat())
