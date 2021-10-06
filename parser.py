import pandas as pd
import numpy as np
import pprint
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re
from thefuzz import fuzz
from thefuzz import process

import csv
with open('taxonomy.csv') as f:
    df_category_taxonomy = pd.read_csv(f)

def get_grocery_list(text_corpus):
    text_corpus = [doc[:40] for doc in text_corpus]
    # get vocab and clean categories list
    vocab, clean_categories_lowercase = get_vocab(df_category_taxonomy)
    clean_corpus = get_clean_corpus(vocab, text_corpus)
    categories_in_corpus = extract_categories(clean_corpus, clean_categories_lowercase)
    df_category_matches = df_category_taxonomy[df_category_taxonomy['clean_name'].isin(categories_in_corpus)]
    group_categories_by_section = df_category_matches.groupby('section')['name'].apply(lambda g: g.values.tolist()).to_dict()
    results = []
    results.append(group_categories_by_section)
    grocery_list_dict = {"grocery_list": results
                        }
    return grocery_list_dict


def clean_data(w):
    #stopwords_list = stopwords.words('french') not working in production
    w = w.lower()
    w=re.sub(r'[^\w\s]',' ',w)
    w=re.sub(r"([0-9])", r" ",w)
    words = w.split()
    clean_words = [word for word in words if len(word) > 2] #(word not in stopwords_list) and len(word) > 2]
    singularized_clean_words = TextBlob(" ".join(clean_words)).words.singularize()
    return " ".join(singularized_clean_words)

def get_vocab(df_category_taxonomy):
    clean_categories = df_category_taxonomy.clean_name.tolist()
    clean_categories_lowercase = [x.lower().split(" ") for x in clean_categories]
    clean_categories_lowercase_corpus = [item for sublist in clean_categories_lowercase for item in sublist]
    vocab = set(clean_categories_lowercase_corpus)
    return vocab, clean_categories_lowercase

def get_clean_corpus(vocab, text_corpus):
    # Lowercase each document, split it by white space and filter out stopwords
    texts = [[word for word in clean_data(document).split(' ')
                             if word in vocab]
                             for document in text_corpus]

    # Count word frequencies
    from collections import defaultdict
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1

    # Only keep words that appear more than once
    processed_corpus = [[token for token in text if frequency[token] > 0] for text in texts]
    #pprint.pprint(processed_corpus)
    return processed_corpus

def extract_categories(clean_corpus, clean_categories_lowercase):
    results = []
    for document in clean_corpus:
        # select 3 first items in document to boost first words
        ratios = process.extractOne(' '.join(document[:3]), clean_categories_lowercase)
        results.append(' '.join(ratios[0]))
    return results


