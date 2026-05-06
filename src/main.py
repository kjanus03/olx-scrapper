import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from src.Scraping.Scraper import Scraper
from src.Scraping.URLBuilder import URLBuilder
from src.GUI.Controller import Controller
from src.GUI.MainWindow import MainWindow
from src.Resources.utils import load_config


def create_app(app_title: str, width: int, height: int, fontsize: int, controller: Controller) -> None:
    """Create and run the main application window.

    Theming is applied at the QApplication level inside MainWindow.apply_theme,
    so dialogs inherit the active palette automatically.
    """
    app = QApplication(sys.argv)

    font = QFont()
    font.setFamily("Inter")
    font.setPointSize(fontsize)
    app.setFont(font)

    main_window = MainWindow(app_title, width, height, controller)
    main_window.show()
    sys.exit(app.exec_())


def main() -> None:
    config = load_config('src/Resources/config.json')
    gui_config = config['gui_config']
    output_config = config['output_config']

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items, gui_config['page_limit'])
    controller = Controller(scraper_instance, output_config)

    create_app(
        gui_config['app_title'],
        gui_config['width'],
        gui_config['height'],
        gui_config['fontsize'],
        controller,
    )


if __name__ == "__main__":
    main()
