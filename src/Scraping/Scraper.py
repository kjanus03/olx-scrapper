import json
import os
from datetime import datetime
from typing import Union
from urllib.parse import urlparse, urljoin

import bs4.element
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp
import asyncio
import re

from src.Exporting.formatting import format_price, format_location_date
from src.Scraping.URLBuilder import URLBuilder


class Scraper:
    def __init__(self, url_strings: list[URLBuilder] = None):
        self.url_list = url_strings if url_strings else []
        self.data_frames = dict()
        self.count_pattern = re.compile(r'Znaleźliśmy\s+(?:ponad\s+)?(\d+)\s+ogłosze(?:ń|nie|nia)')
        self.listings_counts = []
        self.resources_dir = os.path.join(os.path.dirname(__file__), '../Resources')
        self.last_scrape_date = self.load_last_scrape_date()

    def add_url(self, url: URLBuilder) -> None:
        """Adds a new URL to the list of URLs to be scraped."""
        self.url_list.append(url)

    async def scrape_data(self) -> dict[str, pd.DataFrame]:
        self.data_frames = dict()
        """Returns a dictionary of pandas DataFrames with scraped data from the list of URLs."""
        tasks = [self._fetch_data_from_url(url_builder) for url_builder in self.url_list]

        data = await asyncio.gather(*tasks)
        for result, url_builder in zip(data, self.url_list):
            key = url_builder.generate_data_key()
            self.data_frames[key] = result
            # print data type of each column of result
        self.last_scrape_date = datetime.now()
        self.save_last_scrape_date()
        print("scraped data")
        return self.data_frames

    async def _fetch_data_from_url(self, url_builder: URLBuilder) -> pd.DataFrame:
        """Returns a pandas DataFrame with scraped data from the given URL asynchronously."""
        async with aiohttp.ClientSession() as session:
            site_url = urlparse(url_builder.build_url())
            async with session.get(site_url.geturl()) as response:
                # TODO: Handle errors
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "html.parser")

                    # Find the number of listings, if it's 0 we don't want to scrape the default OLX page
                    count = self.find_count(soup)
                    items = soup.find_all("div", {"data-cy": "l-card"})[:count]
                    return pd.DataFrame(self._process_item(item) for item in items) if count != 0 else pd.DataFrame()
                else:
                    print(f"Error: {response.status} for {site_url.geturl()}")
                    return pd.DataFrame()

    @staticmethod
    def _process_item(item: bs4.element.Tag) -> dict:
        """Returns a dictionary with the processed data from the given item."""
        title = item.find("h6").text.strip()
        price = format_price(item.find("p").text)
        location, date = format_location_date(item.find("p", {"data-testid": "location-date"}).text) if item.find(
            "p", {"data-testid": "location-date"}) else ("", "")
        photo = item.find("img").get("src") if item.find("img") else ""
        item_url = urljoin("https://www.olx.pl", item.find("a").get("href"))

        return {"title": title, "price": price, "location": location, "date": date, "item_url": item_url,
                "photo": photo}

    def find_count(self, soup: BeautifulSoup) -> int:
        """Returns the number of listings found on the page."""
        count_element = soup.find("span", {"data-testid": "total-count"})
        count = int(self.count_pattern.search(count_element.text).group(1))
        self.listings_counts.append(count)
        return count

    def save_last_scrape_date(self) -> None:
        with open(os.path.join(self.resources_dir, 'last_scrape.json'), 'w') as file:
            json.dump({'last_scrape_date': self.last_scrape_date.isoformat()}, file)

    def load_last_scrape_date(self) -> Union[datetime, None]:
        try:
            with open(os.path.join(self.resources_dir, 'last_scrape.json'), 'r') as file:
                data = json.load(file)
                self.last_scrape_date = datetime.fromisoformat(data['last_scrape_date'])
                return datetime.fromisoformat(data['last_scrape_date'])
        except (FileNotFoundError, KeyError, ValueError):
            return None

    def update_url_list(self, config: dict) -> None:
        self.url_list = [URLBuilder(**query) for query in config['search_queries']]
