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
import sys
sys.path.append("C:/Users/Admin/PycharmProjects/pydistort")
import pydistort
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


class SeamCarving:
    def __init__(self, path, mode=1):
        self.path = path
        self.mode = mode
        self.image = Image.open(self.path)

    def find_energy(self):
        image = self.image
        img_height = image.height
        img_width = image.width
        energy = [[0 for _ in range(img_height)] for __ in range(img_width)]

        for i in range(img_width):
            for j in range(img_height):
                energy[i][j] = 0

# Считаем отдельно для компонент R, G, B
                for k in range(3):
                    summ = 0
                    count = 0

# Если пиксел не крайний снизу, то добавляем в sum разность между текущим пикселом и соседом снизу
                    if i != img_width - 1:
                        count += 1
                        summ += abs(image.getpixel((i, j))[k] - image.getpixel((i + 1, j))[k])

# Если пиксел не крайний справа, то добавляем в sum разность между поточным пикселом и соседом справа
                    if j != img_height - 1:
                        count += 1
                        summ += abs(image.getpixel((i, j))[k] - image.getpixel((i, j + 1))[k])

# В массив energy добавляем среднее арифметическое разностей пикселя с соседями по k-той компоненте (то есть по R, G, B)
                    if count != 0:
                        energy[i][j] += summ // count
                        # energy[i][j] += summ / count
        return energy

    # Отрисовка энергии пикселей
    def draw_energy(self):
        offs = 255 * bool(self.mode)
        energy = self.find_energy()
        x = len(energy)
        y = len(energy[0])
        # ImageDraw.Draw('RGB', (x, y)).point((i, j), fill=img.getpixel(xy))
        im = Image.new('RGB', (x, y))
        draw = ImageDraw.Draw(im)
        for i in range(x):
            for j in range(y):
                # draw.point((i, j), fill=(int(energy[i][j]), int(energy[i][j]), int(energy[i][j]), int(energy[i][j])))
                draw.point((i, j), fill=(abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j]))))
        print("redy")
        im.save(self.path, format="png")

        return self.path

    def show_energy(self):
        offs = 255 * bool(self.mode)
        energy = self.find_energy()
        x = len(energy)
        y = len(energy[0])
        # ImageDraw.Draw('RGB', (x, y)).point((i, j), fill=img.getpixel(xy))
        im = Image.new('RGB', (x, y))
        draw = ImageDraw.Draw(im)
        for i in range(x):
            for j in range(y):
                # draw.point((i, j), fill=(int(energy[i][j]), int(energy[i][j]), int(energy[i][j]), int(energy[i][j])))
                draw.point((i, j), fill=(abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j]))))
        print("redy")

        return im.show()

    def find_sum(self, mode="x"):
        """
        :param mode: "x" - x->; "y" - y-^
        :return: array of sum
        """
        image = self.image
        img_height = image.height
        img_width = image.width
        energy = self.find_energy()
        x = len(energy)
        y = len(energy[0])
        summm = [[0 for _ in range(img_height)] for __ in range(img_width)]
        # summm = energy

# Для верхней строчки значение sum и energy будут совпадать
        # y
        # for j in range(img_height):
        #     summm[0][j] = energy[0][j]
        for i in range(img_width):
            summm[i][0] = energy[i][0]

# Для всех остальных пикселей значение элемента (i,j) массива sum будут равны
        # energy[i,j] + MIN ( sum[i-1, j-1], sum[i-1, j], sum[i-1, j+1])
        # y
        # for i in range(1, img_width):
        #     for j in range(img_height):
        #         summm[i][j] = summm[i - 1][j]
        #         if j > 0 and summm[i - 1][j - 1] < summm[i][j]:
        #             summm[i][j] = summm[i - 1][j - 1]
        #         if j < img_height - 1 and summm[i - 1][j + 1] < summm[i][j]:
        #             summm[i][j] = summm[i - 1][j + 1]
        #         summm[i][j] += energy[i][j]
        # print(len(summm), len(summm[0]))
        for j in range(1, img_height):
            for i in range(img_width):
                summm[i][j] = summm[i][j - 1]
                # print(i, j)
                # print(summm[i][j])
                # if i > 0:
                #     print(summm[i-1][j-1])
                # if i < img_width - 1:
                #     print(summm[i+1][j-1])
                if i > 0 and summm[i - 1][j - 1] < summm[i][j]:
                    summm[i][j] = summm[i - 1][j - 1]
                if i < img_width - 1 and summm[i + 1][j - 1] < summm[i][j]:
                    summm[i][j] = summm[i + 1][j - 1]
                # print(summm[i][j])
                # print("---")
                summm[i][j] += energy[i][j]
        return summm

    def _show_sum(self):
        offs = 255 * bool(self.mode)
        energy = self.find_sum()
        x = len(energy)
        y = len(energy[0])
        print(max(max(energy)))
        # ImageDraw.Draw('RGB', (x, y)).point((i, j), fill=img.getpixel(xy))
        im = Image.new('RGB', (x, y))
        draw = ImageDraw.Draw(im)
        for i in range(x):
            for j in range(y):
                # draw.point((i, j), fill=(int(energy[i][j]), int(energy[i][j]), int(energy[i][j]), int(energy[i][j])))
                # print(energy[i][j])
                draw.point((i, j), fill=(abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j])), abs(offs - int(energy[i][j]))))
        print("redy")

        return im.show()

    def find_shrinked_pixels(self):
        image = self.image
        img_height = image.height
        img_width = image.width
        summm = self.find_sum()
        x = len(summm)
        y = len(summm[0])
