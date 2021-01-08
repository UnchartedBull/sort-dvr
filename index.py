import logging
import coloredlogs
import os
import sys
import numpy as np

from read_modelname import get_modelname, write_mask, get_model_from_filename
from video_analysis import (
    analyse_video, get_start_frame, get_end_frame, calculate_duration, get_dimension, check_for_splits
)
from recording import Recording
from storage import exists, is_folder, get_next_filename, get_files, move_error_file, get_file_size
from render import render_video, calculate_timestamp_fps
from summary import print_summary
from parser import setup_parser

# TODO
# Database

recordings = []


def analyse_recording(filename, output, unsure, skip_split, model, dry, start_frame=0, end_frame=0):
  global recordings

  recording = Recording(filename, start_frame, end_frame)
  try:
    recording.open_video()

    logging.debug("Analysing Video ...")
    analyse_video(recording)
    get_dimension(recording)

    if not skip_split and start_frame == 0 and end_frame == 0:
      parts = check_for_splits(recording)

      if parts:
        recording.processing_finished()
        logging.info("Video contains %s recordings, splitting into different files", str(len(parts)))
        for part in parts:
          logging.debug("Video Part from frame %s to %s", str(int(part[0])), str(int(part[1])))
          analyse_recording(filename, output, unsure, skip_split, model, dry, part[0], part[1])
        raise Exception('video is split')

    ### REMOVING NOISE FROM START AND END ###
    get_start_frame(recording)
    get_end_frame(recording)
    calculate_duration(recording)

    raise Exception('stop')
    ### GET MODELNAME ###
    if get_model_from_filename(recording.original_location) and not model:
      logging.debug("Using Modelname from file ...")
      recording.confidence = 100
      recording.match_similarity = 100
      recording.ocr_text = "FILENAME"
      recording.matched_model = get_model_from_filename(filename)
    elif not model:
      logging.debug("Reading Modelname ...")
      (
          recording.ocr_text,
          recording.ocr_confidence,
          recording.matched_model,
          recording.match_similarity,
          masked_image,
      ) = get_modelname(recording.video, recording.start_frame, recording.end_frame)
      recording.confidence = round(np.mean([recording.ocr_confidence, recording.match_similarity]), 2)
      recording.masked_image_path = os.path.join(".", "name-masks", str(recording.uuid) + ".png")
      write_mask(recording.masked_image_path, masked_image)

      if recording.match_similarity < 80 or recording.ocr_confidence < 65 or (
          90 <= recording.match_similarity <= 99 and recording.ocr_confidence < 70
      ) or (recording.match_similarity < 90 and recording.ocr_confidence < 75):
        raise Exception("unsure result")
    else:
      recording.confidence = 100
      recording.match_similarity = 100
      recording.ocr_text = "PARAMETER"
      recording.matched_model = model

    ### RENDERING ###
    logging.debug("Rendering Video ...")
    recording.sorted_location = get_next_filename(os.path.join(output, recording.matched_model))
    if not dry:
      recording.average_bitrate = render_video(
          recording.original_location, recording.sorted_location,
          calculate_timestamp_fps(recording.start_frame, recording.fps),
          calculate_timestamp_fps(recording.end_frame, recording.fps), recording.end_frame - recording.start_frame,
          recording.dimension
      )

    ### FILE SIZES ###
    recording.original_size = get_file_size(recording.original_location)
    recording.size = get_file_size(recording.sorted_location)

  except Exception as e:
    recording.error = str(e)
    logging.debug(e, exc_info=True)

  ### CHECKING PROCESSING STATUS ###
  if recording.has_errors():
    if recording.error != 'video is split':
      logging.warning("Could not process video: %s", recording.error)
  else:
    logging.info(
        "Processing finished: %s (%s%% confidence, %ss) - %s",
        recording.matched_model,
        str(recording.confidence),
        str(round(recording.processing_time, 2)),
        recording.sorted_location,
    )

  logging.debug(recording)
  recording.processing_finished()
  if not recording.has_errors() or not recording.error == 'video is split':
    recordings.append(recording)


def analyse_folder(folder, output, unsure, skip_split, model, dry):
  [analyse_recording(os.path.join(folder, file), output, unsure, skip_split, model, dry) for file in get_files(folder)]


if __name__ == "__main__":
  args = setup_parser().parse_args()

  coloredlogs.install(fmt="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG if args.debug else logging.INFO)

  if not exists(args.input):
    logging.error("File / Folder does not exist")
    sys.exit(-1)

  if is_folder(args.input):
    analyse_folder(args.input, args.output, args.unsure, args.skip_split, args.model, args.dry)
  else:
    analyse_recording(args.input, args.output, args.unsure, args.skip_split, args.model, args.dry)

  for recording in recordings:
    if recording.has_errors() and recording.error != 'video is split' and not recording.is_part_of_split:
      move_error_file(recording.original_location, args.unsure, args.dry)

  print_summary(recordings)
