from spellchecker import SpellChecker
from nltk_utils import tokenize
spell = SpellChecker()

# find those words that may be misspelled

sentence = "Hoow long doez shipping take?"
sentence = sentence.lower()
print("Input: " + sentence)
sentence_array = tokenize(sentence)
misspelled = spell.unknown(sentence_array)

for word in misspelled:
    sentence = sentence.replace(word, spell.correction(word))

if len(misspelled)>0:
    print("Did you mean?: "+sentence)