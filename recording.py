import uuid
import time
import cv2
import logging
import datetime

from storage import is_video


class Recording:
    @property
    def uuid(self):
        return self._uuid

    @property
    def processing_time(self):
        if self._processing_time:
            return self._processing_time
        else:
            return time.time() - self._start

    @property
    def video(self):
        return self._video

    @property
    def compression(self):
        relative_size = round(self.size / max(self.original_size, 1) * 100, 1)
        return 100 - relative_size if relative_size > 0 and relative_size < 100 else 0

    def __init__(self, location) -> None:
        self._uuid = uuid.uuid1()
        self._start = time.time()
        self._video = None
        self._processing_time = None
        self.original_location = location
        self.sorted_location = None
        self.start_frame = None
        self.end_frame = None
        self.fps = 0
        self.original_duration = 0
        self.duration = 0
        self.original_dimension = None
        self.dimension = None
        self.average_bitrate = 0
        self.original_size = 0
        self.size = 0
        self.ocr_text = None
        self.ocr_confidence = 0
        self.masked_image_path = None
        self.matched_model = None
        self.match_similarity = 0
        self.confidence = 0
        self.error = None

        logging.info("Start processing video %s (%s)", self.original_location,
                     self._uuid)

    def __str__(self) -> str:
        return f"""
  UUID:                 {self._uuid}
  Original Location:    {self.original_location}
  Sorted Location:      {self.sorted_location}
  Start Frame:          {self.start_frame}
  End Frame:            {self.end_frame}
  FPS:                  {self.fps}
  Original Duration:    {str(datetime.timedelta(seconds=self.original_duration))}
  Duration:             {str(datetime.timedelta(seconds=self.duration))}
  Original Dimension:   {self.original_dimension}
  Dimension:            {self.dimension}
  Average Bitrate:      {self.average_bitrate}Kbps
  Original Size:        {self.original_size}MB
  New Size:             {self.size}MB
  Compression:          {self.compression}%
  OCR Text:             {self.ocr_text}
  OCR Confidence:       {self.ocr_confidence}%
  Masked Image Path:    {self.masked_image_path}
  Matched Model:        {self.matched_model}
  Match Similarity:     {self.match_similarity}%
  Error:                {self.error}
  Processing Time:      {str(datetime.timedelta(seconds=self.processing_time))}
  Confidence:           {self.confidence}%
    """

    def has_errors(self) -> bool:
        return self.error is not None

    def open_video(self) -> None:
        if not is_video(self.original_location):
            raise Exception("file is no video (.mp4, .mov, .avi, .mkv)")
        self._video = cv2.VideoCapture(self.original_location)

    def processing_finished(self) -> None:
        if self._video is not None:
            self._video.release()
        if self._processing_time is None:
            self._processing_time = self.processing_time
