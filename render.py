import subprocess
import logging
import time
import asyncio
from ffmpeg import FFmpeg

average_bitrate = 0


def calculate_timestamp_fps(frame, fps):
    return round(frame / fps, 2)


def render_video(
    input_path,
    output_path,
    start_time,
    end_time,
    frames_to_render,
    quality=30,
    audio_bitrate="32k",
):
    global average_bitrate
    average_bitrate = 0

    start = time.time()

    ffmpeg = FFmpeg().option('y').input(input_path).output(
        output_path, {
            'codec:v': 'libx265',
            'codec:a': 'eac3',
            'tag:v': 'hvc1',
            'preset': 'medium',
            'crf': quality,
            'b:a': audio_bitrate,
            'vf': 'scale=860x720:flags=lanczos',
            'ss': start_time,
            't': end_time
        })

    @ffmpeg.on('progress')
    def on_progress(progress):
        global average_bitrate

        print(progress)
        if average_bitrate == 0:
            average_bitrate = progress.bitrate
        else:
            average_bitrate = round((average_bitrate + progress.bitrate) / 2)

    @ffmpeg.on('completed')
    def on_completed():
        print('Completed')

    @ffmpeg.on('terminated')
    def on_terminated():
        raise Exception('ffmpeg was externally terminated')

    @ffmpeg.on('error')
    def on_error(code):
        raise Exception('ffmpeg exited with ' + code)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ffmpeg.execute())
    loop.close()

    logging.debug("Finished rendering in in %ss",
                  str(round(time.time() - start, 2)))

    return average_bitrate


def log_replace(text):
    print("\x1b[1A\x1b[0J", end="\r")
    logging.debug(text)
