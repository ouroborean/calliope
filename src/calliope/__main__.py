from nltk.corpus import brown
import nltk
from docx import Document
from pathlib import Path
import os

from nltk.tokenize import sent_tokenize

import re

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace("”","\"")
    if "“" in text: text = text.replace("“", "\"")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    if "-" in text: text = text.replace("-\"","\"<endhyp>")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    text = text.replace("<endhyp>", "-<stop>")
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

class Sentence:
    def __init__(self, literal:str):
        self.literal = literal
    

resources_path = os.path.join(Path(__file__).parent.parent.parent, "resources\\")


book = Document(resources_path + "Familiar, MK II.docx")

text = ""

sentences = []

for paragraph in book.paragraphs:
    text = paragraph.text.strip()
    sentences += split_into_sentences(text)

for i in range(300):
    print(sentences[i])

