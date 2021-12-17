from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from scraper import get_recipe
from grocery_list import get_grocery_list
from tagger import get_entities


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
    return get_entities(ItemsList.items)

