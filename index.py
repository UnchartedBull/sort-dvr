import logging
import traceback
import os
import sys
import argparse
import numpy as np

from read_modelname import get_modelname, write_mask
from video_analysis import analyse_video, get_start_frame, get_end_frame, calculate_duration
from recording import Recording
from storage import check_exists, check_folder, check_is_video

# TODO
# Correct filename
# Render files
# Save unsure files
# Read whole folder
# Final stats
# Database

# short_options = "hdi:v:o:"
# long_options = ["help", "debug", "input=", "video=", "output="]

def analyse_recording(filename):
  recording = Recording(filename)

  try:
    logging.debug("Analysing Video ...")
    (recording.fps, recording.original_duration) = analyse_video(recording.video)
    recording.start_frame = get_start_frame(recording.video)
    recording.end_frame = get_end_frame(recording.video)
    recording.duration = calculate_duration(recording.end_frame - recording.start_frame, recording.fps)

    logging.debug("Reading Modelname ...")
    (recording.ocr_text, recording.ocr_confidence, recording.matched_model, recording.match_similarity, masked_image) = get_modelname(recording.video, recording.start_frame, recording.end_frame)
    recording.confidence = round(np.mean([recording.ocr_confidence, recording.match_similarity]), 2)
    recording.masked_image_path = os.path.join('.', 'name-masks', str(recording.uuid) + '.png')
    write_mask(recording.masked_image_path, masked_image)

    recording.sorted_location = os.path.join('.', 'sorted-tmp', recording.matched_model, '#001.mp4')
  except Exception as e:
    recording.error = e
    traceback.print_exc()

  logging.info("Processing finished: %s (%s%% confidence, %ss) - %s", recording.matched_model, str(recording.confidence), str(recording.processing_time), recording.sorted_location)
  logging.debug(recording)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='easily sort your dvr recordings without any effort')
  parser.add_argument('input', type=str, help="input folder or file which should be processed")
  parser.add_argument('output', type=str, help='output folder to which the sorted recordings should be saved')
  parser.add_argument('-d', '--debug', help="turn on debug log statements", action="store_true")

  args = parser.parse_args()

  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG if args.debug else logging.INFO)

  if not check_exists(args.input):
    logging.error("File / Folder does not exist")
    sys.exit(-1)

  if check_folder(args.input):
    print("tbd.")
  else:
    analyse_recording(args.input)