from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl

from src.formatting import apply_hyperlinking, format_price, format_location_date, format_columns
from urlbuilder import URLBuilder


class Scraper:
    def __init__(self, url_strings: list[URLBuilder] = None):
        self.url_list = url_strings if url_strings else []
        self.data_frames = pd.Series(dtype=object)

    def add_url(self, url: URLBuilder) -> None:
        """Adds a new URL to the list of URLs to be scraped."""
        self.url_list.append(url)

    def scrape_data(self) -> pd.Series:
        """Returns a pandas Series of pandas DataFrames with scraped data from the list of URLs."""
        for url_builder in self.url_list:
            data = self._fetch_data_from_url(url_builder)
            key = self._generate_data_key(url_builder)
            self.data_frames[key] = data

        apply_hyperlinking(self, {"item_url", "photo"})
        return self.data_frames

    def create_spreadsheets(self, filename: str, format_column_widths: bool = True) -> None:
        """Creates an MS Excel file with the scraped DataFrames."""
        with pd.ExcelWriter(f"../{filename}.xlsx") as writer:
            for key, df in self.data_frames.items():
                df.to_excel(writer, sheet_name=key, index=False)

        if format_column_widths:
            self._format_excel_columns(filename)

    def _fetch_data_from_url(self, url_builder: URLBuilder) -> pd.DataFrame:
        """Returns a pandas DataFrame with scraped data from the given URL."""
        site_url = urlparse(url_builder.build_url())
        response = requests.get(site_url.geturl())

        #TODO: Add error handling
        if response.status_code == 200:
            soup = BeautifulSoup.BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("div", {"data-cy": "l-card"})

            return pd.DataFrame(self._process_item(item) for item in items)

    @staticmethod
    def _process_item(item) -> dict:
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

    @staticmethod
    def _generate_data_key(url_builder: URLBuilder) -> str:
        key = f"{url_builder.item_query.capitalize()}"
        if url_builder.city:
            key += f" - {url_builder.city.capitalize()}"
        return key

    @staticmethod
    def _format_excel_columns(filename: str) -> None:
        workbook = openpyxl.load_workbook(f"../{filename}.xlsx")
        for sheet in workbook.worksheets:
            format_columns(sheet)
        workbook.save(f"../{filename}.xlsx")
