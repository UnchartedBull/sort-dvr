import logging
import coloredlogs
import os
import sys
import argparse
import numpy as np

from read_modelname import get_modelname, write_mask, get_model_from_filename
from video_analysis import (analyse_video, get_start_frame, get_end_frame,
                            calculate_duration, get_dimsension)
from recording import Recording
from storage import exists, is_folder, get_next_filename, get_files, move_error_file, get_file_size
from render import render_video, calculate_timestamp_fps
from summary import print_summary

# TODO
# Database

recordings = []


def analyse_recording(filename, output, unsure, dry):
    global recordings

    recording = Recording(filename)
    try:
        recording.open_video()

        logging.debug("Analysing Video ...")
        (recording.fps,
         recording.original_duration) = analyse_video(recording.video)
        (recording.original_dimension,
         recording.dimension) = get_dimsension(recording.video)
        recording.start_frame = get_start_frame(recording.video)
        recording.end_frame = get_end_frame(recording.video)
        recording.duration = calculate_duration(
            recording.end_frame - recording.start_frame, recording.fps)

        if get_model_from_filename(recording.original_location):
            logging.debug("Using Modelname from file ...")
            recording.confidence = 100
            recording.match_similarity = 100
            recording.ocr_text = "FILENAME"
            recording.matched_model = get_model_from_filename(filename)
        else:
            logging.debug("Reading Modelname ...")
            (
                recording.ocr_text,
                recording.ocr_confidence,
                recording.matched_model,
                recording.match_similarity,
                masked_image,
            ) = get_modelname(recording.video, recording.start_frame,
                              recording.end_frame)
            recording.confidence = round(
                np.mean([recording.ocr_confidence,
                         recording.match_similarity]), 2)
            recording.masked_image_path = os.path.join(
                ".", "name-masks",
                str(recording.uuid) + ".png")
            write_mask(recording.masked_image_path, masked_image)

        logging.debug("Rendering Video ...")
        recording.sorted_location = get_next_filename(
            os.path.join(output, recording.matched_model))
        if not dry:
            recording.average_bitrate = render_video(
                recording.original_location, recording.sorted_location,
                calculate_timestamp_fps(recording.start_frame, recording.fps),
                calculate_timestamp_fps(recording.end_frame, recording.fps),
                recording.end_frame - recording.start_frame,
                recording.dimension)
        recording.original_size = get_file_size(recording.original_location)
        recording.size = get_file_size(recording.sorted_location)

    except Exception as e:
        recording.error = e
        logging.debug(e, exc_info=True)

    if recording.has_errors():
        move_error_file(recording.original_location, unsure)
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
    recordings.append(recording)
    recording.close_video()


def analyse_folder(folder, output, unsure, dry):
    [
        analyse_recording(os.path.join(folder, file), output, unsure, dry)
        for file in get_files(folder)
    ]
    # if len(recordings) > 0:
    #     logging.warning(
    #         str(len(recordings)) +
    #         " video(s) failed to process, please check logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="easily sort your dvr recordings without any effort")
    parser.add_argument("input",
                        type=str,
                        help="input folder or file which should be processed")
    parser.add_argument(
        "output",
        type=str,
        help="output folder to which the sorted recordings should be saved",
    )
    parser.add_argument(
        "unsure",
        type=str,
        help=
        "unsure folder which is used to store videos that could not be processed",
    )
    parser.add_argument("--dry",
                        help="don't render or move video files, just analyse",
                        action="store_true")
    parser.add_argument("-d",
                        "--debug",
                        help="turn on debug log statements",
                        action="store_true")

    args = parser.parse_args()

    coloredlogs.install(fmt="%(asctime)s %(levelname)s %(message)s",
                        level=logging.DEBUG if args.debug else logging.INFO)

    if not exists(args.input):
        logging.error("File / Folder does not exist")
        sys.exit(-1)

    if is_folder(args.input):
        analyse_folder(args.input, args.output, args.unsure, args.dry)
    else:
        analyse_recording(args.input, args.output, args.unsure, args.dry)

    print_summary(recordings)
