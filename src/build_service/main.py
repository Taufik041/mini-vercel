import asyncio
import json
import os

import aio_pika


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        json.loads(message.body)


async def main():
    while True:
        try:
            connection = await aio_pika.connect(os.environ["RABBITMQ_URL"])
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("build_jobs", durable=True)
                await queue.consume(handle_message)
                await asyncio.Future()
        except Exception:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
