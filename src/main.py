import sys

from PyQt5.QtGui import QFont

from src.Scraping.Scraper import Scraper
from src.Scraping.URLBuilder import URLBuilder
from src.GUI.Controller import Controller
from src.GUI.MainWindow import MainWindow
from src.Resources.utils import load_config
from PyQt5.QtWidgets import QApplication


def create_app(app_title: str, width: int, height: int, fontsize: int, controller: Controller) -> None:
    app = QApplication(sys.argv)

    # import montserrat font from file
    font = QFont()
    font.setFamily("Montserrat")
    font.setPointSize(fontsize)
    app.setFont(font)
    app.setStyle("Windows")

    main_window = MainWindow(app_title, width, height, controller)
    sys.exit(app.exec_())


def main() -> None:
    config = load_config('Resources/config.json')
    gui_config = config['gui_config']

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items, gui_config['page_limit'])

    controller = Controller(scraper_instance)
    create_app(gui_config['app_title'], gui_config['width'], gui_config['height'], gui_config['fontsize'], controller)


if __name__ == "__main__":
    main()
