import os
import asyncio
from typing import Callable

from PIL import Image

from pydistort.utils.queue import Queue
from pydistort.utils.runners import run


async def distort(filename: str, level: int | float):
    kok = (100 - level) % 100
    with Image.open(filename) as image:
        command = ['convert', f'{filename}',
                   '-liquid-rescale', f'{kok}%',
                   '-resize', f'{image.width}x{image.height}', f'{filename}']
    if os.name == "nt":
        command = ["magick", *command]
    await run(command)
    return filename


async def distort_folder(folder: str, queue: Queue = None, callback: Callable = None):
    if queue and not callback:
        async def callback(filename, **kwargs):
            print(filename)
    files = [f'{folder}/{f}' for f in os.listdir(folder)]
    # files = [f'{folder}/{f}' for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    dist_step = 60 / (len(files) + 1)
    coros = [distort(file, 20 + dist_step * i) for i, file in enumerate(files)]
    if queue:
        await queue.add_many(coros, callback)
    else:
        await asyncio.gather(*coros)
