from ffmpeg import FFmpeg
import asyncio
import logging
import os
import time

from progressbar import TqdmToLogger, TqdmUpTo
from storage import get_next_filename


def calculate_timestamp_fps(frame, fps):
  return round(frame / fps, 2)


def render_video(recording, output, dry, quality, audio_bitrate):
  start = time.time()
  logging.debug("Rendering video from frame %s to %s", str(recording.start_frame), str(recording.end_frame))

  if dry:
    recording.sorted_location = "** DRY RUN **"
    return

  recording.sorted_location = get_next_filename(os.path.join(output, recording.matched_model))

  ffmpeg = FFmpeg().input(recording.original_location).output(
      recording.sorted_location, {
          'codec:v': 'libx265',
          'codec:a': 'eac3',
          'tag:v': 'hvc1',
          'preset': 'medium',
          'crf': quality,
          'b:a': audio_bitrate,
          'vf': f'scale={recording.dimension}:flags=lanczos',
          'ss': calculate_timestamp_fps(recording.start_frame, recording.fps),
          'to': calculate_timestamp_fps(recording.end_frame, recording.fps)
      }
  )

  @ffmpeg.on('progress')
  def on_progress(progress):
    progressbar.update_to(progress.frame)

    if recording.average_bitrate == 0:
      recording.average_bitrate = progress.bitrate
    else:
      recording.average_bitrate = round((recording.average_bitrate + progress.bitrate) / 2)

  @ffmpeg.on('terminated')
  def on_terminated():
    raise Exception('ffmpeg was externally terminated')

  @ffmpeg.on('error')
  def on_error(code):
    raise Exception('ffmpeg exited with ' + code)

  loop = asyncio.get_event_loop()

  tqdm_out = TqdmToLogger(logging.getLogger(), level=logging.INFO)
  progressbar = TqdmUpTo(
      total=recording.end_frame - recording.start_frame + 1,
      desc="Rendering video",
      unit="frame",
      file=tqdm_out,
      bar_format='{l_bar}{bar:50}{r_bar}{bar:-50b}',
      ascii=False
  )

  loop.run_until_complete(ffmpeg.execute())
  progressbar.close()

  logging.debug("Finished rendering in in %ss", str(round(time.time() - start, 2)))
