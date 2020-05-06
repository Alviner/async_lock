import logging

from async_lock.pglock.pg_base import PgAdLock, PgAdLocker, \
    AsyncContextExit

log = logging.getLogger(__name__)


class AioPgAdLock(PgAdLock):

    def __init__(self, *args, **kwargs):
        super(AioPgAdLock, self).__init__(*args, **kwargs)
        self._curr = None
        self._tr = None

    async def _acquire_resources(self):
        self._conn = await self._pool.acquire()
        self._curr = await self._conn.cursor()
        self._tr = await self._curr.begin()

    async def _release_resources(self):
        if not self._conn:
            return
        async with AsyncContextExit(self._curr):
            async with AsyncContextExit(self._tr):
                pass

        await self._pool.release(self._conn)
        self._conn = None
        self._curr = None
        self._tr = None

    async def _acquire(self) -> bool:
        await self._curr.execute(self._LOCK_MODE[self._mode].format(self._name))
        async for (is_acquired, *_) in self._curr:
            if is_acquired is True or is_acquired == "":
                return True
            return False

    async def _release(self) -> bool:
        await self._curr.execute(self._RELEASE_MODE[self._mode].format(self._name))
        async for (is_released, *_) in self._curr:
            return is_released is True or is_released == ""


class AioPgAdLocker(PgAdLocker):
    LOCK_CLASS = AioPgAdLock
