import cv2
import numpy as np
import pandas as pd
import pytesseract
import logging
import os
import time

from match_modelname import match_modelname

MASK_FOLDER = os.path.join('.', 'name-masks')
SEARCH_DISTANCE = 120

def read_image(filename):
  return cv2.imread(filename)

def dilate(image):
  kernel = np.ones((4,4),np.uint8)
  return cv2.dilate(image, kernel, iterations = 1)

def erode(image):
  kernel = np.ones((3,3),np.uint8)
  return cv2.erode(image, kernel, iterations = 1)

def apply_mask(image):
  lower_bound = np.array([0,0,0], dtype = "uint16")
  upper_bound = np.array([215,215,215], dtype = "uint16")
  return cv2.inRange(image, lower_bound, upper_bound)

def ocr(image):
  start_time = time.time()
  custom_oem_psm_config = r'--oem 1 --psm 4'
  detected_text = pytesseract.image_to_data(image, output_type='data.frame', config=custom_oem_psm_config)
  detected_text = detected_text[detected_text.conf != -1]
  text = None
  confidence = None

  try:
    text = detected_text.groupby('page_num')['text'].agg(' '.join)[1]
    confidence = round(detected_text.groupby('page_num')['conf'].mean()[1], 2)
  except:
    text = ""
    confidence = 0

  logging.debug('OCR detected %s (%s%% confidence) in %ss', text, str(confidence), str(round(time.time() - start_time, 2)))

  return (text, confidence, image)

def extract_name_from_still(image):
  dilated = dilate(image);
  eroded = erode(dilated);
  masked = apply_mask(eroded);
  return ocr(masked);

def resize_image(image):
  return cv2.getRectSubPix(image, (375, 80), (344, 60))

def get_modelname(dvr_dataframe, dvr):
  logging.debug("Getting model name for video %s", dvr_dataframe.index[0])
  frame_to_search = dvr_dataframe['start_frame'][0]

  ocr_text = None
  ocr_confidence = 0
  masked_image = None
  matched_model = None
  match_similarity = 0

  while frame_to_search + SEARCH_DISTANCE - 1 < dvr_dataframe['end_frame'][0]:
    dvr.set(cv2.CAP_PROP_POS_FRAMES, frame_to_search)
    _, frame = dvr.read()
    frame = resize_image(frame)

    (text, confidence, image) = extract_name_from_still(frame)
    (match, similarity) = match_modelname(text)

    if similarity > match_similarity and confidence > ocr_confidence - 10:
      logging.debug('Higher similarity for %s (%s%% confidence, %s%% similarity)', match, str(confidence), str(similarity))
      ocr_text = text
      ocr_confidence = confidence
      masked_image = image
      matched_model = match
      match_similarity = similarity

    frame_to_search += SEARCH_DISTANCE

  image_path = os.path.join(MASK_FOLDER, str(dvr_dataframe.index[0]) + '.png')
  cv2.imwrite(image_path, masked_image)
  logging.debug("Saved model name image mask at %s", image_path)
  logging.info('Matched model: %s (%s%% confidence, %s%% similarity)', matched_model, str(ocr_confidence), str(match_similarity))


  dvr_dataframe.at[dvr_dataframe.index[0], 'ocr_text'] = ocr_text
  dvr_dataframe.at[dvr_dataframe.index[0], 'ocr_confidence'] = ocr_confidence
  dvr_dataframe.at[dvr_dataframe.index[0], 'masked_image'] = image_path
  dvr_dataframe.at[dvr_dataframe.index[0], 'matched_model'] = matched_model
  dvr_dataframe.at[dvr_dataframe.index[0], 'match_similarity'] = match_similarity

  return dvr_dataframe

if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

  dvr_dataframe = pd.DataFrame(index = ['mock'], columns=['original_location', 'ocr_text', 'ocr_confidence', 'masked_image', 'matched_model', 'match_similarity', 'start_frame', 'end_frame'])

  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/video-1.mov';
  dvr_dataframe.at[dvr_dataframe.index[0], 'start_frame'] = 10
  dvr_dataframe.at[dvr_dataframe.index[0], 'end_frame'] = 5000

  dvr = cv2.VideoCapture(dvr_dataframe.iloc[0]['original_location'])

  print(get_modelname(dvr_dataframe, dvr).iloc[0])
  dvr.release()