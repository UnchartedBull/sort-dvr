import logging
import traceback
import os
import sys
import argparse
import numpy as np

from read_modelname import get_modelname, write_mask, get_model_from_filename
from video_analysis import analyse_video, get_start_frame, get_end_frame, calculate_duration
from recording import Recording
from storage import exists, is_folder, get_next_filename, get_files, move_error_file

# TODO
# Render files
# Database

failed_videos = []

def analyse_recording(filename, output, unsure):
  global failed_videos

  recording = Recording(filename)
  try:
    recording.open_video()

    logging.debug("Analysing Video ...")
    (recording.fps, recording.original_duration) = analyse_video(recording.video)
    recording.start_frame = get_start_frame(recording.video)
    recording.end_frame = get_end_frame(recording.video)
    recording.duration = calculate_duration(recording.end_frame - recording.start_frame, recording.fps)

    if get_model_from_filename(recording.original_location):
      logging.debug("Using Modelname from file ...")
      recording.confidence = 100
      recording.match_similarity = 100
      recording.ocr_text = "FILENAME"
      recording.matched_model = get_model_from_filename(filename)
    else:
      logging.debug("Reading Modelname ...")
      (recording.ocr_text, recording.ocr_confidence, recording.matched_model, recording.match_similarity, masked_image) = get_modelname(recording.video, recording.start_frame, recording.end_frame)
      recording.confidence = round(np.mean([recording.ocr_confidence, recording.match_similarity]), 2)
      recording.masked_image_path = os.path.join('.', 'name-masks', str(recording.uuid) + '.png')
      write_mask(recording.masked_image_path, masked_image)

    recording.sorted_location = get_next_filename(os.path.join(output, recording.matched_model))
  except Exception as e:
    recording.error = e
    logging.debug(e, exc_info=True)

  if recording.has_errors():
    failed_videos.append(recording)
    move_error_file(recording.original_location, unsure)
    logging.warning('Could not process video: %s', recording.error)
  else:
    logging.info("Processing finished: %s (%s%% confidence, %ss) - %s", recording.matched_model, str(recording.confidence), str(recording.processing_time), recording.sorted_location)
    logging.debug(recording)
  recording.close_video()

def analyse_folder(folder, output, unsure):
  [analyse_recording(os.path.join(folder, file), output, unsure) for file in get_files(folder)]
  if (len(failed_videos) > 0):
    logging.warning(str(len(failed_videos)) + " video(s) failed to process, please check logs")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='easily sort your dvr recordings without any effort')
  parser.add_argument('input', type=str, help="input folder or file which should be processed")
  parser.add_argument('output', type=str, help='output folder to which the sorted recordings should be saved')
  parser.add_argument('unsure', type=str, help='unsure folder which is used to store videos that could not be processed')
  parser.add_argument('-d', '--debug', help="turn on debug log statements", action="store_true")

  args = parser.parse_args()

  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG if args.debug else logging.INFO)

  if not exists(args.input):
    logging.error("File / Folder does not exist")
    sys.exit(-1)

  if is_folder(args.input):
    analyse_folder(args.input, args.output, args.unsure)
  else:
    analyse_recording(args.input, args.output, args.unsure)