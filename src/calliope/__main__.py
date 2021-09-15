from typing import Iterator, final
from nltk import metrics
from nltk.corpus import brown
import nltk
from docx import Document, opc
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
    word_count: dict[str, int]

    def __init__(self, name: str):
        self.name = name
        self.sentences = []
        self.word_count = {}

    def add_sentence(self, sentence: "Sentence"):
        self.sentences.append(sentence)
        for word in word_tokenize(sentence.literal):
            if not punctuation.match(word):
                if word not in self.word_count.keys():
                    self.word_count[word] = 1
                else:
                    self.word_count[word] += 1

    def add_sentences(self, sentences: list["Sentence"]):
        self.sentences = sentences

    def find_word(self, word: str) -> Iterator["Sentence"]:
        return (sentence for sentence in self.sentences
                if word in sentence.word_set)

    def expand_from_selection(self, range: int) -> list["Sentence"]:
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
    adj_count: int
    verb_count: int

    def __init__(self, literal: str, position: int):
        self.literal = literal
        self.complexity = 1
        self.index = position
        self.adj_count = 0
        self.verb_count = 0

        self.build_word_map(self.literal)

    def has_word(self, literal) -> bool:
        return literal in self.word_set

    def has_any_term(self, terms: list[str]) -> bool:
        for term in terms:
            if self.has_word(term):
                return True
        return False

    def build_word_map(self, literal):
        words = word_tokenize(literal)
        self.word_set: set[str] = set()
        for word in words:
            if word == ",":
                self.complexity += 1
            if not punctuation.match(word):
                self.word_set.add(word)
                pos_tagged = nltk.pos_tag(word)
                if pos_tagged[1] == "JJ" or pos_tagged[
                        1] == "JJR" or pos_tagged[1] == "JJS" or pos_tagged[
                            1] == "RB" or pos_tagged[1] == "RBR" or pos_tagged[
                                1] == "RBS":
                    self.adj_count += 1
                if pos_tagged[1] == "VB" or pos_tagged[
                        1] == "VBG" or pos_tagged[1] == "VBD" or pos_tagged[
                            1] == "VBN" or pos_tagged[
                                1] == "VBP" or pos_tagged[1] == "VBZ":
                    self.verb_count += 1


def expand_search_terms(collection: Collection,
                        gathered_terms: list[Sentence]):
    print("Expand search terms? (Y/N)")
    term = input()
    if term == "Y":
        while True:
            try:
                term = int(
                    input("Please select a search result to expand from: "))
                if term <= len(gathered_terms) and term > 0:
                    chosen_index = gathered_terms[term - 1].index
                    break
                else:
                    print(
                        "Please select a valid search result to expand from!")
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
        for i in range(low_range, 0, -1):
            expanded_results.append(collection.sentences[chosen_index - i])
        expanded_results.append(collection.sentences[chosen_index])
        for i in range(1, up_range + 1):
            expanded_results.append(collection.sentences[chosen_index + i])

        for sentence in expanded_results:
            print(sentence.literal)


def frustrate_map(satisfaction_map: dict[str, bool]) -> dict[str, bool]:
    for term in satisfaction_map.keys():
        if satisfaction_map[term] == True:
            satisfaction_map[term] == False
    return satisfaction_map


def map_satisfied(satisfaction_map: dict[str, bool]) -> bool:
    for term in satisfaction_map.keys():
        if satisfaction_map[term] == True:
            continue
        else:
            return False
    return True


def single_word_search(collection: Collection):
    print("Input search term: ")
    term = input()

    search_terms = collection.find_word(term)
    for i, sentence in enumerate(search_terms):
        print(f"{i + 1}: {sentence.literal}")

    expand_search_terms(collection, list(collection.find_word(term)))


