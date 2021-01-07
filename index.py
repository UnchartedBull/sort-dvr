import logging
import coloredlogs
import os
import sys
import argparse
import numpy as np

from read_modelname import get_modelname, write_mask, get_model_from_filename
from video_analysis import (analyse_video, get_start_frame, get_end_frame,
                            calculate_duration, get_dimension, check_for_split)
from recording import Recording
from storage import exists, is_folder, get_next_filename, get_files, move_error_file, get_file_size
from render import render_video, calculate_timestamp_fps
from summary import print_summary

# TODO
# Database

recordings = []


def analyse_recording(filename,
                      output,
                      unsure,
                      skip_split,
                      model,
                      dry,
                      start_frame=0,
                      end_frame=0):
    global recordings

    recording = Recording(filename)
    try:
        recording.open_video()

        logging.debug("Analysing Video ...")
        (recording.fps,
         recording.original_duration) = analyse_video(recording.video,
                                                      start_frame, end_frame)
        (recording.original_dimension,
         recording.dimension) = get_dimension(recording.video)

        if not skip_split and start_frame == 0 and end_frame == 0:
            splits = check_for_split(recording.video, recording.fps)
            if recording.original_duration / (len(splits) + 1) < 120:
                raise Exception('more than 1 split per 2m')
            if len(splits) > 0:
                logging.info(
                    "Video contains %s recordings, splitting into different files",
                    str(len(splits) + 1))
                for i in range(len(splits) + 1):
                    split_start_frame = splits[i - 1] if i > 0 else 0
                    split_end_frame = splits[i] if i < len(
                        splits
                    ) else recording.fps * recording.original_duration
                    logging.debug("Split %s from frame %s to %s", str(i + 1),
                                  str(int(split_start_frame)),
                                  str(int(split_end_frame)))
                    analyse_recording(filename, output, unsure, skip_split,
                                      model, dry, split_start_frame,
                                      split_end_frame)
                else:
                    raise Exception('video is split')

        recording.start_frame = get_start_frame(recording.video, start_frame)
        recording.end_frame = get_end_frame(recording.video, end_frame)
        recording.duration = calculate_duration(
            recording.end_frame - recording.start_frame, recording.fps)
        if recording.duration < 60:
            raise Exception('start / end frame too close')

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
            ) = get_modelname(recording.video, recording.start_frame,
                              recording.end_frame)
            recording.confidence = round(
                np.mean([recording.ocr_confidence,
                         recording.match_similarity]), 2)
            recording.masked_image_path = os.path.join(
                ".", "name-masks",
                str(recording.uuid) + ".png")
            write_mask(recording.masked_image_path, masked_image)

            if recording.match_similarity < 80 or recording.ocr_confidence < 65 or (
                    90 <= recording.match_similarity <= 99
                    and recording.ocr_confidence < 70) or (
                        recording.match_similarity < 90
                        and recording.ocr_confidence < 75):
                raise Exception("unsure result")
        else:
            recording.confidence = 100
            recording.match_similarity = 100
            recording.ocr_text = "PARAMETER"
            recording.matched_model = model

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
        recording.error = str(e)
        logging.debug(e, exc_info=True)

    if recording.has_errors():
        move_error_file(recording.original_location, unsure, dry)
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
    if not recording.error or not recording.error == 'video is split':
        recordings.append(recording)


def analyse_folder(folder, output, unsure, skip_split, model, dry):
    [
        analyse_recording(os.path.join(folder, file), output, unsure,
                          skip_split, model, dry) for file in get_files(folder)
    ]


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
    parser.add_argument("--model", help="manually specify model (skip OCR)")
    parser.add_argument("--skip_split",
                        help="don't check for video splits",
                        action="store_true")
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
        analyse_folder(args.input, args.output, args.unsure, args.skip_split,
                       args.model, args.dry)
    else:
        analyse_recording(args.input, args.output, args.unsure,
                          args.skip_split, args.model, args.dry)

    print_summary(recordings)
