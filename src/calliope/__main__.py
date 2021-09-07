from typing import Iterator
from nltk.corpus import brown
import nltk
from docx import Document
from pathlib import Path
import os
import itertools

from nltk.tokenize import sent_tokenize, word_tokenize

import re

alphabets = "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
ellipses = "\.\.\."
punctuation = re.compile("('|\"|!|\.|,|\?|-|/|;|:|”|“)")


def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    if "Ph.D" in text: text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]",
                  "\\1<prd>\\2<prd>\\3<prd>", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>",
                  text)
    text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", text)
    text = re.sub(" " + suffixes + "[.]", " \\1<prd>", text)
    text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
    text = re.sub(ellipses, "<ellipses>", text)
    if "”" in text: text = text.replace("”", "\"")
    if "“" in text: text = text.replace("“", "\"")
    if "\"" in text: text = text.replace(".\"", "\".")
    if "!" in text: text = text.replace("!\"", "\"!")
    if "?" in text: text = text.replace("?\"", "\"?")
    if "-" in text: text = text.replace("-\"", "\"<endhyp>")
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    text = text.replace("<endhyp>", "-<stop>")
    text = text.replace("<ellipses>", "...")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    returned_sentences = []
    for sentence in sentences:
        sentence = sentence.replace("\".", ".\"")
        sentence = sentence.replace("\"!", "!\"")
        sentence = sentence.replace("\"?", "?\"")
        sentence = sentence.replace("\"-", "-\"")
        returned_sentences.append(sentence)
    return returned_sentences


class Collection:

    sentences: list["Sentence"]
    name: str

    def __init__(self, name: str):
        self.name = name
        self.sentences = []

    def add_sentence(self, sentence: "Sentence"):
        self.sentences.append(sentence)

    def add_sentences(self, sentences: list["Sentence"]):
        self.sentences = sentences

    def find_word(self, word: str) -> Iterator["Sentence"]:
        return (sentence for sentence in self.sentences if word in sentence.word_set)

    

    def expand_from_selection(self, range:int) -> list["Sentence"]:
        output = []

        return output

def word_in_set(word: str, word_set: set[str]) -> bool:
    if word in word_set:
        return True
    return False

class Sentence:

    word_set: set[str]
    complexity: int
    index: int

    def __init__(self, literal: str, position: int):
        self.literal = literal
        self.complexity = 1
        self.index = position

        self.build_word_map(self.literal)

    def has_word(self, literal) -> bool:
        try:
            return self.word_map[literal]
        except LookupError:
            return False

    def build_word_map(self, literal):
        words = word_tokenize(literal)
        self.word_set: set[str] = set()
        for word in words:
            if word == ",":
                self.complexity += 1
            if not punctuation.match(word):
                self.word_set.add(word)


def expand_search_terms(collection: Collection, gathered_terms: list[Sentence]):
    print("Expand search terms? (Y/N)")
    term = input()
    if term == "Y":
        while True:
            try:
                term = int(input("Please select a search result to expand from: "))
                if term <= len(gathered_terms) and term > 0:
                    chosen_index = gathered_terms[term - 1].index
                    print(chosen_index)
                    break
                else:
                    print("Please select a valid search result to expand from!")
            except ValueError:
                print("Please enter a valid number!")
        while True:
            try:
                up_range = int(input("Please enter upper range: "))
                if chosen_index + up_range > len(collection.sentences):
                    up_range = len(collection.sentences) - chosen_index
                break
            except ValueError:
                print("Please enter a valid number!")
        while True:
            try:
                low_range = int(input("Please enter a lower range: "))
                if low_range > chosen_index:
                    low_range = chosen_index
                break
            except ValueError:
                print("Please enter a valid number!")
        expanded_results = []
        for i in range (low_range, 0, -1):
            expanded_results.append(collection.sentences[chosen_index - i])
        expanded_results.append(collection.sentences[chosen_index])
        for i in range(1, up_range + 1):
            expanded_results.append(collection.sentences[chosen_index + i])
        
        for sentence in expanded_results:
            print(sentence.literal)


def single_word_search(collection: Collection):
    print("Input search term: ")
    term = input()

    search_terms = collection.find_word(term)
    for i, sentence in enumerate(search_terms):
        print(f"{i + 1}: {sentence.literal}")
    
    expand_search_terms(collection, list(collection.find_word(term)))

resources_path = os.path.join(
    Path(__file__).parent.parent.parent, "resources\\")

book = Document(resources_path + "Familiar, MK II.docx")

text = ""

sentences: list[str] = list(
    itertools.chain.from_iterable(
        split_into_sentences(paragraph.text.strip()) for paragraph in book.paragraphs)
)

familiar = Collection("familiar")


# [foo(x) for x in iterable]
mapped_sentences: list[Sentence] = [
    Sentence(sentence, i) for i, sentence in enumerate(sentences)
]

familiar.add_sentences(mapped_sentences)


term = ""

while term != "EXIT":
    print("Choose an operation: [Single Word Search - SEARCH][Multi Word Search - MULTI][Exit Program - EXIT]")
    term = input()
    if term == "SEARCH":
        single_word_search(familiar)
