import datetime
import locale
import pandas as pd


def format_price(price: str) -> str:
    """Returns price without "do negocjacji"."""
    if "do negocjacji" in price:
        price = price.replace("do negocjacji", "")
    return price


def format_location_date(location_date: str) -> tuple[str, str]:
    """Returns tuple of location and date. Converts date to polish format if it's today."""
    location, date = location_date.split(" - ")
    if "dzisiaj" in date.lower():
        locale.setlocale(locale.LC_ALL, 'pl_PL')
        formatted_date = datetime.datetime.now().strftime("%d %B %Y")
        date = formatted_date
    return location, date


def get_url(item_query: str, city: str = None, distance: int = 100) -> str:
    """Returns a formatted olx url for the given item and city. If city is None, it will search in all cities.
    The distance is set to 100km by default."""
    if city is None:
        city = "oferty"
        distString = ""
    else:
        city = city.replace(" ", "-")
        distString = f"search%5Bdist%5D={distance}&"
    item_query = item_query.replace(" ", "-")
    url = f"https://www.olx.pl/{city}/q-{item_query}/?{distString}search%5Border%5D=created_at%3Adesc"
    return url


def create_hyperlink(url, name):
    """Returns a hyperlink to the given url with the given name."""
    return f'=HYPERLINK("{url}", "{name}")'


def create_spreadsheets(dataFrames: list[pd.DataFrame], sheetNames: list[str]) -> None:
    """Creates an excel file with the given dataFrames and sheetNames."""

    for df in dataFrames:
        df['url'] = df.apply(lambda row: create_hyperlink(row['url'], 'Link'), axis=1)
        df['photo'] = df.apply(lambda row: create_hyperlink(row['photo'], 'Photo'), axis=1)

    with pd.ExcelWriter("../guitars.xlsx") as writer:
        for i, df in enumerate(dataFrames):
            df.to_excel(writer, sheet_name=sheetNames[i], index=False)
