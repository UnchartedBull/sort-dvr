import cv2
import numpy as np
import logging
import time

MIN_VIDEO_DURATION = 60
MIN_NOISE_DURATION_FOR_SPLIT = 10


def check_for_split(recording, fps):
    start_time = time.time()
    frame_number = fps
    consecutive_noise_frames = 0
    consecutive_color_frames = 0
    split_added = False
    splits = []

    while frame_number < int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 1:
        recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, frame = recording.read()
        if is_noise_frame(frame):
            consecutive_color_frames = 0
            consecutive_noise_frames += 1
            if consecutive_noise_frames > MIN_NOISE_DURATION_FOR_SPLIT and not split_added:
                frame_to_split = frame_number - (
                    fps * int(MIN_NOISE_DURATION_FOR_SPLIT / 2))
                logging.debug("Found video split around frame %s",
                              int(frame_to_split))

                splits.append(frame_to_split)
                split_added = True
        else:
            consecutive_color_frames += 1
            if consecutive_color_frames > 2 and consecutive_noise_frames > MIN_NOISE_DURATION_FOR_SPLIT:
                logging.debug("End of split detected around %s",
                              str(int(frame_number - 2 * fps)))
                split_added = False
                consecutive_noise_frames = 0
                consecutive_color_frames = 0
        frame_number += fps

    logging.debug(
        "Found %s split(s) in %ss",
        str(len(splits)),
        str(round(time.time() - start_time, 2)),
    )

    return splits


def get_start_frame(recording):
    start_time = time.time()
    frame_number = 0
    consecutive_color_frames = 0

    while frame_number < int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 1:
        recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, frame = recording.read()
        if not is_noise_frame(frame):
            consecutive_color_frames += 1
            if consecutive_color_frames > 3:
                break
            frame_number += 1
        else:
            consecutive_color_frames = 0
            frame_number += 3

    frame_number = frame_number - 2
    if frame_number > int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 60:
        raise Exception("unable to find start frame")

    logging.debug(
        "Found start frame (%s) in %ss",
        str(frame_number),
        str(round(time.time() - start_time, 2)),
    )
    return frame_number


def get_end_frame(recording):
    start_time = time.time()
    frame_number = int(recording.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    consecutive_color_frames = 0

    while frame_number > 0:
        recording.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, frame = recording.read()
        if not is_noise_frame(frame):
            consecutive_color_frames += 1
            if consecutive_color_frames > 3:
                break
            frame_number -= 1
        else:
            consecutive_color_frames = 0
            frame_number -= 3

    frame_number = frame_number - 2
    if frame_number < 60:
        raise Exception("unable to find end frame")

    logging.debug(
        "Found end frame (%s) in %ss",
        str(frame_number),
        str(round(time.time() - start_time, 2)),
    )
    return frame_number


def get_dimension(recording, new_height=720):
    original_width = recording.get(cv2.CAP_PROP_FRAME_WIDTH)
    original_height = recording.get(cv2.CAP_PROP_FRAME_HEIGHT)

    return (
        f'{int(original_width)}x{int(original_height)}',
        f'{int((original_width / original_height) * new_height)}x{int(new_height)}'
    )


def calculate_duration(frames, fps):
    return int(frames / fps)


def is_noise_frame(image, p=0.05, threshold=0.5):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    s = cv2.calcHist([image], [1], None, [256], [0, 256])
    # p = 0.15
    saturation_percentage = np.sum(s[int(p * 255):-1]) / np.prod(
        image.shape[0:2])

    return saturation_percentage < threshold


def analyse_video(recording):
    fps = recording.get(cv2.CAP_PROP_FPS)
    duration = int(recording.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
    logging.debug("FPS: %s, Duration: %ss", fps, duration)

    if duration < MIN_VIDEO_DURATION:
        raise Exception("video is too short")
    return (fps, duration)
