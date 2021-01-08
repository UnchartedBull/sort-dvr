from pathlib import Path
import logging
import os
import re


def exists(path) -> bool:
  return os.path.exists(path)


def is_folder(path) -> bool:
  return os.path.isdir(path)


def is_video(path) -> None:
  return (".mp4" not in path or ".mov" not in path or ".avi" not in path or ".mkv" not in path)


def create_if_not_exist(path) -> bool:
  Path(path).mkdir(parents=True, exist_ok=True)


def get_files(path):
  files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
  files.sort(reverse=False)
  return files


def get_next_filename(path):
  create_if_not_exist(path)
  numbers = [
      int(re.search("\d+|$", n).group())
      for n in get_files(path)
      if re.match("^#[\d]{3}(?:\.mp4|\.avi|\.mov|\.mkv)$", n)
  ]
  number = 0

  if not numbers:
    number = 1
  else:
    number = max(numbers) + 1

  return os.path.join(path, "#" + str(number).zfill(3) + ".mp4")


def get_file_size(path):
  if exists(path) and not is_folder(path):
    return round(round(os.path.getsize(path) / (1024 * 1024), 3))
  else:
    return 0


def move_error_file(path, unsure, dry):
  if not dry and exists(path):
    create_if_not_exist(unsure)
    new_location = os.path.join(unsure, os.path.split(path)[1])
    logging.debug("Copying unsure file from %s to %s", path, new_location)
    os.rename(path, new_location)


def get_recording_size(recording):
  recording.original_size = get_file_size(recording.original_location)
  recording.size = get_file_size(recording.sorted_location)
