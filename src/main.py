import sys
from typing import Optional

from PyQt5.QtGui import QFont

from src.Scraping.Scraper import Scraper
from src.Scraping.URLBuilder import URLBuilder
from src.GUI.Controller import Controller
from src.GUI.MainWindow import MainWindow
from src.Resources.utils import load_config
from PyQt5.QtWidgets import QApplication


def create_app(app_title: str, width: int, height: int, fontsize: int, dark_mode: bool, controller: Controller, button_style: Optional[str] = None) -> None:
    app = QApplication(sys.argv)

    # import montserrat font from file
    font = QFont()
    font.setFamily("Montserrat")
    font.setPointSize(fontsize)
    app.setFont(font)

    if dark_mode:
        app.setStyleSheet("""
                    QMainWindow, QDialog {
                        background-color: #2e2e2e;
                        color: #f0f0f0;
                    }
                    QLabel, QPushButton, QMenuBar, QMenu, QToolButton, QLineEdit, QTableView, QProgressBar, QCheckBox {
                        background-color: #2e2e2e;
                        color: #f0f0f0;
                    }
                    QPushButton {
                        background-color: #3a3a3a;
                        border: 1px solid #5c5c5c;
                        padding: 5px 10px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #4d4d4d;
                    }
                    QToolButton {
                        background-color: #3a3a3a;
                        border: 1px solid #5c5c5c;
                        padding: 5px 10px;
                        border-radius: 5px;
                    }
                    QToolButton::menu-indicator {
                        image: none;
                    }
                    QTableView {
                        gridline-color: #555555;
                        selection-background-color: #555555;
                        alternate-background-color: #3a3a3a;
                    }
                    QHeaderView::section {
                        background-color: #3a3a3a;
                        color: #f0f0f0;
                        padding: 5px;
                        border: 1px solid #5c5c5c;
                    }
                    QProgressBar {
                        border: 1px solid #3a3a3a;
                        text-align: center;
                        color: #f0f0f0;
                        background-color: #3a3a3a;
                    }
                    QProgressBar::chunk {
                        background-color: #4caf50;
                    }
                    QMenu {
                        background-color: #3a3a3a;
                        border: 1px solid #5c5c5c;
                    }
                    QMenu::item {
                        background-color: transparent;
                        padding: 5px 10px;
                    }
                    QMenu::item:selected {
                        background-color: #4d4d4d;
                    }
                    QMessageBox {
                        background-color: #2e2e2e;
                        color: #f0f0f0;
                    }
                """)
    else:
        app.setStyle("Windows")

    main_window = MainWindow(app_title, width, height, controller, button_style)
    sys.exit(app.exec_())


def main() -> None:
    config = load_config('Resources/config.json')
    gui_config = config['gui_config']
    output_config = config['output_config']
    button_style = """
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:disabled {
                    background-color: #2e2e2e;
                    border: 1px solid #3a3a3a;
                    color: #7a7a7a;
                }
            """

    search_items = [URLBuilder(**query) for query in config['search_queries']]
    scraper_instance = Scraper(search_items, gui_config['page_limit'])

    controller = Controller(scraper_instance, output_config)
    create_app(gui_config['app_title'], gui_config['width'], gui_config['height'], gui_config['fontsize'],
               gui_config['dark_mode'], controller, button_style)


if __name__ == "__main__":
    main()
