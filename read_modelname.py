import cv2
import logging
import numpy as np
import os
import pytesseract
import re

from fuzzy_match import match_modelname, load_modelnames


def dilate(image):
  kernel = np.ones((4, 4), np.uint8)

  return cv2.dilate(image, kernel, iterations=1)


def erode(image):
  kernel = np.ones((3, 3), np.uint8)

  return cv2.erode(image, kernel, iterations=1)


def apply_mask(image):
  lower_bound = np.array([0, 0, 0], dtype="uint16")
  upper_bound = np.array([215, 215, 215], dtype="uint16")

  return cv2.inRange(image, lower_bound, upper_bound)


def resize_image(image):
  return cv2.getRectSubPix(image, (375, 80), (344, 60))


def ocr(image):
  custom_oem_psm_config = r"--oem 1 --psm 4"
  detected_text = pytesseract.image_to_data(image, output_type="data.frame", config=custom_oem_psm_config)
  detected_text = detected_text[detected_text.conf != -1]
  text = None
  confidence = None

  try:
    text = detected_text.groupby("page_num")["text"].agg(" ".join)[1]
    confidence = round(detected_text.groupby("page_num")["conf"].mean()[1], 2)
  except:
    text = ""
    confidence = 0

  return (text, confidence, image)


def extract_name_from_still(image):
  dilated = dilate(image)
  eroded = erode(dilated)
  masked = apply_mask(eroded)

  return ocr(masked)


def get_model_from_filename(filename):
  result = re.search("\[(.*)\]", filename)

  if not result:
    return None
  else:
    return result.group(1)


def write_mask(filename, mask_image):
  cv2.imwrite(filename, mask_image)
  logging.debug("Saved model name image mask at %s", filename)


def is_unsure(match_similarity, ocr_confidence):
  return match_similarity < 80 or ocr_confidence < 65 or (90 <= match_similarity <= 99 and ocr_confidence < 70
                                                         ) or (match_similarity < 90 and ocr_confidence < 75)


def read_modelname(video, start_frame, end_frame, search_distance):
  frame_to_search = start_frame

  ocr_text = None
  ocr_confidence = 0
  masked_image = None
  matched_model = None
  match_similarity = 0

  load_modelnames()

  while frame_to_search + search_distance - 1 < end_frame:
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_to_search)
    _, frame = video.read()
    frame = resize_image(frame)

    (text, confidence, image) = extract_name_from_still(frame)
    (match, similarity) = match_modelname(text)

    if similarity > match_similarity and confidence > ocr_confidence - 10:
      logging.debug(
          "Better match: %s (%s%% confidence, %s%% similarity)",
          match,
          str(confidence),
          str(similarity),
      )
      ocr_text = text
      ocr_confidence = confidence
      masked_image = image
      matched_model = match
      match_similarity = similarity

    frame_to_search += search_distance

  return (ocr_text, ocr_confidence, matched_model, match_similarity, masked_image)


def extract_modelname(recording, model):
  if get_model_from_filename(recording.original_location) and not model:
    logging.debug("Using Modelname from file")

    recording.confidence = 100
    recording.match_similarity = 100
    recording.ocr_confidence = 0
    recording.ocr_text = "FILENAME"

    recording.matched_model = get_model_from_filename(recording.original_location)
  elif model:
    logging.debug("Using Modelname from args")

    recording.confidence = 100
    recording.match_similarity = 100
    recording.ocr_confidence = 0
    recording.ocr_text = "PARAMETER"
    recording.matched_model = model
  else:
    logging.debug("Reading Modelname ...")
    masked_image = None
    search_distance = recording.fps * 10

    while is_unsure(recording.match_similarity, recording.ocr_confidence) and search_distance > recording.fps:
      logging.debug("Searching with search distance %s frames", str(int(search_distance)))

      (
          recording.ocr_text,
          recording.ocr_confidence,
          recording.matched_model,
          recording.match_similarity,
          masked_image,
      ) = read_modelname(recording.video, recording.start_frame, recording.end_frame, search_distance)
      recording.confidence = round(np.mean([recording.ocr_confidence, recording.match_similarity]), 2)

    recording.masked_image_path = os.path.join(".", "name-masks", str(recording.uuid) + ".png")
    write_mask(recording.masked_image_path, masked_image)

    if is_unsure(recording.match_similarity, recording.ocr_confidence):
      raise Exception("unsure result")
