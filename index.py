import logging
import traceback
import os

from read_modelname import get_modelname, write_mask
from video_analysis import analyse_video, get_start_frame, get_end_frame, calculate_duration
from recording import Recording


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

  recording = Recording('./test/video-1.mov')

  try:
    logging.debug("Analysing Video ...")
    (recording.fps, recording.original_duration) = analyse_video(recording.video)
    recording.start_frame = get_start_frame(recording.video)
    recording.end_frame = get_end_frame(recording.video)
    recording.duration = calculate_duration(recording.end_frame - recording.start_frame, recording.fps)

    logging.debug("Reading Modelname ...")
    (recording.ocr_text, recording.ocr_confidence, recording.matched_model, recording.match_similarity, masked_image) = get_modelname(recording.video, recording.start_frame, recording.end_frame)
    recording.masked_image_path = os.path.join('.', 'name-masks', str(recording.uuid) + '.png')
    write_mask(recording.masked_image_path, masked_image)

    recording.sorted_location = os.path.join('.', 'sorted-tmp', recording.matched_model, '#001.mp4')
  except Exception as e:
    recording.error = e
    traceback.print_exc()

  logging.debug(recording)