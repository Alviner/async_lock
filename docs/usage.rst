=====
Usage
=====

To use async-lock in a project:

With aiopg::

    import aiopg
    import async_lock
    async with aiopg.create_pool(dsn=dsn, minsize=2) as pool:
        locker = async_lock.AioPgAdLocker(pool=pool, app_name="awesome_project")

        async with locker.lock("awesome_one_name"):
            ...

        async with locker.lock("awesome_another_name"):
            ...

