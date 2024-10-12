# configuration file for Cute Burner Script

import os

FONT = {
    'fonts_dir': os.path.abspath("assets"),
    'font_path': os.path.abspath("assets/Vazir Black.ttf")
}

video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.mpeg', '.mpg', '.m4v']
leading_zero = 2  # appends one 0 before video index name e.g: 01

copy_right = [
    "mywebsite.com",  # website
    r"more to watch on mywebsite.com",  # start of video
    r"more to watch on mywebsite.com",  # middle of video
    r"more to watch on mywebsite.com",  # end of video
]

# include words you want to remove from text of extracted soft subtitle
words_to_remove_from_subtitle = [".com"]
