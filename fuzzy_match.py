import csv
from fuzzywuzzy import fuzz

MODELNAMES = None


def load_modelnames():
  global MODELNAMES

  with open('modelnames.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')

    for row in reader:
      MODELNAMES = row


def match_modelname(detected_text):
  global MODELNAMES

  best_match = None
  best_match_similarity = 0

  for model in MODELNAMES:
    similarity = fuzz.ratio(detected_text.lower(), model.lower())

    if similarity > best_match_similarity:
      best_match = model
      best_match_similarity = similarity

  return (best_match, best_match_similarity)
