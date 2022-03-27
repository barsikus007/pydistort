# PyDistort
To install:
```bash
pip install -U git+https://github.com/barsikus007/pydistort
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
## Seam Carving py
It is very slow
## TODO
- [ ] Write readme
- [ ] Rewrite seam carving
- [ ] Rewrite seam carving py
- [ ] Add ffmpeg commands
- [ ] lottie -p parameter
