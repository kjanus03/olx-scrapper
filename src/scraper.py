from urllib.parse import urlparse, urljoin
from urlbuilder import URLBuilder
import bs4 as BeautifulSoup
import pandas as pd
import openpyxl
import requests
import datetime

from src.formatting import apply_hyperlinking, format_price, format_location_date, format_columns


class Scraper:
    def __init__(self, url_strings: list[URLBuilder] = None):
        self.url_list = url_strings if url_strings else []
        self.data_frames = pd.Series(dtype=object)

    def add_url(self, url: URLBuilder) -> None:
        """Adds a new URL to the list of URLs to be scraped."""
        self.url_list.append(url)

    def scrap_data(self) -> pd.Series:
        """Returns a pandas Series of pandas DataFrames with scrapped data from the list of URLs."""

        for url_builder in self.url_list:

            site_url = urlparse(url_builder.build_url())
            response = requests.get(site_url.geturl())

            if response.status_code == 200:
                soup = BeautifulSoup.BeautifulSoup(response.text, "html.parser")
                added_today = []
                items = soup.find_all("div", {"data-cy": "l-card"})
                df = pd.DataFrame(columns=["title", "price", "location", "date", "item_url", "photo"])

                for item in items:
                    title = item.find("h6").text.strip()
                    price = format_price(item.find("p").text)
                    location, date = format_location_date(item.find("p", {"data-testid": "location-date"}).text)
                    photo = item.find("img").get("src")
                    item_url = urljoin("https://www.olx.pl", item.find("a").get("href"))

                    new_data = pd.DataFrame(
                        {"title": title, "price": price, "location": location, "date": date, "item_url": item_url,
                         "photo": photo}, index=[0])

                    if date == datetime.datetime.now().strftime("%d %B %Y"):
                        added_today.append(new_data)
                    df = pd.concat([df, new_data], ignore_index=True)

                key = f"{url_builder.item_query.capitalize()} - {url_builder.city.capitalize()}" if url_builder.city else url_builder.item_query.capitalize()
                self.data_frames[key] = df

        apply_hyperlinking(self, ["item_url", "photo"])
        return self.data_frames

    def create_spreadsheets(self, filename: str, format_column_widths: bool = True) -> None:
        """Creates an MS Excel file with the scrapped dataFrames and filename."""

        with pd.ExcelWriter(f"../{filename}.xlsx") as writer:
            for key, df in self.data_frames.items():
                df.to_excel(writer, sheet_name=key, index=False)

        # formatting column widths
        if format_column_widths:
            workbook = openpyxl.load_workbook(f"../{filename}.xlsx")
            for sheet in workbook.worksheets:
                print(type(sheet))
                format_columns(sheet)
            workbook.save(f"../{filename}.xlsx")