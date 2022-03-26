import asyncio
import time
from random import randint


async def gandom(i):
    num = randint(1, 30) / 1000
    await asyncio.sleep(num)
    print(f'{i:03d} - {num}')


async def worker(w, queue):
    while True:
        # Get a "work item" out of the queue.
        sleep_for = await queue.get()

        # Sleep for the "sleep_for" seconds.
        num = randint(1, 30) / 10
        await asyncio.sleep(num)
        # print(f'{sleep_for:03d} - {num}')

        # Notify the queue that the "work item" has been processed.
        queue.task_done()

        print(f'{sleep_for:3d} has slept for {num:.3f} seconds [{w}]')


async def main():
    started_at = time.monotonic()
    tasks = []
    try:
        queue = asyncio.Queue(1)
        for i in range(1):
            task = asyncio.create_task(worker(f'worker-{i}', queue))
            tasks.append(task)
        for i in range(1, 100):
            await queue.put(i)

        # Wait until the queue is fully processed.
        await queue.join()
    finally:
        # Cancel our worker tasks.
        for task in tasks:
            task.cancel()
        # Wait until all worker tasks are cancelled.
        await asyncio.gather(*tasks, return_exceptions=True)
    total = time.monotonic() - started_at
    print(total)


if __name__ == '__main__':
    asyncio.run(main())
