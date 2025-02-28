"""
Generates fake snippet and user data for testing purposes.
"""

from datetime import datetime, timedelta, timezone
import os
import random
import faker
import requests
import re
import data

fake = faker.Faker()


def _load_franken():
    with open("mock_data/frankenstein.txt") as file:
        global franken, franken_starts
        franken = re.sub("[\r\n]+", " ", file.read()).replace("_", "")
        franken_starts = [0]
        for i in range(len(franken) - 1):
            c = franken[i]
            if c == "." or c == "!" or c == "?":
                franken_starts.append(i + 1)
        file.close()


if not os.path.exists("mock_data"):
    os.mkdir("mock_data")
try:
    _load_franken()
except FileNotFoundError:
    with open("mock_data/frankenstein.txt", "x") as file:
        req = requests.get("https://www.gutenberg.org/cache/epub/84/pg84.txt")
        req.encoding = "UTF8"
        text = req.text
        file.write(text[text.find("You will rejoice") : text.rfind("*** END")])
        file.close()
    _load_franken()


def username():
    return fake.user_name()


def code():
    line_count = random.randint(1, 100)
    lines = []
    indents = 0

    for _ in range(line_count):
        if random.random() < 0.1:
            # Randomly change indentation
            if indents > 0 and random.random() < 0.5 or indents == 4:
                indents -= 1
                lines.append("    " * indents + "}")
            else:
                lines.append("    " * indents + fake.word("verb").capitalize() + "() {")
                indents += 1
        else:
            # Generate text
            lines.append(
                "    " * indents + " ".join(fake.words(random.randint(1, 5))) + ";"
            )

    return "\n".join(lines)


def title():
    words = fake.words(random.randint(0, 2), part_of_speech="adjective")
    words.append(fake.word("noun"))
    return " ".join(words).capitalize()


def paragraph():
    sentence_count = random.randint(1, 5)
    ind_start = random.randint(0, len(franken_starts) - sentence_count - 1)
    char_start = franken_starts[ind_start]
    char_end = franken_starts[ind_start + sentence_count]
    return franken[char_start:char_end].strip()


def tags():
    new_tags = set()
    for _ in range(random.randint(0, 6)):
        if random.random() < 0.2:
            new_tags.add(fake.word("adjective").capitalize())
        else:
            new_tags.add(random.choice(data.preset_tags))
    return list(new_tags)


def time():
    days_ago = random.random() * 365 * 2
    return datetime.now(timezone.utc) + timedelta(-days_ago)
