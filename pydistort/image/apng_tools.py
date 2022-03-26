from pydistort.utils.runners import run


def gif_to_apng_(filename_gif):
    import os
    from pathlib import Path
    from tempfile import mkdtemp

    from apng import APNG
    from pydistort.image import gif_tools

    filename_png = Path(filename_gif).with_suffix('.png')
    folder, duration = gif_tools.gif_to_folder(filename_gif, Path(mkdtemp(dir='.')))
    os.remove(filename_gif)
    with open(filename_png, 'wb'):
        APNG.from_files([*Path(folder).iterdir()], delay=duration).save(filename_png)
    return filename_png


async def gif_to_apng(filename_gif, filename_png):
    await run(['ffmpeg', '-i', filename_gif, '-f', 'apng', filename_png])
    return filename_png


async def folder_to_apng(folder, filename_png, duration=16.67):
    await run(['ffmpeg', '-i', f'{folder}/%01d.png', '-framerate', str(1000/duration), '-plays', '0', '-f', 'apng', filename_png])
    return filename_png
