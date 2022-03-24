import asyncio

from pydistort.image.seam_carving import SeamCarving


if __name__ == '__main__':
    SeamCarving("temp.jpg").show_energy()
    # SeamCarving("test.png")._find_sum()
    # SeamCarving("test.png")._show_sum()
    # SeamCarving("test.png")._show_shrinked_pixels()

    # SeamCarving("test.png").remove_lines(50)
    # SeamCarving("test.png").remove_lines_alt(50)
    # numba

    # asyncio.run(
    #     Process().render_lottie(filename_json='../AnimatedSticker.tgs', filename='../A.png')
    # )
