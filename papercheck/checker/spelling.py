# own functions
from papercheck.lib.nlp import *  # language functions
from papercheck.lib.cli import *
from papercheck.pos.posdic import getDict
from papercheck.pos.tags import *
import re
import os
import zipfile
import sys




def addWord(posdic, word, tag):
    if word not in posdic.keys():
        posdic[word] = []
    if tag not in posdic[word]:
        posdic[word].append(tag)





def parse_suffix_char(dic, word, sufc):
    pass


def parse_affix(dic, word, affix):
    addwords = []
    pfxwords = [word]
    prefixes = [c for c in affix if c in "AIUCEFK"]
    suffixes = [c for c in affix if c not in "AIUCEFK"]
    for char in prefixes:
        if char == "A":
            pfxwords.append("re" + word)
        elif char == "I":
            pfxwords.append("in" + word)
        elif char == "U":
            pfxwords.append("un" + word)
        elif char == "C":
            pfxwords.append("de" + word)
        elif char == "E":
            pfxwords.append("dis" + word)
        elif char == "F":
            pfxwords.append("con" + word)
        elif char == "K":
            pfxwords.append("pro" + word)


    for char in suffixes:
        for pfxword in pfxwords:
            if char == "V": 
                newword = re.sub("e$|$", "ive", pfxword)
                addWord(dic, newword, POS_TAG_ADJECTIVE)
            # elif char == "N":
            #     newword = re.sub(
            #             r"(?<!ion)$",
            #             "en",
            #             re.sub("y$", "ication", re.sub("e$", "ion", pfxword)),
            #         )
            #     addWord(dic, newword, POS_TAG_NOUN)
            # elif char == "X":
            #     addwords.append(
            #         re.sub(
            #             r"(?<!ions)$",
            #             "ens",
            #             re.sub("y$", "ications", re.sub("e$", "ions", pfxword)),
            #         )
            #     )
            elif char == "H":
                addwords.append(re.sub(r"y$", "ie", pfxword) + "th")  #
            elif char == "Y":
                addWord(dic, adverb(pfxword), POS_TAG_ADVERB)
            elif char == "G":
                addWord(dic, gerund(pfxword), POS_TAG_VERB)
            elif char == "J":
                addwords.append(re.sub(r"e$", "", pfxword) + "ings")  # gerund
            elif char == "D":
                addwords.append(
                    re.sub(r"e$", "", re.sub(r"(?<=[^aeiou])y$", "i", pfxword))
                    + "ed"
                )  # past
            elif char == "T":
                addwords.append(superlative(pfxword))  # superlative
            elif char == "R":
                addwords.append(
                    re.sub(r"e$", "", re.sub(r"(?<=[^aeiou])y$", "i", pfxword))
                    + "er"
                )
            elif char == "Z":
                addwords.append(
                    re.sub(r"e$", "", re.sub(r"(?<=[^aeiou])y$", "i", pfxword))
                    + "ers"
                )
            elif char == "S":
                addwords.append(plural(pfxword))  # plural
            elif char == "P":
                addwords.append(
                    re.sub(r"(?<=[^aeiou])y$", "i", pfxword) + "ness"
                )  #
            elif char == "M":
                if pfxword[-1] == "s":
                    addwords.append(pfxword + "'")  # noun
                else:
                    addwords.append(pfxword + "'s")  # noun
            elif char == "B":
                addwords.append(
                    re.sub(r"(?<=[^e])e$", "", pfxword) + "able"
                )  # adjective
            elif char == "L":
                addwords.append(pfxword + "ment")  # noun
    # elif char == 'R': addwords.append(comperative(word)) # comparative

    addwords += pfxwords
    return addwords





