import subprocess
import logging
import time
import shlex


def calculate_timestamp_fps(frame, fps):
    return round(frame / fps, 2)


def render_video(
    input_path,
    output_path,
    start_time,
    end_time,
    quality=30,
    audio_bitrate="32k",
):
    start = time.time()
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            input_path,
            "-c:v",
            "libx265",
            "-preset",
            "medium",
            "-crf",
            str(quality),
            "-tag:v",
            "hvc1",
            "-c:a",
            "eac3",
            "-b:a",
            audio_bitrate,
            "-vf",
            "scale=860x720:flags=lanczos",
            "-ss",
            str(start_time),
            "-t",
            str(end_time),
            output_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    while True:
        stdout = process.stdout.readline()

        log_replace(stdout.decode("utf-8").strip())

        return_code = process.poll()
        if return_code is not None:
            if return_code != 0:
                logging.error("FFMPEG exited with error code " +
                              str(return_code))
                logging.debug(process.stderr.readlines())
                raise Exception("rendering failed")
            break

    logging.debug("Rendering finished in %ss",
                  str(round(time.time() - start, 2)))


def log_replace(text):
    print("\x1b[1A\x1b[0J", end="\r")
    logging.debug(text)
