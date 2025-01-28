import re


def remove_ansi_escape_codes(lines):
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    return [ansi_escape.sub("", line) for line in lines]
