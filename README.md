# ASCII Video Player for Termux

**LYNX · FTGAMERV2**

![GitHub stars](https://img.shields.io/github/stars/ftgamer2/ASCII-Video-Player?style=for-the-badge) ![GitHub forks](https://img.shields.io/github/forks/ftgamer2/ASCII-Video-Player?style=for-the-badge) ![GitHub issues](https://img.shields.io/github/issues/ftgamer2/ASCII-Video-Player?style=for-the-badge) ![GitHub license](https://img.shields.io/github/license/ftgamer2/ASCII-Video-Player?style=for-the-badge)

[![Termux](https://img.shields.io/badge/Termux-000000?style=for-the-badge&logo=termux&logoColor=white)](https://termux.com/) [![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

Convert video into real-time ASCII art in an Android terminal, with frame-accurate playback and parallel processing.

## Preview

Example console output:

```text
Video path: /sdcard/video.mp4
ASCII width [80]: 100
Video info:
  Resolution: 1920x1080
  FPS: 30.00
  Duration: 120.5s
  Estimated frames: 3615
  Estimated render time: 18.1s
```

## Features

- Ultra-fast parallel rendering with multi-threading
- Frame-accurate playback with precise timing
- Smart caching for instant replay
- Automatic dependency installation
- Real-time FPS, drift, and progress statistics
- Customizable ASCII density (10 levels, dark to light)
- Termux-optimized Android workflow

## Quick start

```bash
git clone https://github.com/ftgamer2/ASCII-Video-Player.git
cd ASCII-Video-Player
chmod +x player.py
python player.py
```

### One-line installation

```bash
git clone https://github.com/ftgamer2/ASCII-Video-Player.git && cd ASCII-Video-Player && chmod +x player.py && python player.py
```

## Installation

### Automatic (recommended)

The script installs dependencies when needed. Run:

```bash
python player.py
```

### Manual (Termux)

```bash
pkg update && pkg upgrade -y
pkg install python ffmpeg -y
pip install numpy pillow
```

## Usage

```bash
# Interactive mode (recommended)
python player.py

# Play a video directly
python player.py /sdcard/DCIM/Camera/video.mp4

# Set a custom width
python player.py video.mp4 --width 60
```

Command-line form:

```text
python player.py [video_path] [--width WIDTH]
```

## Configuration

The README notes these settings in the configuration section of player.py:

```python
# ASCII characters (dark to light)
ASCII_CHARS = " .:-=+*#%@"

# Default terminal width
DEFAULT_WIDTH = 80

# Number of parallel workers
MAX_WORKERS = 2

# Render cache directory
RENDER_DIR = "/data/data/com.termux/files/usr/tmp/ascii_render"
```

## Performance benchmarks

| Video | Render time | Playback FPS | Accuracy |
|---|---:|---:|---:|
| 480p (30s) | 2.1s | 29.98 | 99.93% |
| 720p (60s) | 8.4s | 29.99 | 99.97% |
| 1080p (30s) | 6.7s | 29.95 | 99.83% |

## How it works

1. FFmpeg extracts video frames.
2. Frames are converted to ASCII using parallel processing.
3. ASCII frames are cached for future playback.
4. Frames are displayed with timing intended to match the original FPS.

## Troubleshooting

**FFmpeg not found**

```bash
pkg install ffmpeg -y
```

**Python modules missing**

```bash
pip install numpy pillow
```

**Slow performance on low-end devices**

- Reduce MAX_WORKERS to 1 in the script.
- Use a smaller ASCII width (40–60).
- Close other apps running in Termux.

**Can't access videos on SD card**

```bash
termux-setup-storage
```

**Memory error**

- Use shorter videos (under 2 minutes).
- Reduce ASCII width.
- Restart Termux.

## Project structure

```text
ASCII-Video-Player/
├── player.py   # Main ASCII video player
├── README.md   # Documentation
├── LICENSE     # MIT License
└── vid.mp4     # Example video for testing
```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a pull request.

## License

Distributed under the MIT License. See LICENSE for details.

## Author and acknowledgments

**ftgamer2** · [@ftgamer2](https://github.com/ftgamer2)

Thanks to FFmpeg, Termux, and the Python community.

## Support

If you find this project useful, consider starring the repository.

---

**LYNX · FTGAMERV2**
