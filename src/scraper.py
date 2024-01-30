from urllib.parse import urlparse, urljoin

import bs4.element
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp
import asyncio

from src.formatting import format_price, format_location_date
from urlbuilder import URLBuilder


class Scraper:
    def __init__(self, url_strings: list[URLBuilder] = None):
        self.url_list = url_strings if url_strings else []
        self.data_frames = pd.Series(dtype=object)

    def add_url(self, url: URLBuilder) -> None:
        """Adds a new URL to the list of URLs to be scraped."""
        self.url_list.append(url)

    async def scrape_data(self) -> pd.Series:
        """Returns a pandas Series of pandas DataFrames with scraped data from the list of URLs."""
        tasks = [self._fetch_data_from_url(url_builder) for url_builder in self.url_list]
        # the data is returned in the same order as the tasks
        data = await asyncio.gather(*tasks)

        for result, url_builder in zip(data, self.url_list):
            key = url_builder.generate_data_key()
            self.data_frames[key] = result

        return self.data_frames

    async def _fetch_data_from_url(self, url_builder: URLBuilder) -> pd.DataFrame:
        """Returns a pandas DataFrame with scraped data from the given URL asynchronously."""
        async with aiohttp.ClientSession() as session:
            site_url = urlparse(url_builder.build_url())
            async with session.get(site_url.geturl()) as response:
                # TODO: Handle errors
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    items = soup.find_all("div", {"data-cy": "l-card"})
                    print(type(items[0]))
                    return pd.DataFrame(self._process_item(item) for item in items)
                else:
                    print(f"Error: {response.status} for {site_url.geturl()}")
                    return pd.DataFrame()

    @staticmethod
    def _process_item(item: bs4.element.Tag) -> dict:
        """Returns a dictionary with the processed data from the given item."""
        title = item.find("h6").text.strip()
        price = format_price(item.find("p").text)
        location, date = format_location_date(item.find("p", {"data-testid": "location-date"}).text)
        photo = item.find("img").get("src")
        item_url = urljoin("https://www.olx.pl", item.find("a").get("href"))

        return {
            "title": title, "price": price, "location": location, "date": date,
            "item_url": item_url, "photo": photo
        }