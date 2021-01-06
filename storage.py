import os
from pathlib import Path
import re
import logging


def exists(path) -> bool:
    return os.path.exists(path)


def is_folder(path) -> bool:
    return os.path.isdir(path)


def is_video(path) -> None:
    return (".mp4" not in path or ".mov" not in path or ".avi" not in path
            or ".mkv" not in path)


def create_if_not_exist(path) -> bool:
    Path(path).mkdir(parents=True, exist_ok=True)


def get_files(path):
    return [
        f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]


def get_next_filename(path):
    create_if_not_exist(path)
    numbers = [
        int(re.search("\d+|$", n).group()) for n in get_files(path)
        if re.match("^#[\d]{3}(?:\.mp4|\.avi|\.mov|\.mkv)$", n)
    ]
    number = 0

    if not numbers:
        number = 1
    else:
        number = max(numbers) + 1

    return os.path.join(path, "#" + str(number).zfill(3) + ".mp4")


def move_error_file(path, unsure):
    create_if_not_exist(unsure)
    new_location = os.path.join(unsure, os.path.split(path)[1])
    logging.debug("Moving unsure file from %s to %s", path, new_location)
    # os.rename(path, new_location)
