from pydistort.utils.runners import run


async def gif_to_apng(filename_gif, filename_png):
    await run(['ffmpeg', '-i', filename_gif, '-f', 'apng', filename_png])


async def folder_to_apng(folder, filename_png, duration=16.67):
    await run(['ffmpeg', '-i', f'{folder}/%01d.png', '-framerate', str(1000/duration), '-plays', '0', '-f', 'apng', filename_png])
    print(1)
