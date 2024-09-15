# Cute Burner

This is a Video Encoder/Embeder script built using Python and FFMPEG library.

## Usage

this script developed mostly to enhance and automate what FFMPEG library can do with the power of Python. 
here's list of things we can do with script:
- Encoding videos (h265 or av1 codecs, 10bit or 8bit color depths, converting resolutions 480, 720, 1080)
- Burning subtitle onto videos (HardSub)
- Extracting/Removing soft subtitle from videos
- Watermarking videos
- Trimming videos

## Prerequisites

Make sure you have the following installed on your system:

- Python 3.x
- ffmpeg (you can find tutorials on installing ffmpeg on internet. note after installing, ffmpeg should be executable through your terminal)

## Installation

Follow these steps to set up the project locally.

### 1. Setup

after clonning this repo head over to cute_burner folder and use `pip install -r requirements.txt` to install all required packages for python.

### 2. Configuration
1.edit `core/config.py` as you need

2.put your videos inside `assets/media`

# 3. Examples
### 1.Video
```bash
from core.video import Video
from core import config

# edit these configurations on your needs in core/config.py file
font_path = config.FONT['font_path']
fonts_dir = config.FONT['fonts_dir']

base_path = "assets/media"
media_path = "test.mkv"

video = Video(media_path, font_path, fonts_dir, base_path=base_path, show_log=True)
(
    video
    .trim(0, 20)  # trim media from second 0 to second 20
    .remove_subtitles()  # removes all soft subtitles from media
    .watermark(watermark="watermark text", position="bottom_left", font_size=16, timing=15)  # watermarks at position bottom left for first 15 seconds
    .encode(resolution="480", color_depth="10bit", codec="h265")  # encode at 480 resolution, 10bit color depth and h265 codec
    .hardcode_subtitle(media_path)  # hardsub test.ass
    .change_title("test2.mkv")  # change media file name
    .execute()
)
```

### 1.Subtitle
```bash
from core.subtitle import Subtitle
from core import config

# edit these configurations on your needs in core/config.py file
words_to_remove_from_subtitle = config.words_to_remove_from_subtitle
copy_right = config.copy_right
font_path = config.FONT['font_path']
fonts_dir = config.FONT['fonts_dir']

base_path = "assets/media/shadow"
media_path = "test.mkv"

subtitle = Subtitle(media_path, base_path, font_path)
(
    subtitle
    .extract_subtitle()  # extracts soft subs if exists from media
    .remove_words(words_to_remove_from_subtitle)  # removes words from subtitle dialogues
    .customize_subtitle(*copy_right)  # adds your copy right to start, middle and end of video
    .change_title("test.ass")  # change subtitle file name
)
```
