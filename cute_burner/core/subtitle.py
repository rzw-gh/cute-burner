from core.utils import Utils
import ffmpeg
import re
import os
from googletrans import Translator
from deep_translator import GoogleTranslator
from datetime import timedelta, datetime


class Subtitle:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, media_path, base_path, font_path, video_info=None, show_log=False):
        self.utils = Utils()

        self.base_path = base_path
        self.show_ffmpeg_log = not show_log
        self.media_path = os.path.join(base_path, media_path)
        self.utils.check_folder(base_path)
        self.utils.validate_file(self.media_path)
        self.font_path = font_path
        self.utils.validate_file(self.font_path)
        self.media_duration = None
        self.dialogues = None

        if self.utils.get_file_extension(media_path) == "mkv":
            self.video_stream, self.audio_stream, self.subtitle_streams, self.media_duration, self.video_info = self.utils.media_streams(
                self.media_path)
        elif video_info:
            self.video_stream, self.audio_stream, self.subtitle_streams, self.media_duration, self.video_info = video_info

    def extract_subtitle(self, index=0):
        """Extracts embedded first subtitle from media"""
        if not self.video_info:
            raise ValueError("you need to provide video info in order to use extract_subtitle method")
        subtitle_streams = [stream for stream in self.video_info['streams'] if stream['codec_type'] == 'subtitle']

        if len(subtitle_streams) == 0:
            raise ValueError("no subtitle found to extract")

        sub_output = self.utils.append_random_name(f"{self.base_path}/extracted_sub.ass")

        try:
            ffmpeg.input(self.media_path, sub_charenc='utf-8').output(sub_output, map='0:{}'.format(subtitle_streams[index]['index']), scodec='ass').run(
                overwrite_output=True, quiet=self.show_ffmpeg_log)
            self.media_path = sub_output
        except ffmpeg.Error as e:
            raise ValueError(e)

        return self

    def remove_words(self, words_to_remove_from_subtitle):
        if not self.media_duration:
            raise ValueError("you need to provide video info in order to use remove_words method")

        for i_loop in range(40):
            self.extract_dialogues()
            with open(self.media_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            dialogue_index = 0
            new_lines = []
            for i, line in enumerate(lines):
                line = self.utils.arabic_to_persian(line)
                add_line = True
                if line.startswith("Dialogue:"):
                    match = re.compile(r"Dialogue: \d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),").search(line)
                    current_start_time = self.utils.parse_time(match.group(1)).time()
                    current_start_seconds = current_start_time.hour * 3600 + current_start_time.minute * 60 + current_start_time.second
                    current_end = self.utils.parse_time(match.group(2))
                    current_end_time = current_end.time()
                    current_end_seconds = current_end_time.hour * 3600 + current_end_time.minute * 60 + current_end_time.second

                    if dialogue_index > 20:
                        prev_end = self.dialogues[dialogue_index - 1]['timing'][1]
                        prev_end_time = self.dialogues[dialogue_index - 1]['timing'][1].time()
                        prev_end_seconds = prev_end_time.hour * 3600 + prev_end_time.minute * 60 + prev_end_time.second
                        dialogue_index += 1
                        if timedelta(seconds=current_start_seconds) < timedelta(seconds=prev_end_seconds) and prev_end != current_end:
                            continue
                        elif current_start_seconds > self.media_duration or current_end_seconds > self.media_duration:
                            continue
                    elif dialogue_index < 3:
                        next_end = self.dialogues[dialogue_index + 1]['timing'][1]
                        next_end_time = self.dialogues[dialogue_index + 1]['timing'][1].time()
                        next_end_seconds = next_end_time.hour * 3600 + next_end_time.minute * 60 + next_end_time.second
                        dialogue_index += 1
                        if timedelta(seconds=current_start_seconds) > timedelta(seconds=next_end_seconds) and next_end != current_end:
                            continue
                    else:
                        dialogue_index += 1

                    if current_start_seconds > self.media_duration or current_end_seconds > self.media_duration:
                        continue

                for index, word in enumerate(words_to_remove_from_subtitle):
                    if word in rf"{line}":
                        add_line = False
                        break

                if bool(re.compile(r'{[^}]*\bm\s+\d').search(line)):
                    continue

                if add_line:
                    new_lines.append(line)

            with open(self.media_path, 'w', encoding='utf-8') as main_file:
                main_file.writelines(new_lines)

        return self

    def extract_dialogues(self, prev_dialogue=1, next_dialogue=1):
        self.utils.validate_file(self.media_path)

        dialogues = []

        with open(self.media_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        format_line = self.utils.get_dialogue_format(lines)
        text_index = self.utils.get_text_field_index(format_line)

        regex_pattern = r"Dialogue: " + r"(?:[^,]*,)" * text_index + r"(.*)"

        dialogue_index = 0
        for i, line in enumerate(lines):
            if line.startswith("Dialogue:"):
                match = re.search(regex_pattern, line)
                if match:
                    en_dialogue = match.group(1).strip()
                    en_dialogue = en_dialogue.replace("\\N", " ")

                    match2 = re.compile(r"Dialogue: \d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),").search(line)
                    current_start = self.utils.parse_time(match2.group(1))
                    current_end = self.utils.parse_time(match2.group(2))

                    timing = [current_start, current_end]
                    dialogues.append({"en": en_dialogue, "timing": timing, "prev_dialogues": [], "next_dialogues": [], "fa": "", "fa_edited": ""})
                    dialogue_index += 1

        for i, dialogue in enumerate(dialogues):
            dialogue["prev_dialogues"] = [dialogues[i - (pi + 1)]['en'] for pi in range(prev_dialogue) if i - (pi + 1) >= 0]
            dialogue["next_dialogues"] = [dialogues[i + (ni + 1)]['en'] for ni in range(next_dialogue) if i + (ni + 1) < len(dialogues)]

        self.dialogues = dialogues

        return dialogues

    def translate_subtitle(self):
        self.utils.validate_file(self.media_path)

        if not self.dialogues:
            self.extract_dialogues()

        # proxies = {
        #     'http': 'http://your_proxy_ip:your_proxy_port',
        #     'https': 'https://your_proxy_ip:your_proxy_port'
        # }
        # translator = Translator(proxies=proxies)
        translator = Translator()

        with open(self.media_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        format_line = self.utils.get_dialogue_format(lines)
        text_index = self.utils.get_text_field_index(format_line)

        regex_pattern = r"Dialogue: " + r"(?:[^,]*,)" * text_index + r"(.*)"

        new_lines = []

        dialogue_index = 0
        for i, line in enumerate(lines):
            if line.startswith("Dialogue:"):
                match = re.search(regex_pattern, line)
                if match:
                    try:
                        en_dialogue = self.utils.concat_dialogue(self.dialogues[dialogue_index])
                        fa_dialogue = translator.translate(en_dialogue, src='en', dest='fa').text
                        fa_dialogue = fa_dialogue.replace("\\", r"\\")
                        fa_dialogue = re.findall(r'\[~](.*?)\[~]', fa_dialogue)[0]
                        fa_dialogue = self.utils.handle_long_dialogue(fa_dialogue)
                    except Exception as e:
                        try:
                            en_dialogue = self.utils.concat_dialogue(self.dialogues[dialogue_index])
                            fa_dialogue = GoogleTranslator(source='en', target='fa').translate(en_dialogue)
                            fa_dialogue = fa_dialogue.replace("\\", r"\\")
                            fa_dialogue = re.findall(r'\[~](.*?)\[~]', fa_dialogue)[0]
                            fa_dialogue = self.utils.handle_long_dialogue(fa_dialogue)
                        except Exception as e:
                            fa_dialogue = "بدون ترجمه"
                    line = re.sub(rf"(Dialogue: (?:[^,]*,){{{text_index}}}).*", r"\1" + fa_dialogue, line)
                    line = line.replace("~", r"\N")
                    dialogue_index += 1
                print(f"{dialogue_index}/{len(self.dialogues)}")
            new_lines.append(line)

        with open(self.media_path, 'w', encoding='utf-8') as main_file:
            main_file.writelines(new_lines)

        return self

    def customize_subtitle(self, sub_copyright="", intro="", opening="", ending=""):
        if not self.media_duration:
            raise ValueError("you need to provide video info in order to use customize_subtitle method")
        self.utils.check_folder(self.media_path)

        if not self.dialogues:
            self.extract_dialogues()

        gap_seconds = 20
        gaps = []
        for i, dialogue in enumerate(self.dialogues):
            dialogue = dialogue['timing']
            previous_end = self.dialogues[i - 1]['timing'][1]
            current_start = dialogue[0]
            current_end = dialogue[1]
            current_end_time = dialogue[1].time()
            current_end_seconds = current_end_time.hour * 3600 + current_end_time.minute * 60 + current_end_time.second
            dialogue_gap = current_start - previous_end
            intro_time = datetime.strptime('0:00:10', '%H:%M:%S')

            if i + 1 == len(self.dialogues) and self.media_duration > current_end_seconds and timedelta(
                    seconds=self.media_duration - current_end_seconds) > timedelta(seconds=gap_seconds):
                end = (current_end + timedelta(seconds=self.media_duration - current_end_seconds))

                gaps.append(
                    {"start": f"{current_end.hour}:{current_end.minute:02}:{current_end.second:02}",
                     "end": f"{end.hour}:{end.minute:02}:{end.second:02}"})
            elif dialogue_gap > timedelta(seconds=gap_seconds) and current_start > intro_time:
                gaps.append(
                    {"start": f"{previous_end.hour}:{previous_end.minute:02}:{previous_end.second:02}",
                     "end": f"{current_start.hour}:{current_start.minute:02}:{current_start.second:02}"})

        append = [
            r"Dialogue: 0,0:00:00.00,0:00:10.00,Default,,0,0,0,,{\fad(3000,3000)\an8\fs50\c&H26D9D9&\3c&H000000&}" + intro
        ]

        for i, gap in enumerate(gaps):
            start = gap['start']
            end = gap['end']

            if i == 0:
                append.append(
                    f"Dialogue: 0,{start}.00,{end}.00" + r",Default,,0,0,0,,{\fad(3000,3000)\an8\fs50\c&H26D9D9&\1a&H00&}" + opening)
            elif i + 1 == len(gaps):
                append.append(
                    f"Dialogue: 0,{start}.00,{end}.00" + r",Default,,0,0,0,,{\fad(3000,3000)\an8\fs50\c&H26D9D9&\1a&H00&}" + ending)

        data = {
            "player_res": [
                "PlayResX: 1920",
                "PlayResY: 1080",
                "ScaledBorderAndShadow: yes"
            ],
            "script_info": [
                f"; Script Copy Right: {sub_copyright}",
            ],
            "font": [self.font_path],
            "append": append
        }
        self.utils.write_line_into_file(self.media_path, data)

        return self

    def time_shift(self, shift_seconds: float = 5.0):
        """
        Shifts time for subtitles by a specified number of seconds.

        Parameters:
        shift_seconds (float): Number of seconds to shift the subtitles. Positive for forward, negative for backward.
        """
        with open(self.media_path, 'r+', encoding='utf-8') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()

            # Regex to match dialogue lines with timestamps
            dialogue_regex = re.compile(r"Dialogue: \d+,(\d:\d\d:\d\d\.\d+),(\d:\d\d:\d\d\.\d+),")

            for line in lines:
                match = dialogue_regex.match(line)
                if match:
                    start_time, end_time = match.group(1), match.group(2)
                    new_start_time = self.utils.shift_time(start_time, shift_seconds)
                    new_end_time = self.utils.shift_time(end_time, shift_seconds)
                    line = line.replace(start_time, new_start_time, 1).replace(end_time, new_end_time, 1)
                file.write(line)

        return self

    def change_title(self, title):
        """Changes subtitle name"""
        title = self.utils.check_extension(title, "ass")
        path = f"{self.base_path}/{title}"
        if os.path.exists(path):
            new_path = self.utils.append_random_name(path)
            os.rename(path, new_path)
            os.rename(new_path, path)
        else:
            os.rename(self.media_path, path)

        return self

    def convert_srt_to_ass(self, i, leading_zero):
        (
            ffmpeg
            .input(self.media_path)
            .output(f"{self.base_path}/{self.utils.append_leading_zero(leading_zero, i + 1)}.ass", format='ass')
            .run(overwrite_output=True)
        )

    def return_path(self):
        return self.media_path
