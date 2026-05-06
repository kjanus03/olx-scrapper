import json
import os
import bs4.element
import pandas as pd
import aiohttp
import asyncio
import re
from datetime import datetime
from typing import Union, Callable, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from src.Exporting.formatting import format_price, format_location_date
from src.Scraping.URLBuilder import URLBuilder


# Heuristics for filtering out accessory/parts listings that show up when
# searching for a product. Real product listings rarely contain any of these
# words in their title; accessory listings nearly always do.
_ACCESSORY_BRANDS = {
    "tech-protect", "techprotect", "spigen", "ringke", "baseus", "ugreen",
    "anker", "belkin", "mophie", "otterbox", "nillkin", "rhinoshield",
    "caseology", "puro", "wozinsky", "bizon", "amazingthing",
}

_ACCESSORY_KEYWORDS = {
    # Polish — cases & covers
    "etui", "pokrowiec", "obudowa", "futerał", "futeral",
    # Polish — glass & film
    "szkło", "szklo", "folia", "hartowane", "hartowana",
    # Polish — cables, chargers, adapters
    "ładowarka", "ladowarka", "kabel", "przewód", "przewod",
    # Polish — holders, mounts, straps
    "uchwyt", "stojak", "podstawka", "pasek",
    # Polish — replacement parts & repair
    "klapka", "klapki", "wymiana", "naprawa", "wyświetlacz", "wyswietlacz",
    "części", "czesci", "część", "czesc", "lcd",
    # English equivalents
    "case", "cover", "sleeve", "wallet",
    "glass", "tempered", "protector", "screen", "film",
    "charger", "cable", "adapter", "holder", "mount", "stand",
    "replacement", "repair", "parts", "flap",
}

_TOKEN_RE = re.compile(r"[\w]+", flags=re.UNICODE)


def _classify_relevance(title: str) -> bool:
    """True if the listing looks like a real product, False if an accessory/part."""
    if not title:
        return False
    t = title.lower()
    if any(brand in t for brand in _ACCESSORY_BRANDS):
        return False
    words = {w.lower() for w in _TOKEN_RE.findall(t)}
    if words & _ACCESSORY_KEYWORDS:
        return False
    return True


