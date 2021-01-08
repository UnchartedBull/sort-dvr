import cv2
import logging
import numpy as np
import time

MIN_VIDEO_DURATION = 60
MIN_NOISE_DURATION_FOR_SPLIT = 10


def check_for_splits(recording):
  start_time = time.time()
  frame_number = recording.fps
  consecutive_noise_frames = 0
  consecutive_color_frames = 0
  split_added = False
  parts = []

  while frame_number < int(recording.end_frame) - 1:
    recording.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    _, frame = recording.video.read()

    if is_noise_frame(frame):
      consecutive_color_frames = 0
      consecutive_noise_frames += 1

      if consecutive_noise_frames > MIN_NOISE_DURATION_FOR_SPLIT and not split_added:
        frame_to_split = frame_number - (recording.fps * int(MIN_NOISE_DURATION_FOR_SPLIT / 2))
        logging.debug("Found video split around frame %s", int(frame_to_split))

        parts.append([0 if not parts else parts[len(parts) - 1][1], int(frame_to_split)])
        split_added = True
    else:
      consecutive_color_frames += 1

      if consecutive_color_frames > 2 and consecutive_noise_frames > MIN_NOISE_DURATION_FOR_SPLIT:
        logging.debug("End of split detected around %s", str(int(frame_number - 2 * recording.fps)))
        split_added = False
        consecutive_noise_frames = 0
        consecutive_color_frames = 0

    frame_number += recording.fps

  if parts:
    parts.append([parts[len(parts) - 1][1], recording.end_frame])

  logging.debug(
      "Found %s split(s) in %ss",
      str(len(parts)),
      str(round(time.time() - start_time, 2)),
  )

  if parts and recording.original_duration / len(parts) < 120:
    raise Exception('more than 1 split per 2m')

  return parts


def get_next_color_frame(video, start, end, multiplier):
  consecutive_color_frames = 0
  frame_number = start

  while frame_number < end if multiplier > 0 else frame_number > end:
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    _, frame = video.read()

    if not is_noise_frame(frame):
      consecutive_color_frames += 1

      if consecutive_color_frames > 3:
        break

      frame_number = frame_number + (1 * multiplier)
    else:
      consecutive_color_frames = 0
      frame_number = frame_number + (3 * multiplier)

  return int(frame_number + (-3 * multiplier))


def get_start_frame(recording):
  start_time = time.time()

  recording.start_frame = get_next_color_frame(recording.video, recording.start_frame, recording.end_frame, 1)

  if recording.start_frame > recording.end_frame - recording.fps * MIN_VIDEO_DURATION:
    raise Exception("unable to find start frame")

  logging.debug(
      "Found start frame (%s) in %ss",
      str(recording.start_frame),
      str(round(time.time() - start_time, 2)),
  )


def get_end_frame(recording):
  start_time = time.time()

  recording.end_frame = get_next_color_frame(recording.video, recording.end_frame - 1, recording.start_frame, -1)

  if recording.end_frame < recording.fps * MIN_VIDEO_DURATION:
    raise Exception("unable to find end frame")

  logging.debug(
      "Found end frame (%s) in %ss",
      str(recording.end_frame),
      str(round(time.time() - start_time, 2)),
  )


def get_dimension(recording, new_height=720):
  original_width = recording.video.get(cv2.CAP_PROP_FRAME_WIDTH)
  original_height = recording.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

  recording.original_dimension = f'{int(original_width)}x{int(original_height)}'
  recording.dimension = f'{int((original_width / original_height) * new_height)}x{int(new_height)}'


def calculate_duration(recording):
  recording.duration = int((recording.end_frame - recording.start_frame) / recording.fps)

  if recording.duration < MIN_VIDEO_DURATION:
    raise Exception('start / end frame too close')


def is_noise_frame(image, p=0.05, threshold=0.6):
  image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
  s = cv2.calcHist([image], [1], None, [256], [0, 256])
  saturation_percentage = np.sum(s[int(p * 255):-1]) / np.prod(image.shape[0:2])

  return saturation_percentage < threshold


def analyse_video(recording):
  recording.fps = recording.video.get(cv2.CAP_PROP_FPS)

  if recording.end_frame == 0:
    recording.end_frame = int(recording.video.get(cv2.CAP_PROP_FRAME_COUNT))

  recording.original_duration = int((recording.end_frame - recording.start_frame) / recording.fps)

  if recording.original_duration < MIN_VIDEO_DURATION:
    raise Exception("video is too short")