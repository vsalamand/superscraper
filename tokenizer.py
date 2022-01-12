from transformers import AutoTokenizer, AutoModelForTokenClassification
import re
from unidecode import unidecode
import unicodedata



tokenizer = AutoTokenizer.from_pretrained('camembert-base')

def get_tokens(docs):
  normalized_docs = [unicodedata.normalize('NFKC',doc) for doc in docs]

  outputs = [tokenizer.tokenize(doc) for doc in normalized_docs]

  cleaned_words = clean_outputs(outputs)

  tokens = set_tokens(normalized_docs, cleaned_words)

  return tokens


def clean_outputs(outputs):
  clean_outputs = []

  for output in outputs:
      result = []

      for i in range(len(output)):

          token = output[i]

          if i != 0:
            prev_token = output[i-1]
          else:
            prev_token = ""

          # handle cases where space alone is tokenized so we attached it to the following token
          if prev_token == "▁":
            token = prev_token + token


          try:
              # combine d/l + ' tokens into 1
              if token == "'":
                  result[-1] += token

              # '_' => skip single space and attach it to next token
              elif token == "▁":
                  continue

              # 'est' + '▁' = 'facultatif'
              elif token[0] != ("▁") and token[0].isalpha() and result[-1] == "":
                  result[-1] += token

              # '▁Mar' + 'mit' + 'on' ou '▁pes' + 'to'
              elif token[0] != ("▁") and token[0].isalpha() and result[-1][-1].isalpha():
                  result[-1] += token

              # '▁80' + '0,50'
              elif token[0] != ("▁") and token[0].isnumeric() and result[-1][-1].isnumeric():
                  result[-1] += token

              # '▁800' + ',' + '50'
              elif token[0].isnumeric() and result[-1][-1]in [",", "."] and result[-2][-1].isnumeric() and not token == "▁":
                  result[-2] += result[-1] + token
                  del result[-1]

              # ¼
              elif token in ["/", "⁄"] and prev_token[-1].isnumeric():
                  result[-1] += token
              elif token.isnumeric() and prev_token[-1] in ["/", "⁄"]:
                  result[-1] += token


              # 'c.à.s' OR 'U.K.' BUT '(5g)' or 'rapé)' or 'porc,'
              elif len(token) == 1 and not token.isnumeric() and not prev_token[-1].isnumeric() and len(prev_token.replace("▁", "")) == 1 and token not in ["(", ")", ","]:
                  result[-1] += token

              # '_(5' remove leading parenthese = SOLUTION TO FIND

              else:
                result.append(token)
                # result.append(token.replace("▁", ""))

          except:
              continue

      clean_outputs.append(result)

  return clean_outputs



def set_tokens(docs, cleaned_words):
  results = []

  for i in range(len(docs)):
    doc = docs[i]
    words = cleaned_words[i]
    tokens = []
    offset = 0

    for n in range(len(words)):
      word = words[n]
      clean_word = word.replace("▁", "")
      word_match = doc.find(clean_word)

      if word_match == -1:
        # edge case for fractions '1/2', '1/4'
        fraction = match_fraction(clean_word)
        if fraction is not None:
          word_match = doc.find(fraction)
          if word_match != -1:
            clean_word = fraction

      if word_match != -1:
        word_start = word_match + offset
        word_finish = word_start + len(clean_word)
        doc = doc[(word_finish - offset):]
        if n != (len(words)-1) and words[n+1][0] == ("▁") :
          space = True
        else:
          space = False
        offset = word_finish

        tokens.append({"word": clean_word, "start": word_start, "end": word_finish, "id": n, "space": space})

    results.append(tokens)

  return results


def match_fraction(clean_word):
    # edge case for fractions '1/2', '1/4'
    if clean_word == "1/2":
      return "½"
    if clean_word == "1/3":
      return "⅓"
    if clean_word == "1/4":
      return "¼"
    if clean_word == "1/5":
      return "⅕"
    if clean_word == "3/4":
      return "¾"
    if clean_word == "2/3":
      return "⅔"
    if clean_word == "2/5":
      return "⅖"
  # edge case for fractions '1/2', '1/4'
    if clean_word == "1⁄2":
      return "½"
    if clean_word == "1⁄3":
      return "⅓"
    if clean_word == "1⁄4":
      return "¼"
    if clean_word == "1⁄5":
      return "⅕"
    if clean_word == "3⁄4":
      return "¾"
    if clean_word == "2⁄3":
      return "⅔"
    if clean_word == "2⁄5":
      return "⅖"
    else:
      return None



