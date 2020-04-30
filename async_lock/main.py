import asyncio
import logging

import aiomisc
import aiopg

from async_lock.pgadlock import AsyncPgAdLocker

dsn = "postgresql://guest:guest@localhost/pgdb"


async def lock(pool):
    locker = AsyncPgAdLocker(pool=pool, app_name="awesome_name")
    async with locker.lock("test"):
        await asyncio.sleep(60)


async def main():
    pool = await aiopg.create_pool(dsn=dsn, minsize=2)
    res = await asyncio.gather(lock(pool), lock(pool), return_exceptions=True)
    print(res)
    pool.close()
    await pool.wait_closed()


if __name__ == '__main__':
    with aiomisc.entrypoint(
        log_level=logging.DEBUG,
    ) as loop:
        loop.run_until_complete(main())
