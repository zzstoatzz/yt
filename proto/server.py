import asyncio
import logging
from collections import defaultdict

import chat_pb2
import chat_pb2_grpc
import grpc
from marvin.beta.assistants import Assistant, Thread

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ChatAssistant(Assistant):
    pass


assistant_threads: dict[str, Thread] = defaultdict(Thread)


class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = []

    async def JoinChat(self, request_iterator, context):
        self.clients.append(context)
        logger.debug(f"Client connected: {context.peer()}")

        async for message in request_iterator:
            logger.debug(f"Received message from {message.user}: {message.message}")
            response = await self.process_message(message)
            logger.debug(f"Sending response to {message.user}: {response}")
            await context.write(chat_pb2.ChatMessage(user="LLM", message=response))

            for client in self.clients:
                if client != context:
                    logger.debug(f"Broadcasting message to {client.peer()}")
                    await client.write(
                        chat_pb2.ChatMessage(user=message.user, message=message.message)
                    )

    async def process_message(self, message):
        user_thread = assistant_threads.get(message.user)
        if not user_thread:
            user_thread = Thread()
            assistant_threads[message.user] = user_thread

        await user_thread.add_async(message.message)

        await user_thread.run_async(ChatAssistant())
        return (await user_thread.get_messages_async())[-1].content[0].text.value


async def serve():
    server = grpc.aio.server()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    logger.info("Server started. Listening on port 50051.")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
