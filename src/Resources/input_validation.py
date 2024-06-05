import re


def validate_filename(filename: str) -> str:
    """
    Validate the filename to ensure it only contains letters, numbers, and underscores.
    :param filename: Filename to validate.
    :return: Validated filename.
    """
    if not re.match(r'^[a-zA-Z0-9_]+$', filename):
        raise ValueError("Filename must only contain letters, numbers, and underscores.")
    return filename


def validate_page_limit(page_limit: int) -> int:
    """
    Validate the page limit to ensure it is between 1 and 10.
    :param page_limit: Page limit to validate.
    :return: Validated page limit.
    """
    if not (1 <= page_limit <= 10):
        raise ValueError("Page limit must be between 1 and 10.")
    return page_limit


def validate_dimension(value: int) -> int:
    """
    Validate the width and height to ensure they are between 100 and 3000.
    :param value: Dimension to validate.
    :return: Validated dimension.
    """
    if not (100 <= value <= 3000):
        raise ValueError("Width and height must be between 100 and 3000.")
    return value


def validate_fontsize(value: int) -> int:
    """
    Validate the font size to ensure it is between 8 and 24.
    :param value: Font size to validate.
    :return: Validated font size.
    """
    if not (8 <= value <= 24):
        raise ValueError("Font size must be between 8 and 24.")
    return value
