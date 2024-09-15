import os
import ffmpeg
import sys
import shutil
import time
from core.utils import Utils


class Video:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, media_path, font_path, fonts_dir, base_path="assets/media", show_log=False):
        self.utils = Utils()
        self.base_path = base_path
        self.media_path = self.utils.check_extension(f"{self.base_path}/{media_path}", "mkv")
        self.media_output_path = self.utils.append_random_name(self.media_path)
        self.show_ffmpeg_log = not show_log
        self.progress_file_path = self.utils.append_random_name(f"{self.base_path}/progress.txt")

        self.utils.check_folder(base_path)
        self.utils.validate_file(self.media_path, False)
        self.utils.validate_file(self.progress_file_path, True)

        self.font_path = font_path
        self.utils.validate_file(self.font_path)
        self.fonts_dir = fonts_dir
        self.utils.validate_file(self.fonts_dir)

        self.filter = False
        self.move_path = None
        self._trim = None
        self._frame = None
        self.output_options = {"acodec": "copy", "vcodec": "copy"}
        self.video_stream, self.audio_stream, self.subtitle_streams, self.media_duration, self.video_info = self.utils.media_streams(
            self.media_path)

    def media_info(self):
        return [self.video_stream, self.audio_stream, self.subtitle_streams, self.media_duration, self.video_info]

    def remove_subtitles(self):
        """Removes all embedded subtitles from media"""
        self.subtitle_streams = []
        return self

    def embed_subtitle(self, subtitle, title):
        """Embeds subtitle to media (CC)"""
        subtitle = self.utils.check_extension(subtitle, "ass")
        subtitle_path = f"{self.base_path}/{subtitle}"
        self.utils.validate_file(subtitle_path)
        self.subtitle_streams = [ffmpeg.input(subtitle_path)]
        self.output_options.update({
            "c:s": "ass",
            "metadata:s:s:0": f"title={title}",
            "disposition:s:s:0": "default"
        })

        return self

    def attach_font(self):
        pass

    def extract_audio(self, audio_type="mp3"):
        output = self.utils.append_random_name(self.media_path, "audio")
        if audio_type == "mp3":
            output = self.utils.remove_file_extension(output, audio_type)
            ffmpeg_inst = ffmpeg.input(self.media_path).output(f"{self.base_path}/{output}", progress=self.progress_file_path, acodec='libmp3lame')
        elif audio_type == "aac":
            output = self.utils.remove_file_extension(output, audio_type)
            ffmpeg_inst = ffmpeg.input(self.media_path).output(f"{self.base_path}/{output}", progress=self.progress_file_path, acodec='aac')
        else:  # "wav"
            output = self.utils.remove_file_extension(output, audio_type)
            ffmpeg_inst = ffmpeg.input(self.media_path).output(f"{self.base_path}/{output}", progress=self.progress_file_path, acodec='pcm_s16le')

        ffmpeg.run_async(ffmpeg_inst, overwrite_output=True, quiet=self.show_ffmpeg_log)
        self.utils.generate_progress_bar(self.media_duration, output, self.progress_file_path)

    def embed_audio(self, audio):
        """Embeds Audio to media"""
        audio = self.utils.check_extension(audio, "mp3")
        audio_path = f"{self.base_path}/{audio}"
        self.utils.validate_file(audio_path)
        self.audio_stream = ffmpeg.input(audio_path)

        return self

    def hardcode_subtitle(self, subtitle):
        """Burn subtitle onto media"""
        self.filter = True
        subtitle = self.utils.check_extension(subtitle, "ass")
        subtitle_path = f"{self.base_path}/{subtitle}"
        self.utils.validate_file(subtitle_path)
        self.video_stream = self.video_stream.filter("subtitles", subtitle_path, fontsdir=self.fonts_dir)

        return self

    def watermark(self, **kwargs):
        """
        Add a watermark (text or image) to the video.

        Parameters:
        -----------
        watermark : str
            The watermark content. For text, this is the watermark text.
            For image, this is the path to the image file.

        watermark_type : str, optional, default='text'
            Type of the watermark. Options are 'text' for text watermark or 'image' for image watermark.

        position : str, optional, default='bottom_left'
            Position of the watermark on the video. Options are:
            - 'bottom_left'
            - 'bottom_right'
            - 'top_left'
            - 'top_right'

        padding : int, optional, default=5
            Distance from the margins to place the watermark.

        timing : str, optional
            Time range to apply the watermark. Format can be:
            - "start_time,end_time" to apply from start_time to end_time in seconds.
            - "duration" to apply for the first duration seconds.

        font_size : int, optional, default=12
            Font size for text watermark.

        font_color : str, optional, default='yellow'
            Font color for text watermark. Can be color name or RGB value.

        font_path : str, optional
            Path to the font file for text watermark.

        stroke_color : str, optional, default='black'
            Border color for the text.

        stroke_width : float, optional, default=1
            Border width for the text.

        width : int, optional, default=100
            Width of the image watermark.

        height : int, optional, default=100
            Height of the image watermark.

        Returns:
        --------
        self : VideoEditor
            The VideoEditor instance with the watermark applied.
        """
        self.filter = True
        video_width = None
        video_height = None
        for stream in self.video_info['streams']:
            if stream['codec_type'] == 'video':
                video_width = stream.get('width', None)
                video_height = stream.get('height', None)
                break
        if video_width is None or video_height is None:
            raise ValueError("video width or height not found")
        watermark = kwargs.get("watermark") or "watermark"
        watermark_type = kwargs.get("watermark_type") or "text"
        position = kwargs.get("position") or "bottom_left"
        padding = kwargs.get("padding") or 5

        if watermark_type == 'text':
            font_size = kwargs.get("font_size") or 12
            # RGB '#FF0000' # Color name 'yellow' # RGB value 'rgb(255,0,0)'
            font_color = kwargs.get("font_color") or "yellow"
            font_path = kwargs.get("font_path")
            timing = kwargs.get("timing")
            stroke_color = kwargs.get("stroke_color") or "black"
            stroke_width = kwargs.get("stroke_width") or 1

            watermark_x, watermark_y = self.utils.calc_text_position(
                position, video_width, video_height, watermark, font_size, padding)
            filter_kwargs = {
                "text": watermark,
                "fontsize": font_size,
                "fontcolor": font_color,
                "x": watermark_x,
                "y": watermark_y
            }
            if stroke_color:
                filter_kwargs["bordercolor"] = stroke_color
            if stroke_width:
                filter_kwargs["borderw"] = stroke_width
            if font_path:
                filter_kwargs["fontfile"] = os.path.join(self.base_path, font_path)
            else:
                filter_kwargs["fontfile"] = self.font_path
            if timing:
                timing = str(timing).split(",")
                if len(timing) == 1:
                    enable = f"lte(t,{timing[0]})"
                else:
                    enable = f"between(t,{timing[0]},{timing[1]})"
                filter_kwargs["enable"] = enable

            self.video_stream = self.video_stream.filter('drawtext', **filter_kwargs)
        else:  # image
            image_width = kwargs.get("width") or 100
            image_height = kwargs.get("height") or 100
            x, y = self.utils.calc_image_position(position, video_width, image_width, video_height,
                                                  image_height, padding)
            watermark_stream = ffmpeg.input(watermark)
            scaled_watermark = watermark_stream.filter('scale', w=image_width, h=image_height)

            self.video_stream = self.video_stream.overlay(scaled_watermark, x=x, y=y)

        return self

    def encode(self, **kwargs):
        """Encodes video

        :codec: str: options is: av1, h265
        :color_depth: str: options is: 10bit, 8bit
        :resolution: str: options is: 720, 480
        :preset: str: the faster preset the less quality and larger file size. options is: faster, fast, medium, slow, slower, veryslow
        :crf: int: the lowest crf the highest quality and larger file size. options is a range of 0-51
        :frame_rate: int: video fps. if not provided it will use videos default fps
        """
        if len(kwargs) == 0:
            sys.exit("specify at least one keyword argument for encoding")

        processor = kwargs.get("processor") or "cpu"
        if "codec" in kwargs:
            codec = kwargs.get("codec")
            if codec == "h265":
                if processor == "cpu":
                    self.output_options["vcodec"] = "libx265"
                else:
                    self.output_options["vcodec"] = "hevc_nvenc"
            elif codec == "av1":
                if processor == "cpu":
                    self.output_options["vcodec"] = "libaom-av1"
                else:
                    self.output_options["vcodec"] = "libsvtav1"
        if "color_depth" in kwargs:
            color_depth = kwargs.get("color_depth")
            if color_depth == "10bit":
                if processor == "cpu":
                    self.output_options["pix_fmt"] = "yuv420p10le"
                else:
                    self.output_options["pix_fmt"] = "p010le"
            elif color_depth == "8bit":
                self.output_options["pix_fmt"] = "yuv420p"
        if "resolution" in kwargs:
            resolution = kwargs.get("resolution")
            if resolution == "720":
                self.video_stream = self.video_stream.filter('scale', 1280, 720)
            elif resolution == "480":
                self.video_stream = self.video_stream.filter('scale', 854, 480)
        if "preset" in kwargs:
            self.output_options["preset"] = kwargs.get("preset")
        if "crf" in kwargs:
            self.output_options["crf"] = kwargs.get("frame_rate")
        if "frame_rate" in kwargs:
            self.output_options["r"] = kwargs.get("frame_rate")

        return self

    def chapter(self):
        pass
        # ;FFMETADATA1
        # [CHAPTER]
        # TIMEBASE = 1 / 1000
        # START = 0
        # END = 30000
        # title = Chapter
        # 1
        # [CHAPTER]
        # TIMEBASE = 1 / 1000
        # START = 30000
        # END = 60000
        # title = Chapter
        # 2

    def trim(self, start, end):
        self.filter = True
        self._trim = {"start": start, "end": end}
        return self

    def frame(self, second: int = None):
        self.filter = True
        if not second:
            second = self.media_duration / 2
        self._frame = {"start": second, "end": second + 1}
        return self

    def change_title(self, title):
        """Changes media name and title"""
        title = self.utils.check_extension(title, "mkv")
        self.media_output_path = f"{self.base_path}/{title}"
        self.output_options["metadata"] = f"title={title}"
        return self

    def move_file(self, path):
        self.move_path = self.base_path
        path_list = path.split('/')
        for i, path in enumerate(path_list):
            self.move_path = os.path.join(self.move_path, path)
        if not os.path.exists(self.move_path):
            os.makedirs(self.move_path)
        return self

    def execute(self, progress_bar=True, async_run=True):
        if self.filter:
            if "acodec" in self.output_options:
                self.output_options.pop("acodec", None)
            if "vcodec" in self.output_options and self.output_options["vcodec"] == "copy":
                self.output_options.pop("vcodec", None)

        # # add threads based on cpu cores to boost processing speed
        self.output_options["threads"] = 4

        try:
            if progress_bar:
                self.output_options["progress"] = self.progress_file_path

            if self._trim:
                self.video_stream = self.video_stream.trim(start=self._trim['start'], end=self._trim['end']).setpts('PTS-STARTPTS')
                self.audio_stream = self.audio_stream.filter_('atrim', start=self._trim['start'], end=self._trim['end']).filter_('asetpts', 'PTS-STARTPTS')
            elif self._frame:
                self.media_output_path = self.utils.check_extension(self.utils.remove_file_extension(self.media_output_path), "png")
                self.output_options["vframes"] = 1
                self.output_options["format"] = "image2"
                self.output_options["update"] = True
                self.video_stream = self.video_stream.trim(start=self._frame['start'], end=self._frame['end']).setpts('PTS-STARTPTS')

            output_streams = [self.video_stream, self.audio_stream]
            if self.subtitle_streams and len(self.subtitle_streams) > 0:
                output_streams.extend(self.subtitle_streams)

            self.media_output_path = self.media_output_path.replace(":", " ")

            command = (
                ffmpeg
                .output(*output_streams, self.media_output_path, **self.output_options)
            )

            if async_run:
                command.run_async(overwrite_output=True, quiet=self.show_ffmpeg_log)
            else:
                command.run(overwrite_output=True, quiet=self.show_ffmpeg_log)

            if progress_bar:
                self.utils.generate_progress_bar(self.media_duration, self.media_output_path, self.progress_file_path)

            if self.move_path:
                if async_run:
                    time.sleep(5)
                shutil.move(os.path.abspath(self.media_output_path), os.path.abspath(self.move_path))
        except Exception as e:
            self.utils.validate_file(self.media_output_path, True)
            self.utils.validate_file(self.progress_file_path, True)
            raise ValueError(e)
