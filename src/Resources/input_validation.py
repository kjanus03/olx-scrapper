import re


def validate_filename(filename: str):
    if not re.match(r'^[a-zA-Z0-9_]+$', filename):
        raise ValueError("Filename must only contain letters, numbers, and underscores.")
    return filename


def validate_page_limit(page_limit: int):
    if not (1 <= page_limit <= 10):
        raise ValueError("Page limit must be between 1 and 10.")
    return page_limit


def validate_dimension(value: int):
    if not (100 <= value <= 3000):
        raise ValueError("Width and height must be between 100 and 3000.")
    return value


def validate_fontsize(value: int):
    if not (8 <= value <= 24):
        raise ValueError("Font size must be between 8 and 24.")
    return value
