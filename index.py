import uuid
import cv2
import pandas as pd
import logging
import traceback

from read_modelname import get_modelname
from video_analysis import analyse_video

if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

  dvr_dataframe = pd.DataFrame(index = [uuid.uuid1()], columns=['original_location', 'sorted_location', 'start_frame', 'end_frame', 'fps', 'duration', 'ocr_text', 'ocr_confidence', 'masked_image', 'matched_model', 'match_similarity', 'error'])
  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/video-1.mov';
  dvr_dataframe.at[dvr_dataframe.index[0], 'start_frame'] = 10
  dvr_dataframe.at[dvr_dataframe.index[0], 'end_frame'] = 5000

  dvr = cv2.VideoCapture(dvr_dataframe.iloc[0]['original_location'])

  while True:
    try:
      dvr_dataframe = analyse_video(dvr_dataframe, dvr)
    except:
      dvr_dataframe.at[dvr_dataframe.index[0], 'error'] = 'Can\'t determine start / end frame'
      logging.error('Can\'t determine start / end frame for video %s', str(dvr_dataframe.index[0]))
      traceback.print_exc()
      break

    try:
      dvr_dataframe = get_modelname(dvr_dataframe, dvr)
    except:
      dvr_dataframe.at[dvr_dataframe.index[0], 'error'] = 'Can\'t determine model name'
      logging.error('Can\'t determine model name for video %s', str(dvr_dataframe.index[0]))
      traceback.print_exc()
      break

    break
  dvr.release();
  logging.debug('Analysis for video %s finished', str(dvr_dataframe.index[0]))
  logging.debug(dvr_dataframe.iloc[0])