def multi_word_search(collection: Collection):
    terms = input("Enter all search terms separated by a space: ").split()

    satisfaction_map = {term: False for term in terms}

    while True:
        try:
            search_range = int(input("Enter search range: "))
            break
        except ValueError:
            print("Please input a valid range!")

    print("Beginning search with terms: ")
    for term in satisfaction_map.keys():
        print(term)
    input(f"Within range {search_range}")

    satisfactory_sets = []
    for term in satisfaction_map.keys():
        potential_matches = list(collection.find_word(term))
        for sentence in potential_matches:
            satisfaction_map[term] = True
            upper_distance = search_range
            lower_distance = search_range
            lower_sentences = []
            upper_sentences = []
            sweeping_include = False
            if lower_distance > sentence.index:
                lower_distance = sentence.index
            if upper_distance + sentence.index > len(collection.sentences):
                upper_distance = len(collection.sentences) - sentence.index
            while lower_distance > 0:
                if collection.sentences[
                        sentence.index - lower_distance].has_any_term(
                            list(satisfaction_map.keys())) or sweeping_include:
                    lower_sentences.append(
                        collection.sentences[sentence.index - lower_distance])
                    for subterm in satisfaction_map.keys():
                        if collection.sentences[sentence.index -
                                                lower_distance].has_word(
                                                    subterm):
                            if not satisfaction_map[subterm]:
                                satisfaction_map[subterm] = True

                    sweeping_include = True
                lower_distance -= 1
            sweeping_include = False
            while upper_distance > 0:
                if collection.sentences[
                        sentence.index + upper_distance].has_any_term(
                            list(satisfaction_map.keys())) or sweeping_include:
                    upper_sentences.append(
                        collection.sentences[sentence.index + upper_distance])
                    for subterm in satisfaction_map.keys():
                        if collection.sentences[sentence.index +
                                                upper_distance].has_word(
                                                    subterm):
                            if not satisfaction_map[subterm]:

                                satisfaction_map[subterm] = True
                    sweeping_include = True
                upper_distance -= 1
            upper_sentences.reverse()

            if map_satisfied(satisfaction_map):
                final_set = lower_sentences
                final_set.append(sentence)
                final_set.extend(upper_sentences)
                satisfactory_sets.append(final_set)

            for term in satisfaction_map.keys():
                satisfaction_map[term] = False

    for i, s_set in enumerate(satisfactory_sets):
        if not subsumed_set(satisfactory_sets, i):
            print(f"Printing set {i}:")
            for sentence in s_set:
                print(sentence.literal)


def display_complexity(collection: Collection):
    complexity_count: dict[int, int] = {}
    total_complexity = 0
    for sentence in collection.sentences:
        if sentence.complexity in complexity_count.keys():
            complexity_count[sentence.complexity] += 1
        else:
            complexity_count[sentence.complexity] = 1
        total_complexity += sentence.complexity
    average_complexity = "{:.2f}".format(total_complexity /
                                         len(collection.sentences))
    print(
        f"Average complexity for Collection {collection.name}: {average_complexity}"
    )

    sorted_complexity = [key for key in complexity_count.keys()]

    sorted_complexity.sort()
    for complexity in sorted_complexity:
        print(
            f"Complexity {complexity} sentences: {complexity_count[complexity]}"
        )

def display_dynamics(collection: Collection):
    pass

def display_descriptive(collection: Collection):
    pass

def display_word_saturation(collection: Collection):
    pass

def get_metrics(collection: Collection):
    metric_type = ""
    while metric_type != "EXIT":
        metric_type = input(
            f"Input the type of metrics you would like to view for Collection {collection.name}:\n" + 
            "[Average Complexity - COMP][Dynamic Writing - DYNA][Descriptive Writing - DESC][Word Saturation - WORD][Exit to menu - EXIT]\n"
        )
        if metric_type == "COMP":
            display_complexity(collection)
        if metric_type == "DYNA":
            display_dynamics(collection)
        if metric_type == "DESC":
            display_dynamics(collection)
        if metric_type == "WORD":
            display_word_saturation(collection)


def subsumed_set(set_of_sets: list[list[Sentence]],
                 compared_index: int) -> bool:

    for sentence in set_of_sets[compared_index]:
        if compared_index > 0:
            if sentence in set_of_sets[compared_index - 1]:
                continue
            else:
                return False
        elif compared_index < len(set_of_sets) - 1:
            if sentence in set_of_sets[compared_index + 1]:
                continue
            else:
                return False
    return True


resources_path = os.path.join(
    Path(__file__).parent.parent.parent, "resources\\")

book_title = ""
while book_title != "EXIT":
    book_title = input(
        "Enter the name of a .txt or .docx file in the resources directory. Enter EXIT to exit.\n"
    )
    try:
        book = Document(resources_path + book_title)
        break
    except opc.exceptions.PackageNotFoundError:
        print("No such file found! Please try again.")
if book_title == "EXIT":
    exit()
text = ""

sentences: list[str] = list(
    itertools.chain.from_iterable(
        split_into_sentences(paragraph.text.strip())
        for paragraph in book.paragraphs))

collection_name = input("Please input a name for this collection.\n")

collection = Collection(collection_name)

# [foo(x) for x in iterable]
mapped_sentences: list[Sentence] = [
    Sentence(sentence, i) for i, sentence in enumerate(sentences)
]

collection.add_sentences(mapped_sentences)

term = ""

while term != "EXIT":
    term = input(
        "Choose an operation: [Single Word Search - SEARCH][Multi Word Search - MULTI][Get Metrics - METRIC][Exit Program - EXIT]\n"
    )
    if term == "SEARCH":
        single_word_search(collection)
    if term == "MULTI":
        multi_word_search(collection)
    if term == "METRIC":
        get_metrics(collection)
