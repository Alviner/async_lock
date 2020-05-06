import logging
from abc import ABC, abstractmethod
from typing import Type, Any

log = logging.getLogger(__name__)


class LockAcquireFailure(Exception):
    pass


class AsyncLock(ABC):
    def __init__(self, name: str):
        self._name = name

    @abstractmethod
    async def acquire(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def release(self) -> bool:
        raise NotImplementedError

    async def __aenter__(self):
        if not await self.acquire():
            raise LockAcquireFailure
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.release()


class AsyncLocker:
    LOCK_CLASS: Type = AsyncLock

    def __init__(self, app_name: str):
        self._app_name = app_name

    def _lock_name(self, name: str) -> Any:
        return "{}.{}".format(self._app_name, name)

    def lock(self, name: str):
        return self.LOCK_CLASS(name=self._lock_name(name))


__all__ = (
    "LockAcquireFailure",
    "AsyncLock",
    "AsyncLocker",
)
