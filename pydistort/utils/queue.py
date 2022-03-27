import asyncio
import inspect
from typing import Callable, Coroutine


class Queue:
    def __init__(self, limit=0):
        self.q = 0
        self.limit = limit if limit != 0 else None

    async def add(self, func: Coroutine, callback: Callable = None):
        while self.limit is not None and self.q > self.limit:
            await asyncio.sleep(0.1)
        self.q += 1
        kwargs = func.cr_frame.f_locals
        return_value = await func
        if callback:
            if inspect.iscoroutinefunction(callback):
                await callback(**kwargs)
            else:
                callback(**kwargs)
        self.q -= 1
        return return_value

    async def add_many(self, coros: list[Coroutine], callback: Callable = None):
        return await asyncio.gather(*[self.add(coro, callback=callback) for coro in coros])
