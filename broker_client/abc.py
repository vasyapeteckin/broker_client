from abc import ABC, abstractmethod
from .types import MessageHandler
from pydantic import BaseModel


class AbstractProducer(ABC):
    @abstractmethod
    async def publish(self, message: BaseModel, routing_key: str) -> None:
        ...


class AbstractConsumer(ABC):
    @abstractmethod
    async def start_consuming(self, queue: str, callback: MessageHandler) -> None:
        ...
