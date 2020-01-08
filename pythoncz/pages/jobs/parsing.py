import re


WHITESPACE_RE = re.compile(r'\s+')


def normalize_text(text):
    if text:
        return WHITESPACE_RE.sub(' ', text.strip())
    return text
