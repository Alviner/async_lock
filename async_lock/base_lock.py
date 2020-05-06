import logging
from abc import ABC, abstractmethod
from typing import ClassVar

log = logging.getLogger(__name__)


class LockAcquireFailure(Exception):
    pass


class AsyncLock(ABC):
    def __init__(self, name: str, *args, **kwargs):
        super(AsyncLock, self).__init__(*args, **kwargs)
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
    LOCK_CLASS: ClassVar[AsyncLock] = AsyncLock

    def __init__(self, app_name: str, **kwargs):
        self._app_name = app_name

    def _lock_name(self, name: str) -> str:
        return "{}.{}".format(self._app_name, name)

    def lock(self, name: str, *args, **kwargs):
        return self.LOCK_CLASS(name=self._lock_name(name), *args, **kwargs)


__all__ = (
    "LockAcquireFailure",
    "AsyncLock",
    "AsyncLocker",
)