# Номер последней строчки
        last = img_height - 1

# Выделяем память под массив результатов
        res = [0 for j in range(img_height)]

# Ищем минимальный элемент массива sum, который находиться в нижней строке и записываем результат в res[last]
        res[last] = 0
        for i in range(1, img_width):
            if summm[i][last] < summm[res[last]][last]:
                res[last] = i

# Теперь вычисляем все элементы массива от предпоследнего до первого.
        for j in range(last-1, -1, -1):
# prev - номер пикселя цепочки из предыдущей строки
# В этой строке пикселями цепочки могут быть только (prev-1), prev или (prev+1), поскольку цепочка должна быть связанной
            prev = int(res[j + 1])

# Здесь мы ищем, в каком элементе массива sum, из тех, которые мы можем удалить, записано минимальное значение и присваиваем результат переменной res[i]
            res[j] = prev
            if prev > 0 and summm[res[j]][j] > summm[prev - 1][j]:
                res[j] = prev - 1
            if prev < img_width - 1 and summm[res[j]][j] > summm[prev + 1][j]:
                res[j] = prev + 1
        return res


    def find_shrinked_pixels_alt(self):
        image = self.image
        img_height = image.height
        img_width = image.width
        summm = self.find_sum()
        x = len(summm)
        y = len(summm[0])
# Номер последней строчки
        last = img_height - 1

# Выделяем память под массив результатов
        res = [0 for j in range(img_height)]

# Ищем минимальный элемент массива sum, который находиться в нижней строке и записываем результат в res[last]
        res[last] = 0
        for i in range(1, img_width):
            if summm[i][last] > summm[res[last]][last]:
                res[last] = i

# Теперь вычисляем все элементы массива от предпоследнего до первого.
        for j in range(last-1, -1, -1):
# prev - номер пикселя цепочки из предыдущей строки
# В этой строке пикселями цепочки могут быть только (prev-1), prev или (prev+1), поскольку цепочка должна быть связанной
            prev = int(res[j + 1])

# Здесь мы ищем, в каком элементе массива sum, из тех, которые мы можем удалить, записано минимальное значение и присваиваем результат переменной res[i]
            res[j] = prev
            if prev > 0 and summm[res[j]][j] < summm[prev - 1][j]:
                res[j] = prev - 1
            if prev < img_width - 1 and summm[res[j]][j] < summm[prev + 1][j]:
                res[j] = prev + 1
        return res

    def _show_shrinked_pixels(self):
        image = self.image
        offs = 255 * bool(self.mode)
        res = self.find_shrinked_pixels()
        x = image.width
        y = image.height
        draw = ImageDraw.Draw(image)
        for j in range(y):
            # draw.point((i, j), fill=(int(energy[i][j]), int(energy[i][j]), int(energy[i][j]), int(energy[i][j])))
            # print(j)
            # if j != 0:
            # print(j)
            draw.point((res[j], j), fill=(255, 0, 0))
        print("redy")

        return image.show()

    def remove_lines(self, level=50):
        image = self.image
        times = image.width // 100 * level
        for time in range(times):
            image = self.image
            print(f"{time+1}/{times}")
            res = self.find_shrinked_pixels()
            x, y = self.image.size
            self.image = Image.new("RGBA", (x-1, y))
            draw = ImageDraw.Draw(self.image)
            get = 0
            for j in range(y):
                for i in range(x-1):
                    if i == res[j]:
                        # draw.point((i, j), fill=(255, 0, 0))
                        # continue
                        get = 1
                    draw.point((i, j), fill=image.getpixel((i+get, j)))
                get = 0


        print("redy")
        self.image.show()
        return self.image.save("test2.png")

    def remove_lines_alt(self, level=50):
        image = self.image
        times = image.width // 100 * level
        for time in range(times):
            image = self.image
            print(f"{time+1}/{times}")
            res = self.find_shrinked_pixels_alt()
            x, y = self.image.size
            self.image = Image.new("RGBA", (x-1, y))
            draw = ImageDraw.Draw(self.image)
            get = 0
            for j in range(y):
                for i in range(x-1):
                    if i == res[j]:
                        # draw.point((i, j), fill=(255, 0, 0))
                        # continue
                        get = 1
                    draw.point((i, j), fill=image.getpixel((i+get, j)))
                get = 0

        print("redy")
        self.image.show()
        return self.image.save("test3.png")


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
