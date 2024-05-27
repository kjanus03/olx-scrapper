from __future__ import annotations

import datetime
import locale
import re


def format_price(price: str) -> int:
    """Returns price as an integer after cleaning the string."""
    price = price.replace("do negocjacji", "").strip()
    price = re.sub(r'[^\d]', '', price)
    return int(price) if price else 0


def format_location_date(location_date: str) -> tuple[str, str]:
    """Returns tuple of location and date. Converts date to Polish format if it's today."""
    location, date = location_date.split(" - ")[:2]
    if "dzisiaj" in date.lower():
        locale.setlocale(locale.LC_ALL, 'pl_PL')
        formatted_date = datetime.datetime.now().strftime("%d %B %Y")
        date = formatted_date
    return location, date

