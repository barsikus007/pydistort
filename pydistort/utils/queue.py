import asyncio
import inspect
from typing import Callable, Coroutine


class Queue:
    def __init__(self, limit=0):
        self.q = 0
        self.limit = limit if limit != 0 else None

    async def add(self, func: Coroutine, callback=None):
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


class _Queue:
    def __init__(self, workers=1, queue_limit=0):
        self.q = 0
        self.workers = workers
        tasks = []
        self.task_queue = asyncio.Queue(queue_limit)
        for i in range(workers):
            task = asyncio.create_task(self.worker(f'worker-{i}'))
            tasks.append(task)

    async def worker(self, name):
        while True:
            func, args, kwargs, callback = await self.task_queue.get()
            await func(*args, **kwargs)
            if callback:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            self.task_queue.task_done()

    async def add(self, func, args=None, kwargs=None, callback=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        await self.task_queue.put([func, args, kwargs, callback])

    async def add_many(self, coros: list):
        # queue = asyncio.Queue()
        for coro in coros:
            if coro[1] is None:
                coro[1] = []
            if coro[2] is None:
                coro[2] = {}
            await self.task_queue.put(coro)

    async def add_task(self, coros: list):
        # queue = asyncio.Queue()
        for coro in coros:
            if coro[1] is None:
                coro[1] = []
            if coro[2] is None:
                coro[2] = {}
            await self.task_queue.put(coro)
