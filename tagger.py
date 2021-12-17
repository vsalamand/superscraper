import pandas as pd
import numpy as np

import requests

from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

HF_API_KEY = os.environ.get("HF_API_KEY")


API_URL = "https://api-inference.huggingface.co/models/gilf/french-camembert-postag-model"
headers = {"Authorization": HF_API_KEY}

def query(payload):
  response = requests.post(API_URL, headers=headers, json=payload)
  return response.json()


def get_entities(items):
  outputs = query(items)
  # return outputs

  entities = []
  for i in range(len(items)):
    annotations = {
      "doc": items[i],
      "tokens": outputs[i]
    }
    entities.append(annotations)

  return entities


