import os
import random
import string
import tqdm
import time
import shutil
import textwrap
import ffmpeg
from datetime import datetime
import mysql.connector
from mysql.connector import Error


class Utils:
    _instance = None
    progress_bar_current_time = 0

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def clear_console():
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('printf "\033c"')

    @staticmethod
    def parse_time(time_str):
        return datetime.strptime(time_str, "%H:%M:%S.%f")

    @staticmethod
    def get_now():
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

    def append_random_name(self, file, suffix=None):
        last_dot_index = file.rfind(".")

        if last_dot_index != -1:
            text_without_extension = file[:last_dot_index]
            extension = file[last_dot_index + 1:]
            if suffix:
                file = f"{text_without_extension}_{suffix}_{self.generate_random_name()}.{extension}"
            else:
                file = f"{text_without_extension}_{self.generate_random_name()}.{extension}"

        return file

    @staticmethod
    def remove_needle(haystack, needles):
        for needle in needles:
            haystack = haystack.replace(needle, "")
        return haystack

    @staticmethod
    def append_prefix(text, prefix):
        if text.strip():
            if text is None:
                return text
            if prefix.endswith("/"):
                return f"{prefix}{text}"
            else:
                return f"{prefix}/{text}"
        else:
            return text

    @staticmethod
    def append_suffix(text, suffix):
        if text.strip():
            if text is None:
                return text
            if not suffix.endswith("/"):
                return f"{text}{suffix}"
            else:
                return f"{text}/{suffix}"
        else:
            return text

    @staticmethod
    def arabic_to_persian(text):
        arabic_to_persian_dict = {
            'ي': 'ی',
            'ك': 'ک',
            'ۀ': 'ه',
            'ة': 'ه',
            'ى': 'ی'
        }

        for arabic_char, persian_char in arabic_to_persian_dict.items():
            text = text.replace(arabic_char, persian_char)

        return text

    def write_line_into_file(self, file_path: str, data: dict):
        self.validate_file(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for i, line in enumerate(lines):
            pass_line = False
            if "script_info" in data and '[Script Info]' in lines[i - 1]:
                new_lines.append('\n'.join([f"{item}" for item in data['script_info']]) + '\n')
            elif "player_res" in data and 'Styles]' in line and 'Format:' in lines[i + 1]:
                new_lines.append('\n'.join([f"{item}" for item in data['player_res']]) + '\n')
            elif "font" in data:
                font_name = data['font'][0]
                font_name = os.path.basename(self.remove_file_extension(font_name))
                if 'Style:' in line:
                    pass_line = True
                elif 'Format:' in line and 'Styles]' in lines[i - 1]:
                    new_lines.append(
                        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
                    )
                    new_lines.append(
                        '\n' + f"Style: Default,{font_name},70,&H26D9D9&,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2.50001,0,2,20,20,30,1"
                    )
                    pass_line = True
                elif '[Events]' in line:
                    new_lines.append('\n\n' + '[Fonts]' + '\n' + f"fontname: {font_name}" + '\n\n')

            if not pass_line:
                new_lines.append(line)
            if "append" in data and i + 1 == len(lines):
                new_lines.append('\n'.join([f"{item}" for item in data['append']]) + '\n')

        with open(file_path, 'w', encoding='utf-8') as main_file:
            main_file.writelines(new_lines)

    @staticmethod
    def get_file_extension(file, default="mkv"):
        last_dot_index = file.rfind(".")

        if last_dot_index != -1:
            extension = file[last_dot_index + 1:]
        else:
            extension = default

        return extension

    def check_extension(self, file, default):
        # common_extensions = [
        #     # Video extensions
        #     'mkv', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'vob', 'ogv', 'ogg', 'drc', 'gif', 'gifv', 'mng',
        #     'mts', 'm2ts', 'ts', 'm4v', '3gp', '3g2', 'mxf', 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b',
        #     # Picture extensions
        #     'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'tif', 'svg', 'webp', 'heif', 'heic',
        #     # Subtitle extensions
        #     'srt', 'sub', 'sbv', 'vtt', 'ass', 'ssa', 'mpl',
        #     # Audio extensions
        #     'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac', 'opus'
        # ]
        parts = file.split('.')
        
        if len(parts) > 1:
            if default != parts[-1]:
                file = self.remove_file_extension(file)
                file = f"{file}.{default}"
        else:
            file = f"{file}.{default}"
        return file

    @staticmethod
    def remove_file_extension(file, default=None):
        last_dot_index = file.rfind(".")

        if last_dot_index != -1:
            text_without_extension = file[:last_dot_index]
        else:
            text_without_extension = file

        if default:
            text_without_extension += f".{text_without_extension}"

        return text_without_extension

    @staticmethod
    def time_to_seconds(time_str):
        hours, minutes, seconds = map(float, time_str.split(':'))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds

    @staticmethod
    def generate_random_name(word_length=6, num_length=4):
        word = ''.join(random.choices(string.ascii_lowercase, k=word_length))
        number = ''.join(random.choices(string.digits, k=num_length))
        random_name = word + number
        return random_name

    @staticmethod
    def validate_file(path, delete_if_exists=False):
        if delete_if_exists:
            os.remove(path) if os.path.exists(path) else None
        elif not os.path.exists(path):
            err = f"{path} not found"
            raise ValueError(err)

    @staticmethod
    def check_folder(path, delete_if_exists=False):
        if not delete_if_exists:
            if path and not os.path.exists(path):
                os.makedirs(path)
        else:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)

    @staticmethod
    def calc_image_position(position, video_width, image_width, video_height, image_height, padding):
        if position == 'bottom_left':
            x = padding
            y = video_height - image_height - padding
        elif position == 'bottom_right':
            x = video_width - image_width - padding
            y = video_height - image_height - padding
        elif position == 'top_left':
            x = padding
            y = padding
        else:  # top_right
            x = video_width - image_width - padding
            y = padding
        return x, y

    @staticmethod
    def calc_text_position(position, video_width, video_height, text, font_size, padding):
        # Calculate the width and height of the text
        # For simplicity, let's assume a fixed character width and height
        char_width = font_size * 0.6  # Approximate width of a character
        char_height = font_size
        text_width = len(text) * char_width
        text_height = char_height

        if position == 'bottom_left':
            x = padding
            y = video_height - text_height - padding + 2
        elif position == 'bottom_right':
            x = video_width - text_width - padding
            y = video_height - text_height - padding
        elif position == 'top_left':
            x = padding
            y = padding
        else:  # top_right
            x = video_width - text_width - padding
            y = padding
        return x, y

    @staticmethod
    def media_streams(media_path):
        input_stream = ffmpeg.input(media_path)
        video_stream = input_stream.video or None
        audio_stream = input_stream.audio or None

        media_info = ffmpeg.probe(media_path)
        subtitle_streams = [input_stream[str(stream['index'])] for stream in media_info['streams'] if stream['codec_type'] == 'subtitle']
        media_duration = float(media_info["format"]["duration"])

        return [video_stream, audio_stream, subtitle_streams, media_duration, media_info]

    def generate_progress_bar(self, media_duration, media_output_path, progress_file, rest=1, remove_media=None):
        self.progress_bar_current_time = 0
        keys = ["progress", "frame", "fps", "stream_0_0_q", "bitrate", "total_size",
                "out_time_us", "out_time_ms", "out_time", "dup_frames", "drop_frames", "speed"]

        progress_bar = tqdm.tqdm(total=media_duration, initial=0, unit="s",
                                 desc=f"Processing {media_output_path}",
                                 ascii=True,
                                 bar_format='{desc} {percentage:3.0f}% | {n:.2f}s/{total:.2f}s |{rate_fmt}{postfix}')

        i = 0
        while True:
            if not os.path.exists(progress_file):
                i = i + 1
                if i >= 10:
                    break
                time.sleep(rest)
            else:
                last_values = {}
                with open(progress_file, 'r') as file:
                    reversed_lines = reversed(file.readlines())

                    for line in reversed_lines:
                        key, value = line.strip().split("=")

                        if key in keys:
                            last_values[key] = value

                        if all(key in last_values for key in keys):
                            break

                if len(last_values) > 0:
                    if last_values['progress'] == 'end':
                        progress_bar.close()
                        if remove_media and len(remove_media) > 0:
                            for media in remove_media:
                                os.remove(media)
                        os.remove(progress_file)
                        break
                    if last_values['out_time'] != "N/A" and last_values['speed'] != "N/A":
                        self.progress_bar_current_time = self.time_to_seconds(last_values['out_time'])
                        speed = float(last_values['speed'].replace('x', ''))
                        remaining_time = (media_duration - self.progress_bar_current_time) / speed
                        estimated_finish_time = time.strftime("%H:%M:%S", time.gmtime(remaining_time))
                        progress_bar.set_description(
                            f"Processing {media_output_path} (Est Finish {estimated_finish_time})"
                        )
                else:
                    self.progress_bar_current_time = 0

                progress_bar.n = self.progress_bar_current_time
                progress_bar.refresh()

                time.sleep(rest)

    @staticmethod
    def handle_long_dialogue(dialogue, max_width=45):
        lines = textwrap.wrap(dialogue, width=max_width)
        if len(lines) > 1:
            for i, line in enumerate(lines):
                if i + 1 == len(lines) and len(line) <= 18:
                    lines[len(lines) - 1] += line
                    lines.pop(i)

            if len(lines) > 1:
                return r"~".join(lines)
            else:
                return dialogue
        else:
            return dialogue

    @staticmethod
    def get_dialogue_format(lines):
        for i, line in enumerate(lines):
            if "Format:" in line and i > 0 and "[Events]" in lines[i - 1]:
                return line.strip()
        raise ValueError("No Format line found in the subtitle file.")

    @staticmethod
    def get_text_field_index(format_line):
        fields = format_line.strip().split(": ")[1].split(", ")
        if len(fields) == 1:
            fields = fields[0].split(",")
        try:
            return fields.index("Text")
        except ValueError:
            raise ValueError("No 'Text' field found in the Format line.")

    @staticmethod
    def shift_time(time_str, shift_seconds):
        """Shift a timestamp by the given number of seconds."""
        hours, minutes, seconds = time_str.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        total_seconds += shift_seconds

        # Handle negative time shift
        if total_seconds < 0:
            total_seconds = 0

        # Convert back to hours, minutes, and seconds
        hours = int(total_seconds // 3600)
        total_seconds %= 3600
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60

        return f"{hours:01}:{minutes:02}:{seconds:05.2f}"

    @staticmethod
    def concat_dialogue(dialogue):
        dialogue_text = ""
        for i, prev_dialogue in enumerate(dialogue['prev_dialogues']):
            dialogue_text += ' ' if len(dialogue_text) else ''
            dialogue_text += prev_dialogue

        dialogue_text += f"[~]{dialogue['en']}[~]"

        for i, next_dialogue in enumerate(dialogue['next_dialogues']):
            dialogue_text += ' ' if len(dialogue_text) else ''
            dialogue_text += next_dialogue
        return dialogue_text

    @staticmethod
    def insert_row_into_table(auth, table, data):
        connection = None  # Initialize the connection variable
        try:
            # Establish the connection
            connection = mysql.connector.connect(**auth)

            if connection.is_connected():
                cursor = connection.cursor()

                # Form the SQL query
                placeholders = ", ".join(["%s"] * len(data))
                columns = ", ".join(data.keys())
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

                # Execute the query
                cursor.execute(sql, list(data.values()))

                # Commit the transaction
                connection.commit()

                print(f"Row inserted into table {table}.")

        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed.")

    @staticmethod
    def append_leading_zero(leading_zero_count, episode):
        episode_length = len(str(episode))
        if leading_zero_count > episode_length:
            diff = leading_zero_count - episode_length
        else:
            diff = 0
        return "0" * diff + str(episode)
