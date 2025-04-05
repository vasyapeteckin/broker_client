from typing import Callable, Awaitable, Dict, Any

MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]