class Scraper:
    def __init__(self, url_strings: list[URLBuilder], page_limit: int) -> None:
        """
        Scraper class for scraping data from OLX.
        :param url_strings: List of URLBuilder objects for scraping data.
        :param page_limit: Limit of pages to scrape for each URL.
        """
        self.url_list = url_strings if url_strings else []
        self.page_limit = page_limit
        self.data_frames = dict()
        self.count_pattern = re.compile(r'Znaleźliśmy\s+(?:ponad\s+)?(\d+)\s+ogłosze(?:ń|nie|nia)')
        self.listings_counts = []
        self.resources_dir = os.path.join(os.path.dirname(__file__), '../Resources')
        self.scraping_history = self.load_scraping_history()
        self.last_scrape_date = (
            datetime.fromisoformat(self.scraping_history[-1]['scrape_date'])
            if self.scraping_history else None
        )
        self._seen_urls_file = os.path.join(self.resources_dir, 'seen_listings.json')
        self._seen_urls: dict = self._load_seen_urls()

    def add_url(self, url: URLBuilder) -> None:
        """Adds a URLBuilder object to the list of URLs to scrape."""
        self.url_list.append(url)

    async def scrape_data(self, progress_callback: Callable[[int], None] = None) -> dict[str, pd.DataFrame]:
        """Scrapes data from the URLs asynchronously."""
        self.data_frames = dict()
        num_urls = len(self.url_list)
        if num_urls == 0:
            return self.data_frames

        tasks = []
        for i, url in enumerate(self.url_list):
            tasks.append(self._fetch_data_from_url(url))
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50))
            await asyncio.sleep(0.1)

        data = await asyncio.gather(*tasks)
        current_urls: dict = {}
        for i, result, url_builder in zip(range(len(self.url_list)), data, self.url_list):
            key = url_builder.generate_data_key()
            if not result.empty and "Item URL" in result.columns:
                prev = self._seen_urls.get(key, {})  # {url: price}
                if prev:
                    result["Is New"] = result["Item URL"].apply(
                        lambda url: bool(url) and url not in prev
                    )
                    def _old_price(row, prev=prev):
                        url = row["Item URL"]
                        if not url or url not in prev:
                            return 0
                        old = prev[url]
                        try:
                            cur = int(row["Price"])
                            old = int(old)
                        except (TypeError, ValueError):
                            return 0
                        return old if (old > 0 and cur > 0 and cur < old) else 0
                    result["Old Price"] = result.apply(_old_price, axis=1)
                else:
                    result["Is New"] = False
                    result["Old Price"] = 0
                if "Title" in result.columns:
                    result["Is Match"] = result["Title"].apply(_classify_relevance)
                else:
                    result["Is Match"] = True

                matched_only = result[result["Is Match"] == True]
                filtered_result = self._filter_price_outliers(matched_only)
                result = pd.concat([filtered_result, result[result["Is Match"] == False]])
                
                current_urls[key] = {
                    row["Item URL"]: int(row["Price"])
                    for _, row in result.iterrows()
                    if row.get("Item URL")
                }
            else:
                current_urls[key] = {}
            self.data_frames[key] = result
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50 + 50))
        self._save_seen_urls(current_urls)
        self._seen_urls = current_urls
        self.last_scrape_date = datetime.now()
        self.save_scrape_date()
        return self.data_frames

    async def _fetch_data_from_url(self, url_builder: URLBuilder) -> pd.DataFrame:
        """Fetches data from the given URL."""
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
                            break
                        page += 1
                    else:
                        raise Exception(f"Error: {response.status} for {site_url.geturl()}")

            processed = []
            for item in all_items:
                try:
                    row = self._process_item(item)
                    if row.get("Title"):  # skip rows we couldn't parse a title for
                        processed.append(row)
                except Exception:
                    # Defensive: never let one malformed card kill the whole scrape.
                    continue

            return pd.DataFrame(processed) if processed else pd.DataFrame()


    @staticmethod
    def _safe_text(element) -> str:
        """Return stripped text from a bs4 element, or '' if None."""
        if element is None:
            return ""
        try:
            return element.get_text(strip=True)
        except AttributeError:
            return ""

    @staticmethod
    def _extract_title(item: bs4.element.Tag) -> str:
        """
        Title extraction is the part OLX randomizes the most.
        Try every heading tag; if none, fall back to the anchor's aria-label,
        then the anchor text itself.
        """
        heading = item.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        title = Scraper._safe_text(heading)
        if title:
            return title
        
        anchor = item.find("a")
        if anchor is not None:
            aria = anchor.get("aria-label")
            if aria:
                return aria.strip()

        return Scraper._safe_text(anchor)

    @staticmethod
    def _extract_price(item: bs4.element.Tag) -> int:
        """
        Find a <p> tag whose text looks like a price. We scan all <p> tags
        rather than assume the first one is the price.
        """
        candidates = item.find_all("p")
        for p in candidates:
            txt = Scraper._safe_text(p)
            if not txt:
                continue
            # Price text on OLX usually contains 'zł' or 'do negocjacji' or just digits
            if "zł" in txt.lower() or "negocjacji" in txt.lower() or re.search(r"\d", txt):
                # Skip the location-date paragraph if it sneaks in
                if p.get("data-testid") == "location-date":
                    continue
                try:
                    return format_price(txt)
                except Exception:
                    continue
        return 0

    @staticmethod
    def _extract_location_date(item: bs4.element.Tag) -> tuple[str, str]:
        """Try data-testid first, fall back to scanning <p> tags for a ' - ' separator."""
        loc_date_el = item.find("p", {"data-testid": "location-date"})
        if loc_date_el is None:
            for p in item.find_all("p"):
                txt = Scraper._safe_text(p)
                if " - " in txt and "zł" not in txt.lower():
                    loc_date_el = p
                    break

        if loc_date_el is None:
            return "", ""

        try:
            return format_location_date(loc_date_el.get_text())
        except Exception:
            return "", ""

    @staticmethod
    def _extract_photo(item: bs4.element.Tag) -> str:
        img = item.find("img")
        if img is None:
            return ""
        # Some lazy-loaded variants put the real URL in data-src
        return img.get("src") or img.get("data-src") or ""

    @staticmethod
    def _extract_url(item: bs4.element.Tag) -> str:
        anchor = item.find("a")
        if anchor is None:
            return ""
        href = anchor.get("href", "")
        if not href:
            return ""
        return urljoin("https://www.olx.pl", href)

    @staticmethod
    def _process_item(item: bs4.element.Tag) -> dict:
        """
        Processes an item from the scraped data.
        Each field is extracted defensively so that a single missing element
        does not break the whole row.
        """
        return {
            "Title": Scraper._extract_title(item),
            "Price": Scraper._extract_price(item),
            "Location": Scraper._extract_location_date(item)[0],
            "Date": Scraper._extract_location_date(item)[1],
            "Item URL": Scraper._extract_url(item),
            "Photo": Scraper._extract_photo(item),
        }


    def find_count(self, soup: BeautifulSoup) -> int:
        """
        Finds the number of listings on the page.
        Returns a large number on failure so we don't break out of pagination
        prematurely just because the count element changed.
        """
        try:
            count_element = soup.find("span", {"data-testid": "total-count"})
            if count_element is None:
                return 10**6
            match = self.count_pattern.search(count_element.text)
            if not match:
                return 10**6
            count = int(match.group(1))
            self.listings_counts.append(count)
            return count
        except Exception:
            return 10**6

    def save_scrape_date(self) -> None:
        """Saves the date of the last scrape to the scraping history file."""
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

    def load_scraping_history(self) -> list[dict[str, Union[str, datetime]]]:
        """Loads the scraping history from the scraping history file."""
        try:
            with open(os.path.join(self.resources_dir, 'scraping_history.json'), 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _load_seen_urls(self) -> dict:
        """Returns {key: {url: price}} — migrates the old [url, ...] list format."""
        try:
            with open(self._seen_urls_file, 'r') as f:
                data = json.load(f)
            migrated = {}
            for k, v in data.items():
                # old format was a plain list of URLs with no prices
                migrated[k] = {url: 0 for url in v} if isinstance(v, list) else v
            return migrated
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_seen_urls(self, current: dict) -> None:
        try:
            with open(self._seen_urls_file, 'w') as f:
                json.dump(current, f)
        except Exception:
            pass

    def update_url_list(self, config: dict) -> None:
        """Updates the URL list with the given configuration."""
        self.url_list = [URLBuilder(**query) for query in config['search_queries']]

    @staticmethod
    def _filter_price_outliers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Uses the Interquartile Range (IQR) to drop extreme outliers (e.g., 35zł pumps 
        or fake 9,999,999zł listings) before they ruin median calculations.
        """
        if df.empty or len(df) < 5 or "Price" not in df.columns: 
            return df
            
        prices = pd.to_numeric(df['Price'], errors='coerce').dropna()
        
        if len(prices) < 5:
            return df

        Q1 = prices.quantile(0.25)
        Q3 = prices.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        return df[(df['Price'] >= lower_bound) & (df['Price'] <= upper_bound)]