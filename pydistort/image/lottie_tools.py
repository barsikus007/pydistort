import sys

from pydistort.utils.runners import run


scripts = sys.executable.split('python.exe')[0]


async def render_lottie(filename_json, filename, quiet=True):
    command = [sys.executable, f'{scripts}lottie_convert.py', filename_json, filename, '--fps', '60']
    if not quiet:
        command.append('-p')
    return await run(command, quiet=quiet)
