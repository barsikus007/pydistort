from pathlib import Path

from pydistort.utils.runners import run


def make_apng(dist_frames, duration, filename_png, lib='apng') -> None:  # TODO
    # os.system(f'magick convert -delay {duration} tmp/*.png -loop 0 APNG:{filename_png}')
    # os.system(f'ffmpeg -framerate {1000/duration} -i tmp/%05d.png -plays 0 -f apng {filename_png} -y')
    if lib == 'apng':
        from apng import APNG
        return APNG.from_files(dist_frames, delay=duration).save(filename_png)
    if lib == 'pil':
        from PIL import Image
        frame, *frames = [Image.open(image) for image in dist_frames]
        return frame.save(
            filename_png,
            append_images=frames,
            save_all=True,
            duration=duration,
            loop=0,
        )


def gif_to_apng_(filename_gif: str | Path):
    import os
    from pathlib import Path
    from tempfile import mkdtemp

    from apng import APNG
    from pydistort.image import gif_to_folder

    filename_png = Path(filename_gif).with_suffix('.png')
    folder, duration = gif_to_folder(filename_gif, Path(mkdtemp(dir='.')))
    os.remove(filename_gif)
    with open(filename_png, 'wb'):
        APNG.from_files([*Path(folder).iterdir()], delay=duration).save(filename_png)
    return filename_png


async def gif_to_apng(filename_gif: str | Path, filename_png: str | Path):
    await run(['ffmpeg', '-i', filename_gif, '-f', 'apng', filename_png])
    return filename_png


async def folder_to_apng(folder: str | Path, filename_png, duration=16.67):
    await run(['ffmpeg', '-i', f'{folder}/%05d.png', '-framerate', str(1000/duration), '-plays', '0', '-f', 'apng', filename_png])
    return filename_png
