import asyncio
from pathlib import Path
from src.Scraping.Scraper import Scraper

from src.Exporting.ExportManager import ExportFormat, ExportManager
from PyQt5.QtCore import QObject, pyqtSlot
from src.GUI.SearchQueriesDialog import SearchQueriesDialog


class Controller(QObject):
    def __init__(self, scraper: Scraper):
        super().__init__()
        self.scraper = scraper
        self.export_manager = None
        self.loop = asyncio.get_event_loop()

    @pyqtSlot()
    def scrape_data(self) -> None:
        """Scrape data from the URLs and create data frames."""
        self.loop.run_until_complete(self.scraper.scrape_data())

    def export_data(self, format: str, directory: str) -> None:
        export_format = ExportFormat[format.upper()]
        output_config = {'filename': str(Path(directory) / 'scraped_data'), 'hyperlinked_columns': ['item_url'],
                         'format_column_widths': True}
        export_manager = ExportManager(export_format, output_config, self.scraper.data_frames)
        export_manager.export_data()

    def view_search_queries(self) -> None:
        dialog = SearchQueriesDialog(config_path='Resources/config2.json')
        dialog.exec_()
        if dialog.result() == dialog.Accepted:
            print("Accepted")
            self.scraper.update_url_list(dialog.config_data)
