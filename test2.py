import asyncio
import glob
import os
import shutil
from pathlib import Path
from time import time

from PIL import Image, ImageSequence

from pydistort._pydistort import make_apng
from pydistort.image.apng import folder_to_apng
from pydistort.image.seam_carving_py import SeamCarving


def dummy_test(filename):
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
    dist_frames.clear()
    shutil.rmtree(folder)
    # os.remove(filename)


def apng_test(filename):
    filename_png = f'{filename.split(".")[0]}.png'
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
    make_apng(dist_frames, duration, filename_png)
    dist_frames.clear()
    shutil.rmtree(folder)
    # os.remove(filename_png)


def pil_test(filename):
    filename_png = f'{filename.split(".")[0]}3.png'
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
    make_apng(dist_frames, duration, filename_png, 'pil')
    dist_frames.clear()
    # shutil.rmtree(folder)
    # os.remove(filename_png)


def ffmpg_test(filename_gif, filename_png):
    filename_png = f'{filename_gif.split(".")[0]}.png'
    dist_frames = []
    with Image.open(filename_gif) as image:
        n_frames = image.n_frames
        duration = image.info["duration"]
        frames = ImageSequence.all_frames(image)
        folder = Path("tmp/")
        folder.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(frames):
            frame = frame.convert("RGBA")
            temp_name = f"tmp/{i + 1:05d}.png"
            dist_frames.append(temp_name)
            frame.save(temp_name, format="PNG")
            print(f'{i + 1:05d}/{n_frames:05d}')
        print(duration)
    os.system(f'ffmpeg -framerate {1000/duration} -i tmp/%05d.png -plays 0 -f apng {filename_png} -y')


def magick_test(filename_gif, filename_png):
    # os.system(f'magick convert {filename_gif} apng:{filename_png}')
    filename_png = f'{filename_gif.split(".")[0]}zxc.png'
    dist_frames = []
    with Image.open(filename_gif) as image:
        n_frames = image.n_frames
        duration = image.info["duration"]
        frames = ImageSequence.all_frames(image)
        folder = Path("tmp/")
        folder.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(frames):
            # frame = frame.convert("RGBA")
            temp_name = f"tmp/{i + 1:05d}.png"
            dist_frames.append(temp_name)
            frame.save(temp_name, format="PNG")
            print(f'{i + 1:05d}/{n_frames:05d}')
        print(duration)
    os.system(f'magick convert -delay {duration} tmp/*.png -loop 0 APNG:{filename_png}')


def new_test(output):
    frames = [Image.open(image) for image in glob.glob(f"tmp/*")]

    frame_one = frames[0]

    frame_one.save(
        output,
        append_images=frames,
        save_all=True,
        duration=10,
        loop=1,
    )


async def main():
    print(1)
    await folder_to_apng('tmp', 'x1.png', duration=16.6)
    print(1)


if __name__ == '__main__':
    # im1 = Image.open('example1.png')
    # im = Image.open('example.png')
    # print(im.is_animated)
    # print(im1.is_animated)
    # print(im.size)
    # print(im1.size)
    start = time()
    # dummy_test('example.gif')  # 0.37999725341796875
    # apng_test('example.gif')  # 0.38349485397338867
    # pil_test('example.gif')  # 0.38349485397338867
    magick_test('example.gif', 'example2222.png')  # 0.38349485397338867
    # asyncio.run(main())
    # new_test('output.png')  # 0.38349485397338867
    print(time()-start)

    # SeamCarving("temp.jpg").show_energy()
    # SeamCarving("test.png")._find_sum()
    # SeamCarving("test.png")._show_sum()
    # SeamCarving("test.png")._show_shrinked_pixels()

    # SeamCarving("test.png").remove_lines(50)
    # SeamCarving("test.png").remove_lines_alt(50)
    # numba

    # asyncio.run(
    #     Process().render_lottie(filename_json='../AnimatedSticker.tgs', filename='../A.png')
    # )
