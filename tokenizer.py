from transformers import AutoTokenizer, AutoModelForTokenClassification

tokenizer = AutoTokenizer.from_pretrained('camembert-base')

def get_tokens(docs):
  outputs = [tokenizer.tokenize(doc) for doc in docs]

  cleaned_words = clean_outputs(outputs)

  tokens = set_tokens(docs, cleaned_words)

  return tokens


def clean_outputs(outputs):
  clean_outputs = []

  for output in outputs:
      result = []

      for token in output:
          try:
              # combine d/l + ' tokens into 1
              if token == "'":
                  result[-1] += token

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
              elif token[0].isnumeric() and  result[-1][-1]in [",", "."] and result[-2][-1].isnumeric() and not token == "▁":
                  result[-2] += result[-1] + token
                  del result[-1]

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


