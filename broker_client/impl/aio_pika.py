import asyncio
import json
import logging
from asyncio import IncompleteReadError

from aio_pika import Message
from aiormq import AMQPConnectionError
from pydantic import BaseModel

from ..abc import AbstractProducer, AbstractConsumer
from ..config import BaseBrokerSettings
from ..types import MessageHandler

import aio_pika


class AioPikaProducer(AbstractProducer):
    def __init__(self, connection: aio_pika.abc.AbstractConnection, channel: aio_pika.abc.AbstractChannel = None):
        self.connection = connection
        self.channel: aio_pika.abc.AbstractChannel | None = channel

    async def _get_channel(self):
        if not self.channel:
            self.channel = await self.connection.channel()
        return self.channel

    async def publish(self, message: BaseModel, routing_key: str) -> None:
        channel = await self._get_channel()
        body = message.model_dump_json().encode("utf-8")
        return await channel.default_exchange.publish(message=Message(body=body), routing_key=routing_key)

    @classmethod
    async def lazy(cls, settings: BaseBrokerSettings = None):
        settings: BaseBrokerSettings = settings or BaseBrokerSettings()
        connection = await aio_pika.connect_robust(settings.url_str)
        return cls(connection)


class AioPikaConsumer(AbstractConsumer):
    def __init__(self, connection: aio_pika.abc.AbstractConnection, channel: aio_pika.abc.AbstractChannel = None):
        self.connection = connection
        self.channel: aio_pika.abc.AbstractChannel | None = channel

    async def _get_channel(self):
        if not self.channel:
            self.channel = await self.connection.channel()
        return self.channel

    async def start_consuming(self, queue: str,
                              callback: MessageHandler,
                              auto_delete: bool = False,
                              requeue: bool = True,
                              reject_on_redelivered: bool = True) -> None:
        channel = await self._get_channel()
        q = await channel.declare_queue(queue, durable=True, auto_delete=auto_delete)
        while True:
            try:
                await q.consume(lambda msg: self._process_message(msg, callback, requeue, reject_on_redelivered))
                try:
                    await asyncio.Future()
                finally:
                    await self.connection.close()
            except (IncompleteReadError, AMQPConnectionError) as e:
                await asyncio.sleep(10)

    async def _process_message(self,
                               msg: aio_pika.IncomingMessage,
                               callback: MessageHandler,
                               requeue: bool,
                               reject_on_redelivered: bool) -> None:
        async with msg.process(requeue=requeue, reject_on_redelivered=reject_on_redelivered):
            try:
                payload = json.loads(msg.body.decode())
                await callback(payload)
            except Exception as e:
                logging.error(f"Error processing message: {e}")

    @classmethod
    async def lazy(cls, settings: BaseBrokerSettings = None):
        settings: BaseBrokerSettings = settings or BaseBrokerSettings()
        connection = await aio_pika.connect_robust(settings.url_str)
        return cls(connection)
