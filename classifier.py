import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

HF_API_KEY = os.environ.get("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/vsalamand/autonlp-fr_get_ingredient_sentences-18353298"
headers = {"Authorization": HF_API_KEY}

def query(payload):
  response = requests.post(API_URL, headers=headers, json=payload)
  return response.json()

def get_ingredients(text_list):
  print('yo')
  try:
    # use only first N words to limit HF API usage based on characters
    inputs = [" ".join(string.lower().split(" ")[:3]) for string in text_list]

    # output is a list of list of dic with label and score
    output = query(inputs)
    print(output)
    # retry if model is not loaded yet
    if not isinstance(output, list):
      time.sleep(10)
      output = query(inputs)

    # extract label predicted for each input
    preds = []
    for result in output:
      preds.append(max(result, key=lambda d: d['score'])['label'])

    # return list of text inputs that correspond to ingredients
    df = pd.DataFrame(list(zip(text_list, preds)), columns = ['text', 'preds'])
    df_ingredients = df[df["preds"].isin(['1', 'yes'])]

    return df_ingredients.text.to_list()

  except:
    return None

