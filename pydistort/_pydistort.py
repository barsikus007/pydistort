import os
import sys
import shutil
import asyncio
from pathlib import Path, PurePath
from random import randint
from tempfile import mkdtemp

from apng import APNG
from PIL import Image

from pydistort.image.apng_tools import gif_to_apng
from pydistort.utils.queue import Queue as _Queue
from pydistort.image import seam_carving, lottie_tools, gif_tools

scripts = sys.executable.split('python.exe')[0]


class Process:
    def __init__(self, limit=0):
        self.queue = _Queue(limit)

    async def distort(self, filename, level, quiet=True):
        return await self.queue.add(seam_carving.distort(filename, level, quiet))

    async def distort_many(self, distorts: list[list[str, int | float]], report_every=1, callback=None, quiet=True):
        if not callback:
            it = 0

            async def callback(*args, **kwargs):
                nonlocal it
                it += 1
                if it % report_every:
                    print(f'{it:05d}/{len(distorts):05d}')
        return await seam_carving.distort_many(distorts, self.queue, callback, quiet)

    async def distort_folder(self, folder, callback=None, quiet=True):
        if callback is None:
            async def callback(filename, *args, **kwargs):
                print(filename)
        return await seam_carving.distort_folder(folder, 20, 80, self.queue, callback, quiet)

    async def distort_gif(self, filename, callback=None, quiet=True):
        return seam_carving.distort_gif(filename, 20, 80, self.queue, callback, quiet)

    async def render_lottie(self, filename_json, filename, quiet=True):
        return await self.queue.add(lottie_tools.render_lottie(filename_json, filename, quiet))

###

    async def distort_lottie_gif(self, filename_json, quiet=True):
        filename = Path(filename_json).with_suffix('.gif')
        await self.render_lottie(filename_json, filename, quiet)
        os.remove(filename_json)
        return await self.distort_gif(filename)

    async def distort_lottie_apng(self, filename_json):
        filename_gif = Path(filename_json).with_suffix('.gif')
        filename_png = Path(filename_json).with_suffix('.png')
        await self.render_lottie(filename_json, filename_gif)
        os.remove(filename_json)

        folder, duration = gif_tools.gif_to_folder(filename_gif, Path(mkdtemp(dir='.')))
        os.remove(filename_gif)
        frames = await seam_carving.distort_folder(folder, 20, 80, self.queue)

        with open(filename_png, 'wb'):
            APNG.from_files(frames, delay=duration).save(filename_png)
        shutil.rmtree(folder)
        return filename_png

    async def render_lottie_gif(self, filename_json):
        filename_gif = Path(filename_json).with_suffix('.gif')
        await self.render_lottie(filename_json, filename_gif)
        os.remove(filename_json)
        return filename_gif

    async def render_lottie_apng(self, filename_json):
        filename_gif = await self.render_lottie_gif(filename_json)
        return gif_to_apng(filename_gif)


###

    async def distort_flex(self, filename, n_frames=9, start=20, end=80, duration=200, reverse=False, random=False):
        folder = Path(mkdtemp(dir='.'))
        frames = [shutil.copyfile(filename, folder / f'{i + 1:05d}.png') for i in range(n_frames)]
        os.remove(filename)
        if random:
            frames = await seam_carving.distort_many([[frame, randint(start, end)] for frame in frames])
        else:
            frames = await seam_carving.distort_folder(folder, start, end)

        if reverse:
            first_frame, *other_frames = [Image.open(frame) for frame in frames[::-1]]
        else:
            first_frame, *other_frames = [Image.open(frame) for frame in frames]
        filename_gif = Path(filename).with_suffix('.gif')
        first_frame.save(filename_gif, save_all=True, append_images=other_frames,
                         format='gif', duration=duration, loop=0)
        [frame.close() for frame in [first_frame, *other_frames]]
        shutil.rmtree(folder)
        return filename_gif

    async def distort_flex_reverse(self, filename, n_frames=10, start=1, end=70, duration=50):
        return await self.distort_flex(filename, n_frames, start, end, duration, reverse=True)

    async def distort_random(self, filename, n_frames=9, start=20, end=80, duration=200):
        return await self.distort_flex(filename, n_frames, start, end, duration, random=True)

###

    def image_to_png(self, filename):
        filename_png = Path(filename).with_suffix('.png')
        with Image.open(filename) as image:
            image.save(filename_png)
        os.remove(filename)
        return filename_png

    def jpeg(self, filename):
        with Image.open(filename) as img:
            img.save(filename, quality=1)
        return filename

    def png_to_jpeg(self, filename):
        filename_jpg = Path(filename).with_suffix('.jpg')
        with Image.open(filename) as img:
            img.convert('RGB').save(filename_jpg, quality=1)
        with Image.open(filename_jpg) as img:
            datas = img.getdata()
            new_data = []
            for item in datas:
                if item[0] == 51 and item[1] == 119 and item[2] == 96:
                    new_data.append((255, 255, 255, 0))
                elif item[0] == 96 and item[1] == 96 and item[2] == 96:
                    new_data.append((255, 255, 255, 0))
                elif item[0] == 0 and item[1] == 0 and item[2] == 0:
                    new_data.append((255, 255, 255, 0))
                elif item[0] == 255 and item[1] == 255 and item[2] == 255:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((item[0], item[1], item[2], 255))
            new_img = Image.new('RGBA', img.size)
            new_img.putdata(new_data)
            new_img.save(filename)
        os.remove(filename_jpg)
        return filename


if __name__ == '__main__':
    asyncio.run(
        Process().render_lottie(filename_json='../AnimatedSticker.tgs', filename='../A.png')
    )
