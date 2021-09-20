from pathlib import Path
import spacy
import html


model_dir = Path('models/spacy-recipe-classifier')
nlp = spacy.load(model_dir)

def get_ingredients(text_list):
    docs = list(nlp.pipe(text_list))
    predictions = []
    for doc in docs:
        if max(doc.cats, key=doc.cats.get) == "ingredient":
            predictions.append(html.unescape(doc.text))
    return predictions
