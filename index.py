import uuid
import cv2
import pandas as pd

from read_modelname import get_modelname

def read_image(filename):
  return cv2.imread(filename)

if __name__ == "__main__":
  dvr_dataframe = pd.DataFrame(index = [uuid.uuid1()], columns=['original_location', 'sorted_location', 'start_frame', 'end_frame', 'fps', 'duration', 'ocr_text', 'ocr_confidence', 'matched_text', 'fuzzy_score', 'successful'])
  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/image-3.png';

  image = read_image(dvr_dataframe.iloc[0]['original_location'])
  print(get_modelname(image, dvr_dataframe))