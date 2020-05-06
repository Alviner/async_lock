import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from types import MappingProxyType
from typing import Type

from async_lock.base_lock import AsyncLocker, AsyncLock

log = logging.getLogger(__name__)


@unique
class LockMode(Enum):
    tr_immediately = "tr_immediately"
    sess_immediately = "sess_immediately"


class PgAdLock(AsyncLock, ABC):
    _LOCK_MODE = MappingProxyType(
        {
            LockMode.tr_immediately: "SELECT pg_try_advisory_xact_lock({:d});",
            LockMode.sess_immediately: "SELECT pg_try_advisory_lock({:d});",
        }
    )

    _RELEASE_MODE = MappingProxyType(
        {
            LockMode.tr_immediately: "SELECT True;",
            LockMode.sess_immediately: "SELECT pg_advisory_unlock({:d});",
        }
    )

    def __init__(
        self, *args, pool, mode: LockMode = LockMode.tr_immediately, **kwargs
    ):
        super(PgAdLock, self).__init__(*args, **kwargs)

        self._mode: LockMode = mode

        self._pool = pool

        self._lock = asyncio.Lock()

        self._conn = None

    @abstractmethod
    async def _acquire_resources(self):
        raise NotImplementedError

    @abstractmethod
    async def _release_resources(self):
        raise NotImplementedError

    @abstractmethod
    async def _acquire(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def _release(self) -> bool:
        raise NotImplementedError

    async def acquire(self) -> bool:
        async with self._lock:
            if not self._conn:
                await self._acquire_resources()
            log.debug("Try acquire lock %r", self._name)
            is_acquired = await self._acquire()
            log.debug("Acquire lock %r result: %r", self._name, is_acquired)
            if not is_acquired:
                await self._release_resources()
            return is_acquired

    async def release(self) -> bool:
        log.debug("Try release lock %r", self._name)
        if not self._conn:
            return False
        async with self._lock:
            is_released = await self._release()
            log.debug("Lock %r was released", self._name)
            await self._release_resources()
            return is_released


class PgAdLocker(AsyncLocker, ABC):
    LOCK_CLASS: Type[PgAdLock]

    def __init__(self, pool, **kwargs):
        super(PgAdLocker, self).__init__(**kwargs)
        self._pool = pool

    def _lock_name(self, name: str) -> int:
        """
            PostgreSQL requires lock id to be integers.
            Lets Hash the lock name to an integer.
        """
        l_name = super(PgAdLocker, self)._lock_name(name=name)
        return (
            int(hashlib.sha256(l_name.encode("utf-8")).hexdigest(), 16)
            % 10 ** 8
        )

    def lock(self, name: str, *args, **kwargs):
        return self.LOCK_CLASS(
            name=self._lock_name(name), pool=self._pool, *args, **kwargs
        )


class AsyncContextExit:
    __slots__ = ("_obj",)

    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        await self._obj.__aexit__(exc_type, exc, tb)
