import os
import sys
import asyncio
from time import sleep
from datetime import datetime
from threading import Thread
import shutil
import subprocess
from pathlib import Path
from random import randint

from apng import APNG
from PIL import Image, ImageDraw, ImageSequence

"""
pip install -e .
###
pip install -U git+https://github.com/barsikus007/pydistort
"""


scripts = sys.executable.split('python.exe')[0]


async def run(cmd, silent=False):
    if not isinstance(cmd, str):
        cmd = " ".join(cmd)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if not silent:
        print(f'[{cmd!r} exited with {proc.returncode}]')
        if stdout:
            print(f'[stdout]\n{stdout.decode(errors="ignore")}')
        if stderr:
            print(f'[stderr]\n{stderr.decode(errors="ignore")}')


class Process:
    def __init__(self, limit=5, ffmpeg_limit=10, unlimited=0):
        self.q = 0
        self.ffmpeg_q = 0
        self.limit = limit
        self.ffmpeg_limit = ffmpeg_limit
        self.unlimited = unlimited

    async def create_coro(self, filename, level, it, total):
        # TODO notify process
        await self.distort(filename, level)
        print(f'{it + 1}/{total}')

    async def render_lottie(self, filename, filename_json):
        while self.q > self.limit:
            await asyncio.sleep(0.1)
        self.q += 1
        command = (sys.executable, f"{scripts}lottie_convert.py", filename_json, filename, "--fps", "60")
        await run(command)
        self.q -= 1

    async def dist(self):
        raise NotImplementedError

    async def distort(self, filename, level):
        while self.q > self.limit:
            await asyncio.sleep(0.1)
        self.q += 1
        with Image.open(filename) as image:
            imgdim = image.width, image.height
        kok = (100 - level) % 100
        if os.name == "nt":
            command = ("magick", "convert", f'"{filename}"', "-liquid-rescale", f"{kok}%", "-resize", f"{imgdim[0]}x{imgdim[1]}", f'"{filename}"')
        else:
            command = ("convert", f'"{filename}"', "-liquid-rescale", f"{kok}%", "-resize", f"{imgdim[0]}x{imgdim[1]}", f'"{filename}"')
        await run(command)
        self.q -= 1
        return filename

    async def distort_folder(self, folder):
        onlyfiles = [fr'{folder}\{f}' for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        # TODO onlyfiles to input or generate
        dist_step = 60 / (len(onlyfiles) + 1)
        coros = [self.create_coro(file, 20 + dist_step * i, i, len(onlyfiles)) for i, file in enumerate(onlyfiles)]
        await asyncio.gather(*coros)
        return

    async def distort_gif(self, filename):
        with Image.open(filename) as image:
            n_frames = image.n_frames
            duration = image.info["duration"]
            dist_step = 60 / (n_frames + 1)
            frames = ImageSequence.all_frames(image)
            folder = Path("tmp/")
            folder.mkdir(parents=True, exist_ok=True)
            coros = []
            for i, frame in enumerate(frames):
                temp_name = f"tmp/{i + 1}.png"
                frame.save(temp_name, format="PNG")
                coros.append(self.create_coro(temp_name, 20 + dist_step * i, i, n_frames))
        dist_frames = []
        await asyncio.gather(*coros)
        for i in range(n_frames):
            dist_frames.append(Image.open(f"tmp/{i + 1}.png"))
        with Image.open("tmp/1.png") as dist_image:
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
                temp_name = f"tmp/{i + 1}.png"
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
                temp_name = f"tmp/{i + 1}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                print(f'{i + 1}/{n_frames}')

        with open(filename_png, 'wb'):
            APNG.from_files(dist_frames, delay=duration).save(filename_png)
        dist_frames.clear()
        shutil.rmtree(folder)
        os.remove(filename_json)
        os.remove(filename)
        return filename_png

    async def ffmpeg(self, command):
        while self.ffmpeg_q > self.ffmpeg_limit:
            await asyncio.sleep(0.1)
        self.ffmpeg_q += 1
        await run(command)
        self.q -= 1

###

    async def distort_flex(self, filename, n_frames=9, a=20, b=80, duration=200, reverse=False, random=False):
        dist_step = (b - a) / (n_frames + 1)
        folder = Path("tmp/")
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(n_frames):
            temp_name = f"tmp/{i + 1}.png"
            shutil.copyfile(filename, temp_name)
            if random:
                await self.distort(temp_name, randint(a, b))
            else:
                await self.distort(temp_name, a + dist_step * i)
            print(f'{i + 1}/{n_frames}')
        dist_frames = []
        for i in range(n_frames):
            dist_frames.append(Image.open(f"tmp/{i + 1}.png"))
        if reverse:
            for i in range(n_frames, 0, -1):
                dist_frames.append(Image.open(f"tmp/{i}.png"))
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
                temp_name = f"tmp/{i + 1}.png"
                dist_frames.append(temp_name)
                frame.save(temp_name, format="PNG")
                print(f'{i + 1}/{n_frames}')
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
    # SeamCarving("test.png").show_energy()
    # SeamCarving("test.png")._find_sum()
    # SeamCarving("test.png")._show_sum()
    # SeamCarving("test.png")._show_shrinked_pixels()

    # SeamCarving("test.png").remove_lines(50)
    # SeamCarving("test.png").remove_lines_alt(50)
    # numba

    asyncio.get_event_loop().run_until_complete(
        Process().render_lottie(filename_json='../AnimatedSticker.tgs', filename='../A.png')
    )
