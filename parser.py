import argparse


def setup_parser():
  parser = argparse.ArgumentParser(description="easily sort your dvr recordings without any effort")
  parser.add_argument("input", type=str, help="input folder or file which should be processed")
  parser.add_argument(
      "output",
      type=str,
      help="output folder to which the sorted recordings should be saved",
  )
  parser.add_argument(
      "unsure",
      type=str,
      help="unsure folder which is used to store videos that could not be processed",
  )
  parser.add_argument("--model", help="manually specify model (skip OCR)")
  parser.add_argument("--skip_split", help="don't check for video splits", action="store_true")
  parser.add_argument("--dry", help="don't render or move video files, just analyse", action="store_true")
  parser.add_argument("-d", "--debug", help="turn on debug log statements", action="store_true")

  return parser
