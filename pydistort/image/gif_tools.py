from PIL import Image, ImageSequence


def gif_to_folder(filename, folder):
    with Image.open(filename) as image:
        duration = image.info["duration"]
        frames = ImageSequence.all_frames(image)
    for i, frame in enumerate(frames):
        temp_name = folder / f"{i + 1:05d}.png"
        frame.save(temp_name, format="PNG")
    return folder, duration
