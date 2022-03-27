import os
from pathlib import Path

from PIL import Image, ImageSequence

__all__ = ['jpeg_lq', 'image_to_png', 'png_to_jpeg_lq', 'gif_to_folder']


def jpeg_lq(filename):
    with Image.open(filename) as img:
        img.save(filename, quality=1)
    return filename


def image_to_png(filename):
    filename_png = Path(filename).with_suffix('.png')
    with Image.open(filename) as image:
        image.save(filename_png)
    os.remove(filename)
    return filename_png


def png_to_jpeg_lq(filename):
    background_colors = [
        (0, 0, 0),
        (96, 96, 96),
        (51, 119, 96),
        (255, 255, 255),
    ]
    filename_jpg = Path(filename).with_suffix('.jpg')
    with Image.open(filename) as img:
        img.convert('RGB').save(filename_jpg, quality=1)
    with Image.open(filename_jpg) as img:
        new_img = Image.new('RGBA', img.size)
        new_img.putdata([(255, 255, 255, 0)  # noqa
                         if item in background_colors else
                         (*item, 255)
                         for item in img.getdata()])
        new_img.save(filename)
    os.remove(filename_jpg)
    return filename


def gif_to_folder(filename, folder):
    with Image.open(filename) as image:
        duration = image.info['duration']
        frames = ImageSequence.all_frames(image)
    for i, frame in enumerate(frames):
        temp_name = folder / f'{i + 1:05d}.png'
        frame.save(temp_name, format='PNG')
    return folder, duration
