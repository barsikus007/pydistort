import shlex
import asyncio

from pydistort.utils.libs import json


async def run(command: list, executable: str = None, stdin=None, quiet=True, log_stdout=False) -> bytes:
    command_string = f'{executable} {shlex.join(command)}' if executable else shlex.join(command)
    proc = await asyncio.create_subprocess_shell(
        command_string,
        stdin=asyncio.subprocess.PIPE if stdin else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate(stdin)

    if not quiet:
        print(f'[{command_string!r} exited with {proc.returncode}]')
        if stderr:
            print(f'[stderr]\n{stderr.decode(errors="ignore")}')
        if stdout and log_stdout:
            print(f'[stdout]\n{stdout.decode(errors="ignore")}')
    return stdout


async def probe(filename: str, stdin=None) -> dict:
    return json.loads(
        (
            await run(['ffprobe', '-show_format', '-show_streams', '-of', 'json', filename], stdin=stdin)
        ).decode()
    )
