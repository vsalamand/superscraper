from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from scraper import get_recipe
from parser import get_grocery_list


app = FastAPI()


@app.get("/")
def read_main():
    return {"message": "Hello World"}

@app.get("/r/u={url:path}")
def recipe(url: str):
    recipe = get_recipe(url)
    if recipe is None:
      recipe = {"recipe": {
                       "name": None,
                       "yield": None,
                       "ingredients": None
                      }
                  }
    return recipe


class GroceryList(BaseModel):
    ingredients: list

@app.post("/glist")
def grocery_list(grocery_list: GroceryList):
    return get_grocery_list(grocery_list.ingredients)
