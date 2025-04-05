import asyncio

import aio_pika
from pydantic import BaseModel

from broker_client import AioPikaProducer, AioPikaConsumer


class Task(BaseModel):
    data: int
    task_type: str = "type"
    priority: int = 1


async def handle_incoming_message(data: dict):
    task = Task(**data)
    print(f"Handling parsing task: {task}")


async def send_messages_task(producer, queue):
    for i in range(100):
        await producer.publish(
            Task(data=i),
            routing_key=queue
        )
        await asyncio.sleep(1)


async def main():
    queue_name = 'test_queue'

    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")

    producer = AioPikaProducer(connection=connection)
    consumer = AioPikaConsumer(connection=connection)

    await asyncio.gather(
        send_messages_task(producer=producer, queue=queue_name),
        consumer.start_consuming(queue=queue_name, callback=handle_incoming_message)
    )


if __name__ == '__main__':
    asyncio.run(main())
