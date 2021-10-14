import pandas as pd
import numpy as np
import pprint
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re
from thefuzz import fuzz
from thefuzz import process

# get taxonomy from file
import csv
with open('taxonomy.csv') as f:
    df_category_taxonomy = pd.read_csv(f)

# get vocab and clean categories list
def get_vocab(df_category_taxonomy):
    clean_categories = df_category_taxonomy.clean_name.tolist()
    clean_categories_lowercase = [x.lower().split(" ") for x in clean_categories]
    clean_categories_lowercase_corpus = [item for sublist in clean_categories_lowercase for item in sublist]
    vocab = set(clean_categories_lowercase_corpus)
    return vocab, clean_categories_lowercase

vocab, clean_categories_lowercase = get_vocab(df_category_taxonomy)

# Create units stopowrds
stopwords = []
stopwords.append(["gramme"])
stopwords.append(["cuillère à soupe", "cuillères à soupe", "c. à soupe", "cuillère(s) à soupe", "c. à table", "cuillère à table"])
stopwords.append(["cuillère à café", "cuillère à café", "c. à café", "cuillère(s) à café", "c. à thé", "cuillère à thé"])
stopwords_list = [item for sublist in stopwords for item in sublist]

def get_grocery_list(text_corpus):
    # initialize dataframe
    gl_df = pd.DataFrame({'documents':text_corpus})

    # filter documents characters limit
    text_corpus = [doc[:40] for doc in text_corpus]

    # return list clean documents based on vocab
    clean_corpus = get_clean_corpus(vocab, text_corpus)
    gl_df['clean_documents'] = clean_corpus

    # return list of matched categories based on clean docuements
    gl_df['clean_name'] = gl_df['clean_documents'].apply(get_matches)

    # merge grocery list df and taxonomy df based on clean name
    gl_df = gl_df.merge(df_category_taxonomy[['name', 'section', 'clean_name']], on='clean_name', how='left').drop_duplicates(subset=['documents'], keep='last')

    # return dict of category list for each section
    group_categories_by_section = gl_df.groupby('section')['name'].apply(lambda g: list(set(g.values.tolist()))).to_dict()
    results = []
    results.append(group_categories_by_section)
    grocery_list_dict = {"grocery_list": results
                        }
    return grocery_list_dict

def clean_data(w):
    #stopwords_list = stopwords.words('french') not working in production
    w = remove_long_unit_patterns(w)
    w = w.lower()
    w=re.sub(r'[^\w\s]',' ',w)
    w=re.sub(r"([0-9])", r" ",w)
    words = w.split()
    # remove ingredients starting with 'pour' because indicates ingredients group
    if words[0] == "pour":
        return ""
    elif [word for word in words if "eau" in word]:
        return ""
    else:
        clean_words = [word for word in words if len(word) > 2] #(word not in stopwords_list) and len(word) > 2]
        singularized_clean_words = TextBlob(" ".join(clean_words)).words.singularize()
        return " ".join(singularized_clean_words)

def remove_long_unit_patterns(document):
    for pattern in stopwords_list:
        document = document.lower().replace(pattern, "")
    return document

def get_clean_corpus(vocab, text_corpus):
    # Lowercase each document, split it by white space and filter out stopwords
    texts = [[word for word in clean_data(document).split(' ')
                             if word in list(vocab)]
                             for document in text_corpus]
    # Only keep 3 first words that appear more than once and join as a string
    processed_corpus = [' '.join([token for token in text[:3]]) for text in texts]
    #pprint.pprint(processed_corpus)
    return processed_corpus

def get_matches(clean_document):
    if len(clean_document) > 0:
        # find exact matches
        if len(df_category_taxonomy[df_category_taxonomy['clean_name'].str.match(clean_document)]) > 0:
            return clean_document
        else:
            # else get 3 top possibilities
            possibilities = process.extract(clean_document, list(df_category_taxonomy.clean_name), limit=3)
            # find exact word in clean document
            possible_words = [possible[0] for possible in possibilities if possible[1] > 89]
            top_possibility = [word for word in clean_document.split(' ') if word in possible_words]
            # return exact word match
            if len(top_possibility) > 0:
                return top_possibility[0]
            # else return top possiblity
            else:
                return possibilities[0][0]
    else:
        return


