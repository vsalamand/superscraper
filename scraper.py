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
import re

from requests import get
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import unquote
import json
import unidecode
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

INSTA_EMAIL = os.environ.get("INSTA_EMAIL")
INSTA_PWD = os.environ.get("INSTA_PWD")


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
    # clean URL
    url = urlparse(url).scheme + '://' + urlparse(url).netloc + urlparse(url).path

    """# 1. INSTAGRAM POST"""
    if ("instagram" in urlparse(url).netloc):

      try:
        insta_soup = get_insta_soup(url)
        insta_text = json.loads(insta_soup.find("script", type="application/ld+json").string)['caption']

        """ pre-process text """
        text = get_processed_text(insta_text)

        # get recipe data
        ingredients = get_ingredients([html.unescape(doc) for doc in text])
        images = insta_soup.find("meta", property='og:image')['content'].replace("\\u0026","&").split()


      except:
        ingredients = None
        images = None

      """ return recipe dic """
      recipe = {"recipe": {
               "name": None,
               "yield": None,
               "ingredients": ingredients,
               "images": images
              }
          }
      return recipe


    """# 2. STRUCTURED DATA - JSON-lD / MICRODATA"""
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


    """3. PARSE UNSTRUCTED DATA."""
    downloaded = fetch_url(url)

    # to get the main text of a page
    if downloaded != None:
        text_input = extract(downloaded, include_comments=False)

        """ pre-process text """
        text = get_processed_text(text_input)

        # get recipe data
        name = get_title(downloaded)
        images = download_images(url)
        if text != None:
          ingredients = get_ingredients([html.unescape(doc) for doc in text])
        else:
          ingredients = None


        """ return recipe ditc """
        recipe = {"recipe": {
                 "name": name,
                 "yield": None,
                 "ingredients": ingredients,
                 "images": images
                }
            }
        return recipe


    """4. NO PARSING."""

    recipe = {"recipe": {
                     "name": None,
                     "yield": None,
                     "ingredients": None,
                     "images": None
                    }
                }

    return recipe




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

    try:
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

    except ValueError:
        return None

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


def get_processed_text(text_input):
    # split in sentences
  text = sentence_parser(text_input)

  # parse sentences with ingredients only
  text = ingredients_parser(text).documents.tolist()

  return text


def sentence_parser(result):
    # getting all the paragraphs
    text = []
    try:
        #sentences = sent_tokenize(result, language='french')
        sentence_tokens = tokenizer.tokenize(result)

        # # decode and split sentences if digit is next to letter 'eg:pour 4 personnes4 courgettes'
        sentences = []
        for sentence in sentence_tokens:
            # unescape text in case of &#x27; types of characters with beautiful soup
            sentences.append(re.split("(?<=[a-z])(?=\\d)", html.unescape(sentence)))
        sentences = [item for sublist in sentences for item in sublist]

        for sentence in sentences:
            if (sentence.replace(",","* ").count('*') > 4):
                [text.append(x.strip()) for x
                                         in sentence.replace(",","* ").replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")
                                         if len(x) < 140 ]
            elif (sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").count('*') > 2):
                [text.append(x.strip()) for x
                                         in sentence.replace("\n","* ").replace("– ","* ").replace("- ","* ").replace("• ","* ").replace("• ","* ").split("* ")
                                         if len(x) < 140 ]
            else:
                [text.append(x.strip()) for x
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

    len_start = 0
    # do not take 1 image for over-blog sites
    if "over-blog" in url:
        len_start = 1

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
        return images[len_start:2]

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
        return images[len_start:2]

    # if no matche, look for figures images in soup
    for article in soup.find_all('figure'):
        for item in article.find_all('img'):
            try:
                image_url = unquote(item['src'])
                print(item['src'])
                image_url_patterns = get_url_patterns(image_url)
                pattern_matches = [x for x in url_patterns if x in image_url_patterns]
                if len(pattern_matches) > 0:
                    images.append(image_url)
                elif (any(x in ['uploads', 'image'] for x in image_url_patterns)):
                    images.append(item['src'])
            except:
                continue
    if (len(images) > 0):
        return images[len_start:2]

    # if no matches, return empty array
    return images[len_start:2]


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


def get_insta_soup(url):
  try:
    login_instagram()
    response = requests.get(url)
    print(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    return soup

  except:
      return None


def login_instagram():
  link = 'https://www.instagram.com/accounts/login/'
  login_url = 'https://www.instagram.com/accounts/login/ajax/'

  time = int(datetime.now().timestamp())

  payload = {
      'username': 'clubmama_',
      'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{INSTA_PWD}',
      'queryParams': {},
      'optIntoOneTap': 'false'
  }

  with requests.Session() as session:
      r = session.get(link)
      csrf = re.findall(r"csrf_token\":\"(.*?)\"", r.text)[0]
      login_header = {
              "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
              "X-Requested-With": "XMLHttpRequest",
              "Referer": "https://www.instagram.com/accounts/login/",
              "x-csrftoken": csrf
          }
      r = session.post(login_url, data=payload, headers=login_header)
      print(r.status_code)






