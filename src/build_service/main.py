import asyncio
import aio_pika
import os
import json


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        print(f"Received build job: {data}")


async def main():
    while True:
        try:
            connection = await aio_pika.connect(os.environ["RABBITMQ_URL"])
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("build_jobs", durable=True)
                await queue.consume(handle_message)
                print("Build service waiting for jobs...")
                await asyncio.Future()
        except Exception as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
