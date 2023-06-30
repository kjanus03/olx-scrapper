import datetime
from urllib.parse import urlparse

import bs4 as BeautifulSoup
import pandas as pd
import requests

from src.utils import format_price, format_location_date


def scrap_data(url_string: str) -> pd.DataFrame:
    """Returns a pandas DataFrame with scrapped data from the given url."""
    added_today = []
    df = pd.DataFrame(columns=["title", "price", "location", "date", "url", "photo"])
    url = urlparse(url_string)
    response = requests.get(url.geturl())
    if response.status_code == 200:
        soup = BeautifulSoup.BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", {"data-cy": "l-card"})
        for item in items:
            title = item.find("h6").text.strip()
            price = format_price(item.find("p").text)
            location, date = format_location_date(item.find("p", {"data-testid": "location-date"}).text)
            photo = item.find("img").get("src")
            item_url = "https://www.olx.pl" + item.find("a").get("href")

            new_data = pd.DataFrame(
                {"title": title, "price": price, "location": location, "date": date, "url": item_url, "photo": photo},
                index=[0])
            if date == datetime.datetime.now().strftime("%d %B %Y"):
                added_today.append(new_data)

            df = pd.concat([df, new_data], ignore_index=True)
    return df
