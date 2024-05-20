import asyncio
from src.ExportManager import ExportFormat, ExportManager

from PyQt5.QtCore import QObject, pyqtSlot


class Controller(QObject):
    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper
        self.loop = asyncio.get_event_loop()

    @pyqtSlot()
    def scrape_data(self):
        result = self.loop.run_until_complete(self.scraper.scrape_data())
        print(result)

    def export_data(self, format):
        export_format = ExportFormat[format.upper()]
        output_config = {'filename': 'scraped_data', 'hyperlinked_columns': ['item_url'], 'format_column_widths': True}
        export_manager = ExportManager(export_format, output_config, self.scraper.data_frames)
        export_manager.export_data()
