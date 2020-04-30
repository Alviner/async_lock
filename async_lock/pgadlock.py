import hashlib
import logging

from aiopg import Pool

from async_lock.base_lock import AsyncLocker, AsyncLock

ACQUIRE_QUERY = """SELECT pg_try_advisory_lock({:d});"""
RELEASE_QUERY = """SELECT pg_advisory_unlock({:d});"""

log = logging.getLogger(__name__)


class AsyncPgAdLock(AsyncLock):
    def __init__(self, name: str, pool: Pool):
        super(AsyncPgAdLock, self).__init__(name=name)
        self._pool = pool

    async def acquire(self):
        log.debug("Try acquire lock %r", self._name)
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ACQUIRE_QUERY.format(self._name))
                async for (is_acquired, *_) in cur:
                    log.debug("Lock %d in conn %r acquired result: %r",
                              self._name, id(conn), is_acquired)
                    return is_acquired

    async def release(self):
        log.debug("Try release lock %r", self._name)
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(RELEASE_QUERY.format(self._name))
                async for (is_released, *_) in cur:
                    log.debug("Lock %d released in conn %r result: %r",
                              self._name, id(conn), is_released)
                    return is_released


class AsyncPgAdLocker(AsyncLocker):
    LOCK_CLASS = AsyncPgAdLock

    def __init__(self, pool: Pool, **kwargs):
        super(AsyncPgAdLocker, self).__init__(**kwargs)
        self._pool: Pool = pool

    def _lock_name(self, name: str) -> int:
        """
            PostgreSQL requires lock id to be integers.
            Lets Hash the lock name to an integer.
        """
        l_name = super(AsyncPgAdLocker, self)._lock_name(name=name)
        return int(hashlib.sha256(l_name.encode('utf-8')).hexdigest(),
                   16) % 10 ** 8

    def lock(self, *args, **kwargs):
        return super(AsyncPgAdLocker, self).lock(*args, **kwargs,
                                                 pool=self._pool)
