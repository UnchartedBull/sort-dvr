import cv2
import numpy as np
import pandas as pd
import pytesseract
import logging
import os
import time

MASK_FOLDER = os.path.join('.', 'name-masks')

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

def ocr(image, dvr_dataframe):
  start_time = time.time()
  custom_oem_psm_config = r'--oem 1 --psm 4'
  detected_text = pytesseract.image_to_data(image, output_type='data.frame', config=custom_oem_psm_config)
  detected_text = detected_text[detected_text.conf != -1]
  dvr_dataframe.at[dvr_dataframe.index[0], 'ocr_text'] = detected_text.groupby('page_num')['text'].agg(' '.join)[1]
  dvr_dataframe.at[dvr_dataframe.index[0], 'ocr_confidence'] = detected_text.groupby('page_num')['conf'].mean()[1]
  logging.debug('OCR detected %s (%s%% confidence) in %ss', dvr_dataframe['ocr_text'][0], dvr_dataframe['ocr_confidence'][0], str(round(time.time() - start_time, 2)))


  return dvr_dataframe

def get_modelname(image, dvr_dataframe):
  logging.debug("Getting model name for video %s", dvr_dataframe.index[0])
  dilated = dilate(image);
  eroded = erode(dilated);
  masked = apply_mask(eroded);
  image_path = os.path.join(MASK_FOLDER, str(dvr_dataframe.index[0]) + '.png')
  cv2.imwrite(image_path, masked)
  logging.debug("Generated model name image mask at %s", image_path)
  return ocr(masked, dvr_dataframe);

if __name__ == "__main__":
  dvr_dataframe = pd.DataFrame(index = ['mock'], columns=['original_location', 'ocr_text', 'ocr_confidence'])
  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/image-3.png';

  image = read_image(dvr_dataframe.iloc[0]['original_location'])
  print(get_modelname(image, dvr_dataframe))