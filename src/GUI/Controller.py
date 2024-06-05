import asyncio
from pathlib import Path

import pandas as pd

from src.Scraping.Scraper import Scraper

from src.Exporting.ExportManager import ExportFormat, ExportManager
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from src.GUI.SearchQueriesDialog import SearchQueriesDialog


class Controller(QObject):
    """Controller class to handle the communication between the GUI and the Scraper."""

    progress_updated = pyqtSignal(int) # Signa to notify that progress updated
    scraping_done = pyqtSignal()  # Signal to notify when scraping is done
    scraping_failed = pyqtSignal(str)

    def __init__(self, scraper: Scraper, output_config: dict[str]) -> None:
        """
        Initialize the Controller object.
        :param scraper: Scraper object to scrape data
        :param output_config: Configuration for the output file
        """
        super().__init__()
        self.scraper = scraper
        self.loop = asyncio.get_event_loop()
        self.output_config = output_config

    @pyqtSlot()
    def scrape_data(self) -> None:
        """
        Scrape data from the URLs and update the progress bar.
        :return:
        """
        self.progress_updated.emit(0)
        self.loop.run_until_complete(self.scrape_and_update_progress())
        if self.scraping_failed:
            self.progress_updated.emit(0)
        else:
            self.progress_updated.emit(100)

    async def scrape_and_update_progress(self) -> dict[str, pd.DataFrame]:
        """
        Scrape data from the URLs and update the progress bar.
        :return: Data frames of the scraped data
        """
        try:
            await self.scraper.scrape_data(self.progress_updated.emit)
            self.scraping_done.emit()
        except Exception as e:
            self.scraping_failed.emit(str(e))
        return self.scraper.data_frames

    def export_data(self, format: str, directory: str) -> None:
        """
        Export the scraped data to a file.
        :param format: Format of the output file
        :param directory: Directory to save the output file
        :return:
        """
        export_format = ExportFormat[format.upper()]
        if not self.output_config['filename'].startswith(str(Path(directory))):
            self.output_config['filename'] = str(Path(directory) / self.output_config['filename'])

        export_manager = ExportManager(export_format, self.output_config, self.scraper.data_frames)
        export_manager.export_data()

    def view_search_queries(self) -> None:
        """
        Open the dialog to view and view/edit the search queries.
        :return:
        """
        dialog = SearchQueriesDialog(config_path='Resources/config.json')
        dialog.exec_()
        if dialog.result() == dialog.Accepted:
            self.scraper.update_url_list(dialog.config_data)