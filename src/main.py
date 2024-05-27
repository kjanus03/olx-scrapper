import sys

from PyQt5.QtGui import QFont

from src.Scraping.Scraper import Scraper
from src.Scraping.URLBuilder import URLBuilder
from src.GUI.Controller import Controller
from src.GUI.MainWindow import MainWindow
from src.Resources.utils import load_config
from PyQt5.QtWidgets import QApplication


def create_app(app_title: str, width: int, height: int, fontsize:int, controller: Controller) -> None:
    app = QApplication(sys.argv)

    # Set the global font size to 12
    font = QFont()
    font.setPointSize(fontsize)
    app.setFont(font)
    app.setStyle("Windows")

    main_window = MainWindow(app_title, width, height, controller)
    sys.exit(app.exec_())


def main() -> None:
    config = load_config('Resources/config2.json')

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items)

    # Create the main window
    gui_config = config['gui_config']
    controller = Controller(scraper_instance)
    create_app(gui_config['app_title'], gui_config['width'], gui_config['height'], gui_config['fontsize'], controller)


if __name__ == "__main__":
    main()
