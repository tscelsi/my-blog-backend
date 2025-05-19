import asyncio

from utils.background_tasks import BackgroundTasks


async def test_background_tasks_add():
    var = 0

    async def async_fn():
        await asyncio.sleep(0)
        nonlocal var
        var += 1

    bgt = BackgroundTasks()
    bgt.add(coro=async_fn)
    await bgt.join()
    assert var == 1
