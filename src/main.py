import asyncio
import json
import sys

from scraper import Scraper
from urlbuilder import URLBuilder
from ExportManager import ExportFormat, ExportManager
from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def create_app(app_title: str, width: int, height: int) -> None:
    app = QApplication(sys.argv)
    main_window = MainWindow(app_title, width, height)
    sys.exit(app.exec_())


def main() -> None:
    config = load_config('config2.json')

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items)

    # Concurrently scrape data and create data frames
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scraper_instance.scrape_data())

    # Create spreadsheets
    export_format = ExportFormat.EXCEL
    export_manager = ExportManager(export_format, config['output'], scraper_instance.data_frames)
    export_manager.export_data()

    # Create the main window
    gui_config = config['gui_config']
    create_app(gui_config['app_title'], gui_config['width'], gui_config['height'])


if __name__ == "__main__":
    main()
