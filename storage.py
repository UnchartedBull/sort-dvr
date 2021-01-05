import os
from pathlib import Path
import re

def exists(path) -> bool:
  return os.path.exists(path)

def is_folder(path) -> bool:
  return os.path.isdir(path)

def is_video(path) -> None:
  return ".mp4" not in path or ".mov" not in path or ".avi" not in path or ".mkv" not in path

def create_if_not_exist(path) -> bool:
  Path(path).mkdir(parents=True, exist_ok=True)

def get_files(path):
  return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

def get_file_numbers(path):
  return [int(re.search('\d+|$', f).group()) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

def get_next_filename(path):
  create_if_not_exist(path)
  numbers = [int(re.search('\d+|$', n).group()) for n in get_files(path)]
  number = 0

  if not number:
    number = 1
  else:
    number = max(numbers) + 1

  return os.path.join(path, '#' + str(number).zfill(3) + '.mp4')
