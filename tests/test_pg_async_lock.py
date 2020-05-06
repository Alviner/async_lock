import asyncio
import os

import aiopg
import asyncpg
import pytest

from async_lock.base_lock import LockAcquireFailure
from async_lock.pglock.aiopg import AioPgAdLocker
from async_lock.pglock.asyncpg import AsyncPgAdLocker
from async_lock.pglock.pg_base import LockMode

DB_URL = os.environ.get("DB_URL", "postgresql://pguser:pguser@localhost/pgdb")


@pytest.fixture(params=[asyncpg, aiopg])
async def async_pool(request):
    pool_module = request.param
    async with pool_module.create_pool(dsn=DB_URL) as _pool:
        yield _pool


@pytest.fixture(params=[asyncpg, aiopg])
def locker(async_pool):
    locker_cls = None
    if isinstance(async_pool, aiopg.Pool):
        locker_cls = AioPgAdLocker
    elif isinstance(async_pool, asyncpg.pool.Pool):
        locker_cls = AsyncPgAdLocker
    return locker_cls(pool=async_pool, app_name="awesome_project")


@pytest.mark.parametrize("mode", [mode for mode in LockMode])
async def test_concurrently_lock(locker, mode):
    def gen_lock():
        return locker.lock("lock", mode=mode)

    num = 20
    locks = [gen_lock() for _ in range(num)]
    results = await asyncio.gather(*[lock.acquire() for lock in locks])
    locked_index = results.index(True)
    try:
        assert results.pop(locked_index) is True
        assert results == [False for _ in range(num - 1)]
    finally:
        await locks[locked_index].release()


@pytest.mark.parametrize("mode_first", [mode for mode in LockMode])
@pytest.mark.parametrize("mode_second", [mode for mode in LockMode])
async def test_async_context_manager(locker, mode_first, mode_second):
    lock = locker.lock("something", mode=mode_first)
    try:
        async with locker.lock("something", mode=mode_second):
            assert await lock.acquire() is False
        assert await lock.acquire() is True
    finally:
        await lock.release()


@pytest.mark.parametrize("mode_first", [mode for mode in LockMode])
@pytest.mark.parametrize("mode_second", [mode for mode in LockMode])
async def test_async_context_manager_error(locker, mode_first, mode_second):
    lock = locker.lock("something", mode=mode_first)
    assert await lock.acquire() is True
    try:
        with pytest.raises(LockAcquireFailure):
            async with locker.lock("something", mode=mode_second):
                pass
    finally:
        await lock.release()


@pytest.mark.parametrize("mode", [mode for mode in LockMode])
async def test_release_lock(locker, mode):
    lock = locker.lock("something", mode=mode)
    assert await lock.release() is False

    try:
        assert await lock.acquire() is True
    finally:
        assert await lock.release() is True
