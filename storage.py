import os

def check_exists(path) -> bool:
  return os.path.exists(path)

def check_folder(path) -> bool:
  return os.path.isdir(path)

def check_is_video(path) -> None:
  if ".mp4" not in path or ".mov" not in path or ".avi" not in path or ".mkv" not in path:
    raise Exception('file is no video (.mp4, .mov, .avi, .mkv)')