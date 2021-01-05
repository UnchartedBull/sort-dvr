import cv2
import pandas as pd
import numpy as np

def get_start_frame(dvr):
  frame_number = 0
  dvr.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  while True:
    _, frame = dvr.read()
    if image_colorfulness(frame) > 15:
      break
    frame_number += 1

  return frame_number;

def get_end_frame(dvr):
  frame_number = int(dvr.get(cv2.CAP_PROP_FRAME_COUNT)) - 1;
  dvr.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  while True:
    _, frame = dvr.read()
    if image_colorfulness(frame) > 15:
      break
    frame_number -= 1
    dvr.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

  return frame_number;


def image_colorfulness(image):
	(B, G, R) = cv2.split(image.astype("float"))
	rg = np.absolute(R - G)
	yb = np.absolute(0.5 * (R + G) - B)
	(rbMean, rbStd) = (np.mean(rg), np.std(rg))
	(ybMean, ybStd) = (np.mean(yb), np.std(yb))
	stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
	meanRoot = np.sqrt((rbMean ** 2) + (ybMean ** 2))
	return stdRoot + (0.3 * meanRoot)

def analyse_video(dvr_dataframe):
  dvr = cv2.VideoCapture(dvr_dataframe.iloc[0]['original_location'])
  dvr_dataframe.at[dvr_dataframe.index[0], 'fps'] = dvr.get(cv2.CAP_PROP_FPS)
  dvr_dataframe.at[dvr_dataframe.index[0], 'duration'] = int(dvr.get(cv2.CAP_PROP_FRAME_COUNT) / dvr_dataframe['fps'][0])
  dvr_dataframe.at[dvr_dataframe.index[0], 'start_frame'] = get_start_frame(dvr)
  dvr_dataframe.at[dvr_dataframe.index[0], 'end_frame'] = get_end_frame(dvr)
  print(dvr_dataframe)
  dvr.release()

if __name__ == "__main__":
  dvr_dataframe = pd.DataFrame(index = ['mock'], columns=['original_location', 'start_frame', 'end_frame', 'fps', 'duration'])
  dvr_dataframe.at[dvr_dataframe.index[0], 'original_location'] = './test/video-1.mov';

  analyse_video(dvr_dataframe)