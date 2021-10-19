import pandas as pd
import numpy as np

from parser import ingredients_parser


def get_grocery_list(ingredient_inputs):
    # parse ingredients and return dataframe
    gl_df = ingredients_parser(ingredient_inputs)

    # hide unwanted categories
    hidden_cat = ["eau", "sel", "vegan"]
    remove_categories_by_index = gl_df.index[gl_df.clean_documents.str.contains('|'.join(hidden_cat))].tolist()
    gl_df = gl_df.drop(gl_df.index[remove_categories_by_index])

    # return dict of category list for each section
    group_categories_by_section = gl_df.groupby('section')['name'].apply(lambda g: list(set(g.values.tolist()))).to_dict()
    results = []
    results.append(group_categories_by_section)
    grocery_list_dict = {"grocery_list": results
                        }
    return grocery_list_dict
