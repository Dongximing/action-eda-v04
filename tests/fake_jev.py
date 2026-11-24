"""Fake Jev adapters for tests (not a model)."""


def good(context, question, options):
    letters = [l for l, _ in options]
    # prefer "C"/"Z"/last option (= neither / none), mimicking an uninformative judge
    return {l: (0.7 if l == letters[-1] else 0.3 / (len(letters) - 1)) for l in letters}


def letter_only(context, question, options):
    return options[0][0]


def bad_letter(context, question, options):
    return "Q"


def not_ready(context, question, options):
    raise NotImplementedError("adapter not filled in")
