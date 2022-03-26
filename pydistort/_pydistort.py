import os
import sys
import shutil
import asyncio
from pathlib import Path, PurePath
from random import randint
from tempfile import mkdtemp

from apng import APNG
from PIL import Image, ImageSequence

from pydistort.utils.queue import Queue as _Queue
from pydistort.utils.runners import run
from pydistort.image import seam_carving


scripts = sys.executable.split('python.exe')[0]


def make_apng(dist_frames, duration, filename_png, lib='apng') -> None:
    if lib == 'apng':
        return APNG.from_files(dist_frames, delay=duration).save(filename_png)
    if lib == 'pil':
        frame, *frames = [Image.open(image) for image in dist_frames]
        return frame.save(
            filename_png,
            append_images=frames,
            save_all=True,
            duration=duration,
            loop=0,
        )


class Process:
    def __init__(self, limit=0):
        self.queue = _Queue(limit)
        self.q = 0

    async def render_lottie(self, filename_json, filename, quiet=True):
        command = [sys.executable, f'{scripts}lottie_convert.py', filename_json, filename, "--fps", "60"]
        return await self.queue.add(run(command, quiet=quiet))

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
        return await seam_carving.distort_folder(folder, self.queue, callback, quiet)

    async def distort_gif(self, filename):

        distorts = []
        folder = Path(mkdtemp(dir='.'))
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            dist_step = 60 / (n_frames + 1)
            frames = ImageSequence.all_frames(image)
            for i, frame in enumerate(frames):
                temp_name = folder / f"{i + 1:05d}.png"
                frame.save(temp_name, format="PNG")
                distorts.append([temp_name, 20 + dist_step * i])
        await self.distort_many(distorts)

        first_frame, *dist_frames = [Image.open(folder / f"{i + 1:05d}.png") for i in range(n_frames)]
        first_frame.save(filename, save_all=True, append_images=dist_frames,
                         format="gif", duration=duration, loop=0)
        [frame.close() for frame in [first_frame, *dist_frames]]  # TODO is it required?
        shutil.rmtree(folder)
        return filename

    async def distort_lottie_gif(self, filename_json, quiet=True):
        filename = f'{filename_json.split(".")[0]}.gif'
        await self.render_lottie(filename_json, filename, quiet)
        os.remove(filename_json)
        return await self.distort_gif(filename)

    async def distort_lottie_apng(self, filename_json):
        link_hash = filename_json.split(".")[0]
        filename = f'{link_hash}.gif'
        await self.render_lottie(filename_json, filename)
        os.remove(filename_json)
        filename_png = f'{link_hash}.png'

        distorts = []
        folder = Path(mkdtemp(dir='.'))
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            dist_step = 60 / (n_frames + 1)
            frames = ImageSequence.all_frames(image)
            for i, frame in enumerate(frames):
                temp_name = folder / f"{i + 1:05d}.png"
                frame.save(temp_name, format="PNG")
                distorts.append([temp_name, 20 + dist_step * i])
        await self.distort_many(distorts)

        with open(filename_png, 'wb'):
            APNG.from_files([_[0] for _ in distorts], delay=duration).save(filename_png)
        shutil.rmtree(folder)
        os.remove(filename)
        return filename_png

    async def render_lottie_gif(self, filename_json):
        filename = f'{filename_json.split(".")[0]}.gif'
        await self.render_lottie(filename_json, filename)
        os.remove(filename_json)
        return filename

    async def render_lottie_apng(self, filename_json):
        filename = await self.render_lottie_gif(filename_json)
        filename_png = f'{filename_json.split(".")[0]}.png'
        dist_frames = []

        folder = Path(mkdtemp(dir='.'))
        with Image.open(filename) as image:
            duration = image.info["duration"]
            frames = ImageSequence.all_frames(image)
            for i, frame in enumerate(frames):
                temp_name = folder / f"{i + 1:05d}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")

        with open(filename_png, 'wb'):
            APNG.from_files(dist_frames, delay=duration).save(filename_png)
        shutil.rmtree(folder)
        os.remove(filename)
        return filename_png

###

    async def distort_flex(self, filename, n_frames=9, a=20, b=80, duration=200, reverse=False, random=False):
        dist_step = (b - a) / (n_frames + 1)
        folder = Path(mkdtemp(dir='.'))
        for i in range(n_frames):
            temp_name = folder / f"{i + 1:05d}.png"
            shutil.copyfile(filename, temp_name)
            if random:
                await self.distort(temp_name, randint(a, b))
            else:
                await self.distort(temp_name, a + dist_step * i)
            print(f'{i + 1:05d}/{n_frames}')
        if reverse:
            first_frame, *dist_frames = [Image.open(folder / f"{i:05d}.png") for i in range(n_frames, 0, -1)]
        else:
            first_frame, *dist_frames = [Image.open(folder / f"{i + 1:05d}.png") for i in range(n_frames)]
        filename = filename[:-4:] + ".gif"
        first_frame.save(filename, save_all=True, append_images=dist_frames,
                         format="gif", duration=duration, loop=0)
        [frame.close() for frame in [first_frame, *dist_frames]]
        shutil.rmtree(folder)
        return filename

    async def distort_flex_reverse(self, filename, n_frames=10, a=1, b=70, duration=50):
        return await self.distort_flex(filename, n_frames, a, b, duration, reverse=True)

    async def distort_random(self, filename, n_frames=9, a=20, b=80, duration=200):
        return await self.distort_flex(filename, n_frames, a, b, duration, random=True)

###

    def png(self, filename):
        filename_png = f'{filename.split(".")[0]}.png'
        with Image.open(filename) as image:
            image.save(filename_png)
        os.remove(filename)
        return filename_png

    def png_gif(self, filename):
        filename_png = f'{filename.split(".")[0]}.png'
        dist_frames = []
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            frames = ImageSequence.all_frames(image)
            folder = Path("tmp/")
            folder.mkdir(parents=True, exist_ok=True)
            for frame, i in zip(frames, range(n_frames)):
                temp_name = f"tmp/{i + 1:05d}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                print(f'{i + 1:05d}/{n_frames}')
        with open(filename_png, 'wb'):
            APNG.from_files(dist_frames, delay=duration).save(filename_png)
        dist_frames.clear()
        os.remove(filename)
        return filename_png

    def jpeg(self, filename):
        with Image.open(filename) as img:
            img.save(filename, quality=1)
        return filename

    def jpeg_png(self, filename):
        filename_jpg = f'{filename.split(".")[0]}.jpg'
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
            new_img = Image.new("RGBA", img.size)
            new_img.putdata(new_data)
            new_img.save(filename)
        os.remove(filename_jpg)
        return filename


if __name__ == '__main__':
    asyncio.run(
        Process().render_lottie(filename_json='../AnimatedSticker.tgs', filename='../A.png')
    )
