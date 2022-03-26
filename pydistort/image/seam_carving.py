import os
import asyncio
from pathlib import Path
from typing import Callable

from PIL import Image

from pydistort.utils.queue import Queue
from pydistort.utils.runners import run


async def distort(filename: str, level: int | float, quiet=True):
    kok = (100 - level) % 100
    with Image.open(filename) as image:
        command = ['convert', f'{filename}',
                   '-liquid-rescale', f'{kok}%',
                   '-resize', f'{image.width}x{image.height}', f'{filename}']
    if os.name == "nt":
        command = ["magick", *command]
    await run(command, quiet=quiet)
    return filename


async def distort_many(distorts: list[list[str, int | float]], queue: Queue = None, callback: Callable = None, quiet=True):
    distorts = [distort(file, level, quiet) for file, level in distorts]
    if queue:
        return await queue.add_many(distorts, callback)
    else:
        return await asyncio.gather(*distorts)


async def distort_folder(folder: str, queue: Queue = None, callback: Callable = None, quiet=True):
    files = [*Path(folder).iterdir()]
    dist_step = 60 / (len(files) + 1)
    return await distort_many([[file, 20 + dist_step * i] for i, file in enumerate(files)], queue, callback, quiet)
