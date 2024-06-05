import datetime
import locale
import re


def format_price(price: str) -> int:
    """
    Returns price as integer. Removes all non-digit characters.
    :param price: price string
    :return: formatted price
    """
    price = price.replace("do negocjacji", "").strip()
    price = re.sub(r'\D', '', price)
    return int(price) if price else 0


def format_location_date(location_date: str) -> tuple[str, str]:
    """
    Returns location and date from location_date string. Formats date to polish format.
    :param location_date: location and date string
    :return: formatted location and date
    """
    location, date = location_date.split(" - ")[:2]
    if "dzisiaj" in date.lower():
        locale.setlocale(locale.LC_ALL, 'pl_PL')
        formatted_date = datetime.datetime.now().strftime("%d %B %Y")
        date = formatted_date
    return location, date
