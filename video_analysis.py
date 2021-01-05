import cv2
import numpy as np
import logging
import time

# TODO
# split videos if uncolorful frames are in between for at least 10s

MIN_VIDEO_DURATION = 60

def get_start_frame(recording):
  start_time = time.time()
  frame_number = 0
  recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  while frame_number < int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 1:
    _, frame = recording.read()
    if image_colorfulness(frame) > 15:
      break
    frame_number += 5

  if frame_number > int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 60:
    raise Exception('unable to find start frame')

  logging.debug('Found start frame (%s) in %ss', str(frame_number), str(round(time.time() - start_time, 2)))
  return frame_number;

def get_end_frame(recording):
  start_time = time.time()
  frame_number = int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 1;
  recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  while frame_number > 0:
    _, frame = recording.read()
    if image_colorfulness(frame) > 15:
      break
    frame_number -= 5
    recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  if frame_number < 60:
    raise Exception('unable to find end frame')

  logging.debug('Found end frame (%s) in %ss', str(frame_number), str(round(time.time() - start_time, 2)))
  return frame_number;

def calculate_duration(frames, fps):
  return int(frames / fps)

def image_colorfulness(image):
	(B, G, R) = cv2.split(image.astype("float"))
	rg = np.absolute(R - G)
	yb = np.absolute(0.5 * (R + G) - B)
	(rbMean, rbStd) = (np.mean(rg), np.std(rg))
	(ybMean, ybStd) = (np.mean(yb), np.std(yb))
	stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
	meanRoot = np.sqrt((rbMean ** 2) + (ybMean ** 2))
	return stdRoot + (0.3 * meanRoot)

def analyse_video(recording):
  fps = recording.get(cv2.CAP_PROP_FPS)
  duration = int(recording.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
  logging.debug("FPS: %s, Duration: %ss", fps, duration)

  if duration < MIN_VIDEO_DURATION:
    raise Exception('video is too short')
  return (fps, duration)