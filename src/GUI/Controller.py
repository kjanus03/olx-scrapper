import asyncio
from pathlib import Path

from src.Exporting.ExportManager import ExportFormat, ExportManager
from PyQt5.QtCore import QObject, pyqtSlot


class Controller(QObject):
    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper
        self.export_manager = None
        self.loop = asyncio.get_event_loop()

    @pyqtSlot()
    def scrape_data(self) -> None:
        """Scrape data from the URLs and create data frames."""
        result = self.loop.run_until_complete(self.scraper.scrape_data())
        print(result)

    def export_data(self, format, directory):
        export_format = ExportFormat[format.upper()]
        output_config = {
            'filename': str(Path(directory) / 'scraped_data'),
            'hyperlinked_columns': ['item_url'],
            'format_column_widths': True
        }
        export_manager = ExportManager(export_format, output_config, self.scraper.data_frames)
        export_manager.export_data()
