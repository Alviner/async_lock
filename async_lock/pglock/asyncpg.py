import logging

from asyncpg.connection import Connection
from asyncpg.transaction import Transaction

from async_lock.pglock.pg_base import PgAdLock, PgAdLocker, AsyncContextExit

log = logging.getLogger(__name__)


class AsyncPgAdLock(PgAdLock):
    def __init__(self, *args, **kwargs):
        super(AsyncPgAdLock, self).__init__(*args, **kwargs)
        self._tr = None

    async def _acquire_resources(self):
        self._conn: Connection = await self._pool.acquire()
        self._tr: Transaction = self._conn.transaction()
        await self._tr.start()

    async def _release_resources(self):
        if not self._conn:
            return
        async with AsyncContextExit(self._tr):
            pass

        await self._pool.release(self._conn)
        self._conn = None
        self._tr = None

    async def _acquire(self) -> bool:
        is_acquired = await self._conn.fetchval(
            self._LOCK_MODE[self._mode].format(self._name)
        )
        if is_acquired is True or is_acquired == "":
            return True
        return False

    async def _release(self) -> bool:
        is_released = await self._conn.fetchval(
            self._RELEASE_MODE[self._mode].format(self._name)
        )
        return is_released is True or is_released == ""


class AsyncPgAdLocker(PgAdLocker):
    LOCK_CLASS = AsyncPgAdLock
