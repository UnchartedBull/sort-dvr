import logging
import coloredlogs
import os
import sys

from parser import setup_parser
from read_modelname import extract_modelname
from recording import Recording
from render import render_video
from storage import exists, is_folder, get_files, move_error_file, get_recording_size
from summary import print_summary, print_recording_stats
from video_analysis import (
    analyse_video, get_start_frame, get_end_frame, calculate_duration, get_dimension, check_for_splits
)

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

    get_start_frame(recording)
    get_end_frame(recording)
    calculate_duration(recording)

    extract_modelname(recording, model)

    render_video(recording, output, dry, quality=30, audio_bitrate="32k")

    get_recording_size(recording)
  except Exception as e:
    recording.error = str(e)
    logging.debug(e, exc_info=True)

  print_recording_stats(recording)

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
