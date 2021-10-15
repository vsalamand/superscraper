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

from requests import get
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import unquote

#from nltk.tokenize import sent_tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
punkt_param = PunktParameters()
abbreviation = ['cuil']
punkt_param.abbrev_types = set(abbreviation)
tokenizer = PunktSentenceTokenizer(punkt_param)

from classifier import get_ingredients
from parser import ingredients_parser



"""--- MASTER PARSER METHOD to parse structured data, if fail, try unstructured data"""

def get_recipe(url: str) -> Optional[List[dict]]:

    """# 1. STRUCTURED DATA - JSON-lD / MICRODATA"""
    metadata = get_metadata(url)
    if metadata:
      recipe_df = get_recipe_df(metadata)

      if recipe_df is not None:
          recipe = {"recipe": {
                       "name": html.unescape(recipe_df.name.values[0]),
                       "yield": get_servings(html.unescape(recipe_df.recipeYield.values[0])),
                       "ingredients": [html.unescape(el) for el in recipe_df.recipeIngredient.values[0]],
                       "images": get_images(recipe_df)
                      }
                  }
          return recipe

    """2. PARSE UNSTRUCTED DATA."""
    downloaded = fetch_url(url)

    # to get the main text of a page
    if downloaded != None:
        result = extract(downloaded, include_comments=False)

        # split in sentences
        text = sentence_parser(result)

        # parse sentences with ingredients only
        text = ingredients_parser(text).dropna().documents.tolist()

        if text != None:
            recipe = {"recipe": {
                     "name": get_title(downloaded),
                     "yield": None,
                     "ingredients": get_ingredients([html.unescape(doc) for doc in text]),
                     "images": download_images(url)
                    }
                }
            return recipe

    """If nothing was parsed correctly"""
    return None




"""--- PARSER METHODS BELOW ---"""

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
        #sentences = sent_tokenize(result, language='french')
        sentences = tokenizer.tokenize(result)
        for sentence in sentences:
            if (sentence.replace(",","* ").count('*') > 4):
                [text.append(x.rstrip()) for x
                                         in sentence.replace(",","* ").replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")
                                         if len(x) < 140 ]
            elif (sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").count('*') > 2):
                [text.append(x.rstrip()) for x
                                         in sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")
                                         if len(x) < 140 ]
            else:
                [text.append(x.rstrip()) for x
                                         in sentence.replace('\n', '* ').replace('\r', '* ').replace('\xa0', '* ').split('* ')
                                         if len(x) < 140 ]

        # remove empty strings from list
        return list(filter(None, text))[:30]
    except:
        return None


def get_title(downloaded):
    return html.unescape(trafilatura.bare_extraction(downloaded)['title'])


def get_images(recipe_df):
    images = recipe_df.image.values[0]
    if isinstance(images, str):
        image_array = []
        image_array.append(images)
        return image_array
    else:
        return images



def download_images(url):
    url_patterns = get_url_patterns(url)
    htmldata = requests.get(url).text
    soup = BeautifulSoup(htmldata, 'html.parser')

    images = []

    # search images in soup
    for item in soup.find_all('img'):
        try:
            image_url = unquote(item['src'])
            image_url_patterns = get_url_patterns(image_url)
            pattern_matches = [x for x in url_patterns if x in image_url_patterns]
            if len(pattern_matches) > 0:
                images.append(image_url)
        except:
            continue
    if (len(images) > 0):
        return images[:2]

    # if no matche, look for articles images in soup
    for article in soup.find_all('article'):
        for item in article.find_all('img'):
            try:
                image_url = unquote(item['src'])
                image_url_patterns = get_url_patterns(image_url)
                pattern_matches = [x for x in url_patterns if x in image_url_patterns]
                if len(pattern_matches) > 0:
                    images.append(image_url)
                elif 'uploads' in image_url_patterns :
                    images.append(image_url)
            except:
                continue
    if (len(images) > 0):
        return images[:2]

    # if no matches, return empty array
    return images[:2]


def get_url_patterns(url):
    url = unquote(url)
    path = urlparse(url).path
    path_elements = path.split('/')
    path_elements = [el.split('-') for el in path_elements if el]
    path_elements = [item for sublist in path_elements for item in sublist]
    path_elements = [el.split('_') for el in path_elements if el]
    path_elements = [item.lower() for sublist in path_elements for item in sublist]
    path_elements = [el.split('+') for el in path_elements if el]
    path_elements = [item.lower() for sublist in path_elements for item in sublist]
    return path_elements

