import os
import asyncio

from pydistort import Process
from pydistort.image import seam_carving


async def main():
    proc = Process()
    # os.system('wsl cp example.gif example1.gif')
    # print(await seam_carving.distort_gif('example1.gif', quiet=False))
    # print(await proc.distort_gif('example1.gif'))
    # print(await proc.distort_folder('tmp', quiet=False))
    # print(await proc.distort_lottie_gif('tgs.json', False))
    # print(await proc.render_lottie('tgs.tgs', 'tgs.gif', quiet=False))


if __name__ == '__main__':
    asyncio.run(main())

