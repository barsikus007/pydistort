# PyDistort

[![PyPI - Version](https://img.shields.io/pypi/v/pydistort.svg)](https://pypi.org/project/pydistort)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydistort.svg)](https://pypi.org/project/pydistort)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)
- [Usage](#usage)

## Installation

```console
pip install pydistort
```
Dev build
```bash
# without optional dependencies:
pip install -U git+https://github.com/barsikus007/pydistort
# with optional dependencies:
pip install -U "pydistort[all]@ git+https://github.com/barsikus007/pydistort"
```
For distortion, you need to install imagemagick
#### Linux (Ubuntu)
```bash
sudo apt install imagemagick
```
#### Windows
You can do this via scoop.sh
```pwsh
scoop install imagemagick
```
For video, gif and apng procession, you need to install ffmpeg
#### Linux (Ubuntu)
```bash
sudo apt install ffmpeg
```
#### Windows
You can do this via scoop.sh
```pwsh
scoop install ffmpeg
```
For lottie->gif procession you need to install gtk
#### Linux (Ubuntu)
```bash
sudo apt install libgtk-3-0
```
#### Windows
You can do this via scoop.sh
```pwsh
scoop install msys2
msys2  # then exit in msys shell
msys2 -c "pacman -S mingw-w64-x86_64-gtk3 --noconfirm"
```

## License

`pydistort` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Usage

```python
from pydistort.image.seam_carving import distort

await distort('image.png', 60)
```

## TODO for 0.1.0 release
- [ ] Write readme
- [ ] Rewrite seam carving
- [ ] Rewrite seam carving py
- [ ] Maybe rewrite to Glaxnimate
- [ ] Add ffmpeg commands
- [ ] lottie -p parameter
- [ ] https://github.com/bodqhrohro/giftolottie
- [ ] https://github.com/bunkahle/gif2numpy
- [ ] os.remove to unlink
