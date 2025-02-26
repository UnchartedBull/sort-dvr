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


def analyse_recording(file, args, start_frame=0, end_frame=0):
  global recordings

  recording = Recording(file, start_frame, end_frame)
  try:
    recording.open_video()

    logging.debug("Analysing Video ...")
    analyse_video(recording)
    get_dimension(recording)

    if not args.skip_split and start_frame == 0 and end_frame == 0:
      parts = check_for_splits(recording)

      if parts:
        recording.processing_finished()
        logging.info("Video contains %s recordings, splitting into different files", str(len(parts)))

        for part in parts:
          logging.debug("Video Part from frame %s to %s", str(int(part[0])), str(int(part[1])))
          analyse_recording(file, args, part[0], part[1])

        raise Exception('video is split')

    get_start_frame(recording)
    get_end_frame(recording)
    calculate_duration(recording)

    extract_modelname(recording, args.model)

    render_video(recording, args.output, args.dry_run, quality=args.x265_quality, audio_bitrate=args.audio_bitrate)

    get_recording_size(recording)
  except Exception as e:
    recording.error = str(e)
    logging.debug(e, exc_info=True)

  print_recording_stats(recording)

  recording.processing_finished()

  if not recording.has_errors() or not recording.error == 'video is split':
    recordings.append(recording)


def analyse_folder(args):
  [analyse_recording(os.path.join(args.input, file), args) for file in get_files(args.input)]


if __name__ == "__main__":
  args = setup_parser().parse_args()

  coloredlogs.install(fmt="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG if args.debug else logging.INFO)

  if not exists(args.input):
    logging.error("File / Folder does not exist")
    sys.exit(-1)

  if is_folder(args.input):
    analyse_folder(args)
  else:
    analyse_recording(args.input, args)

  for recording in recordings:
    if recording.has_errors() and recording.error != 'video is split' and not recording.is_part_of_split:
      move_error_file(recording.original_location, args.unsure, args.dry_run)

  print_summary(recordings)
