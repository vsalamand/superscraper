from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from scraper import get_recipe
from grocery_list import get_grocery_list
from tagger import get_tags
from tokenizer import get_tokens



app = FastAPI()


@app.get("/")
def read_main():
    return {"message": "Hello World"}


# Scrape link to extract recipe data
class RecipeUrl(BaseModel):
    url: str

@app.post("/r")
def recipe(recipe: RecipeUrl):
    recipe = get_recipe(recipe.url)
    if recipe is None:
      recipe = {"recipe": {
                       "name": None,
                       "yield": None,
                       "ingredients": None,
                       "images": None
                      }
                  }
    return recipe


# Convert ingredients into grocery list
class GroceryList(BaseModel):
    ingredients: list

@app.post("/glist")
def grocery_list(grocery_list: GroceryList):
    return get_grocery_list(grocery_list.ingredients)



# Scan text to extract entities (quantity, measures, products and ingredients)
class Items(BaseModel):
    items: list

@app.post("/scan")
def scan(ItemsList: Items):
    return get_tags(ItemsList.items)



# Tokenizer

@app.post("/tokenize")
def tokenize(ItemsList: Items):
    return get_tokens(ItemsList.items)



