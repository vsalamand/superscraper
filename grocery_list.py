import pandas as pd
import numpy as np

from parser import ingredients_parser


def get_grocery_list(ingredient_inputs):
    # parse ingredients and return dataframe
    gl_df = ingredients_parser(ingredient_inputs)

    # group df by section and get clean product/category lists
    group_categories_by_section = gl_df.groupby('section')['name'].apply(lambda g: get_clean_product_list(g.values.tolist()) ).to_dict()

     # return dict of category list for each section
    results = []
    results.append(group_categories_by_section)
    grocery_list_dict = {"grocery_list": results
                        }
    return grocery_list_dict


def get_clean_product_list(product_list):
  # hide unwanted categories
  hidden_cat = ["eau", "sel", "vegan"]
  # return product list without duplicates and unwanted categories
  products = [p for p in product_list if p.lower() not in hidden_cat]
  return list(set( products ))
