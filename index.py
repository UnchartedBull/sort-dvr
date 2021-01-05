import uuid
import cv2
import pandas as pd
import logging
import traceback

from read_modelname import get_modelname
from video_analysis import analyse_video

def read_image(filename):
  return cv2.imread(filename)

if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

  dvr_dataframe = pd.DataFrame(index = [uuid.uuid1()], columns=['original_location', 'sorted_location', 'start_frame', 'end_frame', 'fps', 'duration', 'ocr_text', 'ocr_confidence', 'matched_text', 'fuzzy_score', 'error'])
  # dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/video-1.mov';
  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/image-1.png';

  while True:
    # try:
    #   dvr_dataframe = analyse_video(dvr_dataframe)
    # except:
    #   dvr_dataframe.at[dvr_dataframe.index[0], 'error'] = 'Can\'t determine start / end frame'
    #   logging.error('Can\'t determine start / end frame for video %s', str(dvr_dataframe.index[0]))
    #   traceback.print_exc()
    #   break

    try:
      image = read_image(dvr_dataframe.iloc[0]['original_location'])
      dvr_dataframe = get_modelname(image, dvr_dataframe)
    except:
      dvr_dataframe.at[dvr_dataframe.index[0], 'error'] = 'Can\'t determine model name'
      logging.error('Can\'t determine model name for video %s', str(dvr_dataframe.index[0]))
      traceback.print_exc()
      break

    break
  print(dvr_dataframe)