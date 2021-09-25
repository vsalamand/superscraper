from fastapi import FastAPI
from scraper import get_recipe


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
