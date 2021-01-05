import csv
from fuzzywuzzy import fuzz

def load_csv():
  with open('modelnames.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
      return row


def match_modelname(detected_text):
  modelnames = load_csv()
  best_match = None
  best_match_similarity = 0
  for model in modelnames:
    similarity = fuzz.ratio(detected_text.lower(), model.lower())
    if similarity > best_match_similarity:
      best_match = model
      best_match_similarity = similarity
  return (best_match, best_match_similarity)

if __name__ == "__main__":
  print(match_modelname('FROG) LITE 4'))
