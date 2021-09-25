"""Fetch structured JSON-LD OR MICRODATA data from a given URL."""
from typing import Optional, List
import pandas as pd
import numpy as np
import requests
import extruct
import pprint
import html
from w3lib.html import get_base_url
from trafilatura import fetch_url, extract
import trafilatura
from nltk.tokenize import sent_tokenize

from classifier import get_ingredients



# method to extract structured data

def get_recipe(url: str) -> Optional[List[dict]]:
    """Parse structured data from a URL. JSON-lD / MICRODATA"""
    metadata = get_metadata(url)
    if metadata:
      recipe_df = get_recipe_df(metadata)
      if recipe_df is not None:
          recipe = {"recipe": {
                       "name": html.unescape(recipe_df.name.values[0]),
                       "yield": get_servings(html.unescape(recipe_df.recipeYield.values[0])),
                       "ingredients": [html.unescape(el) for el in recipe_df.recipeIngredient.values[0]]
                      }
                  }
          return recipe

    """Parse unstructured data from a URL."""
    downloaded = fetch_url(url)
    # to get the main text of a page
    if downloaded != None:
        result = extract(downloaded, include_comments=False)
        text = sentence_parser(result)
        if text != None:
            recipe = {"recipe": {
                     "name": get_title(downloaded),
                     "yield": None,
                     "ingredients": get_ingredients([html.unescape(el) for el in text])
                    }
                }
            return recipe

    """If nothing was parsed correctly"""
    return None



def get_metadata(url: str):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
    r = requests.get(url, headers=headers)

    """Fetch JSON-LD & Microdata structured data."""
    metadata = extruct.extract(
        r.text,
        base_url = get_base_url(r.text, r.url),
        syntaxes=['json-ld', 'microdata'],
        uniform=True
    )
    if metadata.get('json-ld'):
      metadata = metadata['json-ld']
    else:
      metadata = metadata['microdata']

    if bool(metadata) and isinstance(metadata, list):
        metadata = metadata[0]

    return metadata

def get_recipe_df(metadata):
    #check metadata dict format
    if '@graph' in metadata:
        recipe_df = pd.DataFrame(metadata['@graph'])
    else:
        recipe_df = pd.DataFrame.from_dict(metadata, orient='index').transpose()

    try:
      #get first row with recipeIngredient
      recipe_df = recipe_df.sort_values(by='recipeIngredient').head(1)
      return recipe_df
    except:
      return None



def get_servings(value):
  if type(value) == list:
    return max(value)
  else:
    return value



def sentence_parser(result):
    # getting all the paragraphs
    text = []
    try:
        sentences = sent_tokenize(result, language='french')
        for sentence in sentences:
            if (sentence.replace(",","* ").count('*') > 4):
                [text.append(x.rstrip()) for x in sentence.replace(",","* ").replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")]
            elif (sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").count('*') > 2):
                [text.append(x.rstrip()) for x in sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")]
            else:
                [text.append(x.rstrip()) for x in sentence.replace('\n', '* ').replace('\r', '* ').replace('\xa0', '* ').split('* ')]

        # remove empty strings from list
        return list(filter(None, text))
    except:
        return None


def get_title(downloaded):
    return html.unescape(trafilatura.bare_extraction(downloaded)['title'])
