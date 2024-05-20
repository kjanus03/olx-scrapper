import asyncio

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
