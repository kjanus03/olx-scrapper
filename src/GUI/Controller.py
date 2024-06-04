import asyncio
from pathlib import Path

import pandas as pd

from src.Scraping.Scraper import Scraper

from src.Exporting.ExportManager import ExportFormat, ExportManager
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from src.GUI.SearchQueriesDialog import SearchQueriesDialog


class Controller(QObject):
    progress_updated = pyqtSignal(int)

    def __init__(self, scraper: Scraper) -> None:
        super().__init__()
        self.scraper = scraper
        self.export_manager = None
        self.loop = asyncio.get_event_loop()

    @pyqtSlot()
    def scrape_data(self) -> None:
        # Ensure progress bar is visible and reset to 0
        self.progress_updated.emit(0)
        self.loop.run_until_complete(self.scrape_and_update_progress())
        self.progress_updated.emit(100)  # Ensure progress is 100% when done

    async def scrape_and_update_progress(self) -> dict[str, pd.DataFrame]:
        await self.scraper.scrape_data(self.progress_updated.emit)
        return self.scraper.data_frames

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
