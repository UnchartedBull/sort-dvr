from tabulate import tabulate
from termcolor import colored
import datetime
import logging


def print_summary(recordings):
  recordings_tabular = [[
      colored(u'\u2713', 'green', attrs=['bold']) if not recording.has_errors() else
      colored(u'\u2718', 'red', attrs=['bold']), f'{str(datetime.timedelta(seconds=recording.duration))}h',
      recording.matched_model if recording.matched_model else '???', f'{recording.confidence}%', f'{recording.size}MB',
      f'{recording.compression}%', recording.original_location,
      recording.sorted_location if recording.sorted_location else '---',
      f'{str(datetime.timedelta(seconds=recording.processing_time))}', recording.error
  ] for recording in recordings]

  logging.info(
      "\n" + tabulate(
          recordings_tabular,
          tablefmt="fancy_grid",
          headers=[
              "Status", "Duration", "Model", "Confidence", "Size", "Compression", "Original", "New Location",
              "Processing Time", "Errors"
          ]
      )
  )


def print_recording_stats(recording):
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