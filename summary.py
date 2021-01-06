from fuzzy_match import match_modelname
from tabulate import tabulate
import logging
import datetime
from termcolor import colored


def print_summary(recordings):
    recordings_tabular = [[
        colored(u'\u2713', 'green', attrs=['bold'])
        if not recording.has_errors() else colored(
            u'\u2718', 'red', attrs=['bold']),
        f'{str(datetime.timedelta(seconds=recording.duration))}h',
        recording.matched_model if recording.matched_model else '???',
        f'{recording.confidence}%', f'{recording.size}MB',
        f'{round(recording.size / max(recording.original_size, 1) * 100, 1)}%',
        recording.original_location,
        recording.sorted_location if recording.sorted_location else '---',
        f'{str(datetime.timedelta(seconds=recording.processing_time))}',
        recording.error
    ] for recording in recordings]

    logging.info("\n" + tabulate(
        recordings_tabular,
        tablefmt="fancy_grid",
        headers=[
            "Status", "Duration", "Model", "Confidence", "Size", "Compression",
            "Original", "New Location", "Processing Time", "Errors"
        ]))
