import pandas as pd
import numpy as np

import requests

from tokenizer import get_tokens

from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
HF_API_KEY = os.environ.get("HF_API_KEY")
# API_URL = "https://api-inference.huggingface.co/models/Jean-Baptiste/camembert-ner"
API_URL = "https://api-inference.huggingface.co/models/vsalamand/fr_ner_ingredients"
headers = {"Authorization": HF_API_KEY}


def get_tags(items):
  tokens = get_tokens(items)
  # Sending multiple queries for each item because querying list of strings is not working, the system is only accepting string input.
  entities = [query_ner_tagger(item) for item in items]
  # entities = query_ner_tagger(items)
  print(entities)

  tags = []

  for i in range(len(items)):
    tokens_with_entities, entities_with_token_ids = enrich(tokens[i], entities[i])

    annotations = {
      "doc": items[i],
      "tokens": tokens_with_entities,
      "entities": entities_with_token_ids
    }
    tags.append(annotations)

  return tags



def query_ner_tagger(payload):
  try:
    response = requests.post(API_URL, headers=headers, json=payload,)
    return response.json()
  except:
    print(response)



def enrich(tokens, entities):
  for entity in entities:
    token_start = next((sub for sub in tokens if sub['start'] == entity['start']), None)
    token_end = next((sub for sub in tokens if sub['end'] == entity['end']), None)

    if token_start is not None and token_end is not None:
      entity["token_start"] = token_start["id"]
      entity["token_end"] = token_end["id"]

      for i in list(range(entity["token_start"], entity["token_end"]+1)):
          token = next(x for x in tokens if x["id"] == i)
          token["entity_group"] = entity["entity_group"]

  return tokens, entities
