import os
import asyncio
import shutil
from pathlib import Path
from tempfile import mkdtemp
from typing import Callable

from PIL import Image

from pydistort.image import gif_to_folder
from pydistort.utils.queue import Queue
from pydistort.utils.runners import run


async def distort(filename: str | Path, level: int | float, quiet=True):
    kok = (100 - level) % 100
    with Image.open(filename) as image:
        command = ['convert', f'{filename}',
                   '-liquid-rescale', f'{kok}%',
                   '-resize', f'{image.width}x{image.height}', f'{filename}']
    if os.name == 'nt':
        command = ['magick', *command]
    await run(command, quiet=quiet)
    return filename


async def distort_many(
        distorts: list[list[str | Path, int | float]],
        queue: Queue = None, callback: Callable = None, quiet=True):
    distorts = [distort(file, level, quiet) for file, level in distorts]
    if queue:
        return await queue.add_many(distorts, callback)
    else:
        return await asyncio.gather(*distorts)


async def distort_folder(
        folder: str | Path, start=20, end=80,
        queue: Queue = None, callback: Callable = None, quiet=True):
    files = [*Path(folder).iterdir()]
    dist_step = (end-start) / (len(files) + 1)
    return await distort_many([[file, start + dist_step * i] for i, file in enumerate(files)], queue, callback, quiet)


async def distort_gif(
        filename: str | Path, start=20, end=80,
        queue: Queue = None, callback: Callable = None, quiet=True):
    folder, duration = gif_to_folder(filename, Path(mkdtemp(dir='.')))
    frames = await distort_folder(folder, start, end, queue, callback, quiet)
    first_frame, *other_frames = [Image.open(frame) for frame in frames]
    first_frame.save(filename, save_all=True, append_images=other_frames, format='gif', duration=duration, loop=0)
    [frame.close() for frame in [first_frame, *other_frames]]  # TODO is it required?
    shutil.rmtree(folder)
    return filename
