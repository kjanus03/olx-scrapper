import asyncio
import json

from scraper import Scraper
from urlbuilder import URLBuilder
from spreadsheet_manager import SpreadsheetManager


def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def main() -> None:
    config = load_config('config.json')

    # Create Scraper instance
    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items)

    # Concurrently scrape data and create data frames
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scraper_instance.scrape_data())

    # Create spreadsheets
    output_config = config['output']
    spreadsheet_manager = SpreadsheetManager(scraper_instance.data_frames, output_config['filename'])
    spreadsheet_manager.initialize_spreadsheets(set(output_config['hyperlinked_columns']),
                                                output_config['format_column_widths'])


if __name__ == "__main__":
    main()
