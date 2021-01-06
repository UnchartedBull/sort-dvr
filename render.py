import logging
import time
import asyncio
from ffmpeg import FFmpeg
from tqdm import tqdm

average_bitrate = 0
progressbar = None


class TQDMUpTo(tqdm):
    def update_to(self, frames=1):
        return self.update(frames - self.n)


def calculate_timestamp_fps(frame, fps):
    return round(frame / fps, 2)


def render_video(
    input_path,
    output_path,
    start_time,
    end_time,
    frames_to_render,
    new_resolution,
    quality=30,
    audio_bitrate="32k",
):
    global average_bitrate
    global progressbar

    average_bitrate = 0
    progressbar = TQDMUpTo(total=frames_to_render,
                           desc="Rendering video",
                           unit="frame")

    start = time.time()

    ffmpeg = FFmpeg().input(input_path).output(
        output_path, {
            'codec:v': 'libx265',
            'codec:a': 'eac3',
            'tag:v': 'hvc1',
            'preset': 'medium',
            'crf': quality,
            'b:a': audio_bitrate,
            'vf': f'scale={new_resolution}:flags=lanczos',
            'ss': start_time,
            't': end_time
        })

    @ffmpeg.on('progress')
    def on_progress(progress):
        global average_bitrate
        global progressbar

        progressbar.update_to(progress.frame)
        if average_bitrate == 0:
            average_bitrate = progress.bitrate
        else:
            average_bitrate = round((average_bitrate + progress.bitrate) / 2)

    @ffmpeg.on('terminated')
    def on_terminated():
        raise Exception('ffmpeg was externally terminated')

    @ffmpeg.on('error')
    def on_error(code):
        raise Exception('ffmpeg exited with ' + code)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ffmpeg.execute())
    # loop.close()
    progressbar.close()

    logging.debug("Finished rendering in in %ss",
                  str(round(time.time() - start, 2)))

    return average_bitrate