def read_file_or_zip(filename):
    lines = ""
    try:
        fh = open(filename, "r", encoding="utf8")
        lines = fh.read()
        fh.close()
    except (FileNotFoundError, NotADirectoryError):
        try:
            arch = zipfile.ZipFile(sys.argv[0], "r")
            fh = arch.open(filename, "r")
            lines = fh.read().decode("utf-8")
            fh.close()
        except FileNotFoundError:
            print("ERROR: File '{}' not found.".format(filename))
    return lines


def read_dictionary(dictionary, dictfile):
    text = read_file_or_zip(dictfile)

    for line in text.splitlines():
        if dictfile[-4:] == ".dic":
            word, _, affix = line.strip().partition("/")
            dictionary[word] = ""
            for additional in parse_affix(dictionary, word, affix):
                dictionary[additional] = ""
        else:
            words = line.strip().split(" ")
            for word in words:
                dictionary[word] = ""

    return dictionary


def read_acronyms(acronyms, acronymfile):
    text = read_file_or_zip(acronymfile)

    for line in text.splitlines():
        line = line.strip()
        acronym = re.match(r"\W([A-Z0-9]{2,})", line)
        if acronym != None:
            acronyms[acronym] = ""


class Correction:
    def __init__(self, line, column, match, suggestion, description):
        self.line = line
        self.col = column
        self.match = match
        self.sugg = suggestion
        self.desc = description


# todo: show Capital errors only IF there is a one edit suggestion, otherwise it is probably a name and correct
def check_words(dictionary, text):
    lines = text.splitlines(True)

    word_counter = {}
    corrections = []
    for idx, line in enumerate(lines):
        words = split2words(line)
        for word in words:
            if word.isupper() or isNum(word) or len(re.findall(r"[A-Z]", word)) != 0:
                continue
            isCorrect = word in dictionary
            if not isCorrect:
                if word[0].isupper():
                    lowword = word[0].lower() + word[1:]
                    isCorrect = lowword in dictionary
                if not isCorrect and len(word) > 2:
                    matches = re.findall(r"\W" + word + r"\W", line)
                    match = " " + word + " " if len(matches) == 0 else matches[0]
                    if match[-1] == "-" and word in [
                        "anti",
                        "bio",
                        # "dis",
                        "inter",
                        "intra",
                        # "mis",
                        "multi",
                        "non",
                        "pre",
                        "quasi",
                        "re",
                        "semi",
                        "sub",
                    ]:
                        continue
                    sugg = suggest(dictionary, word)
                    if sugg == "" and word[0].isupper():
                        continue  # do not show capital errors without suggestion
                    if word not in word_counter.keys():
                        word_counter[word] = 0
                    if word_counter[word] < 1:
                        word_counter[word] += 1
                        corrections.append(
                            Correction(
                                idx + 1, 0, match, sugg, "Possibly misspelled word."
                            )
                        )
                        askAction(idx, "Maybe misspelled word.", match, sugg)
                # print("Typo: '{}',  Sugg: {}".format(word, suggest(dictionary, word)))

    return corrections


def edits1(word):
    "All edits that are one edit away from `word`."
    letters = "esianrtolcdugmphbyfvkwz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    capital = [word[0].upper() + word[1:]]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    deletes = [L + R[1:] for L, R in splits if R]
    return list(set(capital + transposes + replaces + inserts + deletes))


def suggest(dictionary, wrong):
    suggs = list(set(w for w in edits1(wrong) if w in dictionary))
    return "" if len(suggs) == 0 else suggs[0]


def checkSpelling(text):

    print(
        "\n\nChecking Spelling:\n----------------------------------------------------"
    )
    print("CWD:", os.getcwd())

    dictionary = {}
    # dictionary = read_dictionary(dictionary, "papercheck/dictionary/en_US.dic")
    # dictionary = read_dictionary(dictionary, "papercheck/dictionary/en-Academic.dic")
    dictionary = getDict()

    read_acronyms(dictionary, "papercheck/dictionary/acronyms.md")
    if dictionary == {}:
        return
    corrections = check_words(dictionary, text)
    return corrections
