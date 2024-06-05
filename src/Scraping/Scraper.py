import json
import os
from datetime import datetime
from typing import Union, Callable
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
    def __init__(self, url_strings: list[URLBuilder], page_limit: int) -> None:
        self.url_list = url_strings if url_strings else []
        self.page_limit = page_limit
        self.data_frames = dict()
        self.count_pattern = re.compile(r'Znaleźliśmy\s+(?:ponad\s+)?(\d+)\s+ogłosze(?:ń|nie|nia)')
        self.listings_counts = []
        self.resources_dir = os.path.join(os.path.dirname(__file__), '../Resources')
        self.scraping_history = self.load_scraping_history()
        self.last_scrape_date = datetime.fromisoformat(self.scraping_history[-1]['scrape_date']) if self.scraping_history else None

    def add_url(self, url: URLBuilder) -> None:
        """Adds a new URL to the list of URLs to be scraped."""
        self.url_list.append(url)

    async def scrape_data(self, progress_callback: Callable[[int], None] = None) -> dict[str, pd.DataFrame]:
        """Returns a dictionary of pandas DataFrames with scraped data from the list of URLs."""
        self.data_frames = dict()
        num_urls = len(self.url_list)
        tasks = []
        for i, url in enumerate(self.url_list):
            tasks.append(self._fetch_data_from_url(url))
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50))
            await asyncio.sleep(0.1)  # Small delay to allow UI update

        data = await asyncio.gather(*tasks)
        for i, result, url_builder in zip(range(len(self.url_list)), data, self.url_list):
            key = url_builder.generate_data_key()
            self.data_frames[key] = result
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50 + 50))
        self.last_scrape_date = datetime.now()
        self.save_scrape_date()
        return self.data_frames

    async def _fetch_data_from_url(self, url_builder: URLBuilder) -> pd.DataFrame:
        """Returns a pandas DataFrame with scraped data from the given URL asynchronously."""
        async with aiohttp.ClientSession() as session:
            all_items = []
            page = 1
            while True:
                site_url = urlparse(url_builder.build_url(page))
                async with session.get(site_url.geturl()) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), "html.parser")
                        items = soup.find_all("div", {"data-cy": "l-card"})
                        all_items.extend(items)
                        count = self.find_count(soup)

                        if page >= self.page_limit or len(all_items) >= count:
                            break  # Break if there are no more pages
                        page += 1
                    else:
                        raise Exception(f"Error: {response.status} for {site_url.geturl()}")

            return pd.DataFrame(self._process_item(item) for item in all_items) if all_items else pd.DataFrame()

    @staticmethod
    def _process_item(item: bs4.element.Tag) -> dict:
        """Returns a dictionary with the processed data from the given item."""
        title = item.find("h6").text.strip()
        price = format_price(item.find("p").text)
        location, date = format_location_date(item.find("p", {"data-testid": "location-date"}).text) if item.find("p",
            {"data-testid": "location-date"}) else ("", "")
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

    def save_scrape_date(self) -> None:
        history_file_path = os.path.join(self.resources_dir, 'scraping_history.json')
        scraping_entry = {'scrape_date': self.last_scrape_date.isoformat()}

        try:
            with open(history_file_path, 'r+') as file:
                history = json.load(file)
                history.append(scraping_entry)
                file.seek(0)
                json.dump(history, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(history_file_path, 'w') as file:
                json.dump([scraping_entry], file, indent=4)

    def load_scraping_history(self) -> list:
        try:
            with open(os.path.join(self.resources_dir, 'scraping_history.json'), 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def update_url_list(self, config: dict) -> None:
        self.url_list = [URLBuilder(**query) for query in config['search_queries']]
