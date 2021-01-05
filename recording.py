import uuid
import time
import cv2
import logging

class Recording:

  @property
  def uuid(self):
    return self._uuid

  @property
  def processing_time(self):
    return str(round(time.time() - self._start, 2))

  @property
  def video(self):
    return self._video

  def __init__(self, location) -> None:
    self._uuid = uuid.uuid1()
    self._start = time.time()
    self._video = None
    self.original_location = location
    self.sorted_location = None
    self.start_frame = None
    self.end_frame = None
    self.fps = 0
    self.original_duration = 0
    self.duration = 0
    self.ocr_text = None
    self.ocr_confidence = 0
    self.masked_image_path = None
    self.matched_model = None
    self.match_similarity = 0
    self.confidence = 0
    self.error = None

    self._open_video()

    logging.info("Start processing video %s (%s)", self.original_location, self._uuid)

  def __str__(self) -> str:
    return f"""
  UUID:                 {self._uuid}
  Original Location:    {self.original_location}
  Sorted Location:      {self.sorted_location}
  Start Frame:          {self.start_frame}
  End Frame:            {self.end_frame}
  FPS:                  {self.fps}
  Original Duration:    {self.original_duration}s
  Duration:             {self.duration}s
  OCR Text:             {self.ocr_text}
  OCR Confidence:       {self.ocr_confidence}%
  Masked Image Path:    {self.masked_image_path}
  Matched Model:        {self.matched_model}
  Match Similarity:     {self.match_similarity}%
  Error:                {self.error}
  Processing Time:      {self.processing_time}s
  Confidence:           {self.confidence}%
    """

  def has_errors(self) -> bool:
    return self.error is not None

  def _open_video(self) -> None:
    self._video = cv2.VideoCapture(self.original_location)

  def close_video(self) -> None:
    self._video.release()