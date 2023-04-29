from pathlib import Path

from pydistort.utils.runners import run, probe


__all__ = ['webm_to_folder', 'folder_to_webm']


async def webm_to_folder(filename, folder: str | Path):
    info = await probe(filename)
    width = info['streams'][0]['width']

    duration = float(info['format']['duration'])
    framerate = info['streams'][0]['avg_frame_rate']
    framerate = int(framerate.split('/')[0]) / int(framerate.split('/')[1])
    total_frames = int(duration * framerate)

    for i in range(total_frames):
        output_filename = folder / f'{i + 1:05d}.png'
        time_to_frame = i / framerate

        command = ['ffmpeg', '-i', filename,
                   '-ss', str(time_to_frame),
                   '-vf', f'scale={width}:-1',
                   '-vframes', '1',
                   '-q:v', '1', str(output_filename)]

        await run(command, quiet=True)
    return folder, duration


async def folder_to_webm(folder: str | Path, filename_webm, framerate):
    await run(
        ['ffmpeg', '-y',
         '-i', f'{folder}/%05d.png',
         '-framerate', str(framerate),
         '-pix_fmt', 'yuv420p',
         filename_webm], quiet=True)
    return filename_webm
