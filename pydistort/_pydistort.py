import os
import sys
import shutil
import asyncio
from pathlib import Path
from random import randint

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
    if lib == 'magick':
        return


class Process:
    def __init__(self, limit=0):
        self.limit = limit  # TODO
        self.queue = _Queue(limit)
        self.q = 0

    async def create_coro(self, filename, level, it, total):
        await self.distort(filename, level)
        print(f'{it + 1:03d}/{total:03d}')

    # TODO LEGACY async def render_lottie(self, filename_json, filename, quiet=False):
    async def render_lottie(self, filename, filename_json, quiet=False):
        command = [filename_json, filename, "--fps", "60"]
        return await self.queue.add(run(command, executable=f"{sys.executable} {scripts}lottie_convert.py", quiet=quiet))

    async def distort(self, filename, level):
        return await self.queue.add(seam_carving.distort(filename, level))

    async def distort_many(self, distorts: list[list[str, int | float]], report_every=1, callback=None):
        if not callback:
            it = 0

            async def callback(*args, **kwargs):
                nonlocal it
                it += 1
                if it % report_every:
                    print(f'{it:03d}/{len(distorts):03d}')
        distorts = [self.distort(file, level) for file, level in distorts]
        return await self.queue.add_many(distorts, callback)

    async def distort_folder(self, folder, callback=None):
        if not callback:
            async def callback(filename, *args, **kwargs):
                print(filename)
        files = [f'{folder}/{f}' for f in os.listdir(folder)]
        dist_step = 60 / (len(files) + 1)
        await self.queue.add_many([self.distort(file, 20 + dist_step * i) for i, file in enumerate(files)], callback)

    async def distort_gif(self, filename):
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            dist_step = 60 / (n_frames + 1)
            frames = ImageSequence.all_frames(image)
            folder = Path("tmp/")
            folder.mkdir(parents=True, exist_ok=True)
            distorts = []
            for i, frame in enumerate(frames):
                temp_name = f"tmp/{i + 1:03d}.png"
                frame.save(temp_name, format="PNG")
                distorts.append([temp_name, 20 + dist_step * i])
        dist_frames = []
        await self.distort_many(distorts)
        for i in range(n_frames):
            dist_frames.append(Image.open(f"tmp/{i + 1:03d}.png"))
        with Image.open("tmp/001.png") as dist_image:
            dist_image.save(filename, save_all=True, append_images=dist_frames[1:],
                            format="gif", duration=duration, loop=0)
            dist_frames.clear()
        shutil.rmtree(folder)
        return filename

    async def distort_lottie_gif(self, filename_json):
        filename = f'{filename_json.split(".")[0]}.gif'
        await self.render_lottie(filename, filename_json)
        os.remove(filename_json)
        return await self.distort_gif(filename)

    async def distort_lottie_apng(self, filename_json):
        link_hash = filename_json.split(".")[0]
        filename = f'{link_hash}.gif'
        await self.render_lottie(filename, filename_json)
        os.remove(filename_json)
        filename_png = f'{link_hash}.png'
        dist_frames = []
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            dist_step = 60 / (n_frames + 1)
            frames = ImageSequence.all_frames(image)
            folder = Path("tmp/")
            folder.mkdir(parents=True, exist_ok=True)
            coros = []
            for i, frame in enumerate(frames):
                temp_name = f"tmp/{i + 1:03d}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                coros.append(self.create_coro(temp_name, 20 + dist_step * i, i, n_frames))
        await asyncio.gather(*coros)
        with open(filename_png, 'wb'):
            APNG.from_files(dist_frames, delay=duration).save(filename_png)
        dist_frames.clear()
        shutil.rmtree(folder)
        os.remove(filename)
        return filename_png

    async def clon_lottie_gif(self, filename_json):
        filename = f'{filename_json.split(".")[0]}.gif'
        await self.render_lottie(filename, filename_json)
        os.remove(filename_json)
        return filename

    async def clon_lottie_apng(self, filename_json):
        filename = f'{filename_json.split(".")[0]}.gif'
        await self.render_lottie(filename, filename_json)
        filename_png = f'{filename_json.split(".")[0]}.png'
        dist_frames = []
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            frames = ImageSequence.all_frames(image)
            folder = Path("tmp/")
            folder.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(frames):
                temp_name = f"tmp/{i + 1:03d}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                print(f'{i + 1:03d}/{n_frames}')

        with open(filename_png, 'wb'):
            APNG.from_files(dist_frames, delay=duration).save(filename_png)
        dist_frames.clear()
        shutil.rmtree(folder)
        os.remove(filename_json)
        os.remove(filename)
        return filename_png

###

    async def distort_flex(self, filename, n_frames=9, a=20, b=80, duration=200, reverse=False, random=False):
        dist_step = (b - a) / (n_frames + 1)
        folder = Path("tmp/")
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(n_frames):
            temp_name = f"tmp/{i + 1:03d}.png"
            shutil.copyfile(filename, temp_name)
            if random:
                await self.distort(temp_name, randint(a, b))
            else:
                await self.distort(temp_name, a + dist_step * i)
            print(f'{i + 1:03d}/{n_frames}')
        dist_frames = []
        for i in range(n_frames):
            dist_frames.append(Image.open(f"tmp/{i + 1:03d}.png"))
        if reverse:
            for i in range(n_frames, 0, -1):
                dist_frames.append(Image.open(f"tmp/{i:03d}.png"))
        filename = filename[:-4:] + ".gif"
        with Image.open("tmp/1.png") as dist_image:
            dist_image.save(filename, save_all=True, append_images=dist_frames[1:],
                            format="gif", duration=duration, loop=0)
            dist_frames.clear()
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
                temp_name = f"tmp/{i + 1:03d}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                print(f'{i + 1:03d}/{n_frames}')
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
