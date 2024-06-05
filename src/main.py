import sys

from PyQt5.QtGui import QFont

from src.Scraping.Scraper import Scraper
from src.Scraping.URLBuilder import URLBuilder
from src.GUI.Controller import Controller
from src.GUI.MainWindow import MainWindow
from src.Resources.utils import load_config
from PyQt5.QtWidgets import QApplication


def create_app(app_title: str, width: int, height: int, fontsize: int, dark_mode: bool, controller: Controller) -> None:
    """
    Create the main application window
    :param app_title: Application title
    :param width: Width of the window
    :param height: Height of the window
    :param fontsize: Font size of the application
    :param dark_mode: If True, the application will use a dark theme
    :param controller: Controller object that connects the GUI with the backend Scraper
    :return:
    """
    app = QApplication(sys.argv)

    # import montserrat font from file
    font = QFont()
    font.setFamily("Montserrat")
    font.setPointSize(fontsize)
    app.setFont(font)

    if dark_mode:
        with open('GUI/stylesheets/app_stylesheet.qss') as stylesheet:
            app.setStyleSheet(stylesheet.read())
    else:
        app.setStyle("Windows")

    main_window = MainWindow(app_title, width, height, controller)
    sys.exit(app.exec_())


def main() -> None:
    """
    Main function that initializes the application
    :return:
    """
    config = load_config('Resources/config.json')
    gui_config = config['gui_config']
    output_config = config['output_config']

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items, gui_config['page_limit'])
    controller = Controller(scraper_instance, output_config)

    create_app(gui_config['app_title'], gui_config['width'], gui_config['height'], gui_config['fontsize'],
               gui_config['dark_mode'], controller)


if __name__ == "__main__":
    main()
