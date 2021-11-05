import requests
import pandas as pd

from parser import get_matches

from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

HF_API_KEY = os.environ.get("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/vsalamand/autonlp-fr_get_ingredient_sentences-18353298"
headers = {"Authorization": HF_API_KEY}

# GET PREDICTIONS USING HF INFERENCE API
def query(payload):
  response = requests.post(API_URL, headers=headers, json=payload)
  return response.json()


def get_ingredients(text_list):
  try:
    # use only first N words to limit HF API usage based on characters
    inputs = [" ".join(string.lower().split(" ")[:3]) for string in text_list]

    # output is a list of list of dic with label and score using HF INFERENCE API
    outputs = query(inputs)

    # extract label predicted for each input
    predictions = []
    for result in outputs:
      predictions.append(max(result, key=lambda d: d['score'])['label'])

    # return list of text inputs that correspond to ingredients
    df = pd.DataFrame(list(zip(text_list, predictions)), columns = ['text', 'preds'])
    df_ingredients = df[df["preds"].isin(['1', 'yes'])]

    ## remove duplicated ingredients (eg: when instructions are considered like ingredients)
    #df_ingredients['matches'] = df_ingredients['text'].apply(get_matches)
    #df_ingredients = df_ingredients.drop_duplicates(subset='matches', keep="first")

    # return ingredients as list based on predictions
    ingredients = [ing.strip() for ing in df_ingredients.text.to_list()]
    return  ingredients

  except:
    return None





# #--- HF PYTHON API = NOT WORKING ON HEROKU BECAUSE OF MEMORY LEAK + HARD TO MANAGE SLUG SIZE WITH TORCH ---


# from dotenv import load_dotenv
# import os

# load_dotenv()  # take environment variables from .env.

# HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# import torch
# tokenizer = AutoTokenizer.from_pretrained("vsalamand/autonlp-fr_get_ingredient_sentences-18353298", use_auth_token=HF_API_TOKEN)
# model = AutoModelForSequenceClassification.from_pretrained("vsalamand/autonlp-fr_get_ingredient_sentences-18353298", use_auth_token=HF_API_TOKEN)
# labels = model.config.id2label


# def get_predictions(inputs):
#   tokenized_inputs = tokenizer(inputs, max_length= 10, padding=True, truncation=True, return_tensors="pt")

#   outputs = model(**tokenized_inputs)

#   # get outputs tensor
#   probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
#   # FIid index of max value in tensor to match with corresponding label
#   predictions = [labels[i] for i in torch.argmax(probabilities, dim=1).tolist()]

#   return predictions


