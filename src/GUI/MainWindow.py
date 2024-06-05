import sys

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QPushButton, QVBoxLayout, QWidget, QStackedLayout, QHBoxLayout, \
    QLabel, QDialog, QTableView, QProgressBar, QMenu, QToolButton, QMessageBox, QLayout
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QPoint, QModelIndex, QProcess
from src.GUI.DataFrameModel import DataFrameModel
from src.GUI.Controller import Controller
from src.GUI.ClickableDelegate import ClickableDelegate
from src.GUI.ExportDialog import ExportDialog
from src.GUI.ImageDialog import ImageDialog
from src.GUI.SettingsDialog import SettingsDialog
from src.GUI.ScrapingHistoryDialog import ScrapingHistoryDialog
import requests


def reboot_application() -> None:
    """
    Reboots the application.
    :return:
    """
    qApp.quit()
    QProcess.startDetached(sys.executable, sys.argv)


class MainWindow(QMainWindow):
    """Main window of the application."""
    def __init__(self, title: str, width: int, height: int, controller: Controller) -> None:
        """
        Initializes the main window.
        :param title: Title of the window.
        :param width: Width of the window.
        :param height: Height of the window.
        :param controller: Controller object, connecting the GUI to the backend Scraper.
        """
        super().__init__()
        self.controller = controller
        self.controller.progress_updated.connect(self.update_progress_bar)
        self.controller.scraping_done.connect(self.update_last_scrape_label)
        self.controller.scraping_done.connect(self.enable_buttons)
        self.controller.scraping_failed.connect(self.show_scraping_error)
        self.settings_dialog = SettingsDialog(config_path='Resources/config.json')
        self.init_ui(title, width, height)

    def init_ui(self, title: str, width: int, height: int) -> None:
        """
        Initializes the user interface.
        :param title: Title of the window.
        :param width: Width of the window.
        :param height: Height of the window.
        :return:
        """
        self.setup_menu()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.last_scrape_label = QLabel(self)
        self.update_last_scrape_label()

        self.button_layout = QVBoxLayout()
        main_layout.addLayout(self.button_layout)

        self.setup_buttons()

        self.menu_button = self.create_menu_button()
        self.button_layout.addWidget(self.menu_button)

        self.stacked_layout = QStackedLayout()
        main_layout.addLayout(self.stacked_layout)

        self.setup_progress_bar(main_layout)

        self.setGeometry(100, 100, width, height)
        self.set_button_styles()
        if self.settings_dialog.dark_mode_toggle.isChecked():
            self.apply_dark_mode()
        self.setWindowTitle(title)
        self.show()

    def setup_menu(self) -> None:
        """
        Sets up the menu bar.
        :return:
        """
        exit_act = QAction(QIcon('exit.png'), '&Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(qApp.quit)

        reboot_act = QAction('&Reboot', self)
        reboot_act.setShortcut('Ctrl+R')
        reboot_act.setStatusTip('Reboot application')
        reboot_act.triggered.connect(reboot_application)

        view_history_act = QAction('&View Scraping History', self)
        view_history_act.setStatusTip('View the scraping history')
        view_history_act.triggered.connect(self.show_scraping_history_dialog)

        settings_act = QAction('Settings', self)
        settings_act.triggered.connect(self.show_settings_dialog)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_act)
        file_menu.addAction(reboot_act)
        file_menu.addAction(view_history_act)
        file_menu.addAction(settings_act)

    def setup_buttons(self) -> None:
        """
        Sets up the buttons in the GUI.
        :return:
        """
        self.prev_button = self.create_button("Previous", self.show_previous)
        self.button_layout.addWidget(self.prev_button)
        self.prev_button.setVisible(False)

        self.next_button = self.create_button("Next", self.show_next)
        self.button_layout.addWidget(self.next_button)
        self.next_button.setVisible(False)

        self.scrape_button = self.create_button('Scrape Data', self.controller.scrape_data)
        self.button_layout.addWidget(self.scrape_button)

        self.view_button = self.create_button('View Data', lambda: self.show_data(), enabled=False)
        self.button_layout.addWidget(self.view_button)

        self.export_button = self.create_button('Export Data', self.show_export_dialog, enabled=False)
        self.button_layout.addWidget(self.export_button)

        self.view_search_queries_button = self.create_button('View Search Queries', self.controller.view_search_queries)
        self.button_layout.addWidget(self.view_search_queries_button)

        self.settings_button = self.create_button('Settings', self.show_settings_dialog)
        self.button_layout.addWidget(self.settings_button)

    def create_button(self, text, callback, enabled=True) -> QPushButton:
        """
        Creates a button.
        :param text: Text of the button.
        :param callback: Callback function to be called when the button is clicked.
        :param enabled: Enabled state of the button.
        :return: Button object.
        """
        button = QPushButton(text, self)
        button.setToolTip(text)
        button.setEnabled(enabled)
        button.clicked.connect(callback)
        return button

    def setup_progress_bar(self, layout: QLayout) -> None:
        """
        Sets up the progress bar.
        :param layout: Layout to add the progress bar to.
        :return:
        """
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.progress_layout = QHBoxLayout()
        self.progress_layout.addWidget(self.last_scrape_label)
        self.progress_layout.addWidget(self.progress_bar)
        layout.addLayout(self.progress_layout)

    def create_menu_button(self) -> QToolButton:
        """
        Creates a menu button.
        :return: The menu button.
        """
        menu_button = QToolButton(self)
        menu_button.setText('Menu')
        menu_button.setPopupMode(QToolButton.InstantPopup)
        menu_button.setMinimumSize(100, 50)
        menu = QMenu(menu_button)

        self.scrape_action = QAction('Scrape Data', self)
        self.scrape_action.triggered.connect(self.controller.scrape_data)
        menu.addAction(self.scrape_action)

        self.view_action = QAction('View Data', self)
        self.view_action.triggered.connect(lambda: self.show_data())
        menu.addAction(self.view_action)

        self.export_action = QAction('Export Data', self)
        self.export_action.triggered.connect(self.show_export_dialog)
        menu.addAction(self.export_action)

        self.view_search_queries_action = QAction('View Search Queries', self)
        self.view_search_queries_action.triggered.connect(self.controller.view_search_queries)
        menu.addAction(self.view_search_queries_action)

        self.settings_action = QAction('Settings', self)
        self.settings_action.triggered.connect(self.show_settings_dialog)
        menu.addAction(self.settings_action)

        menu_button.setMenu(menu)
        menu_button.setVisible(False)
        return menu_button

    def show_progress_bar(self) -> None:
        """
        Shows the progress bar.
        :return:
        """
        self.progress_bar.setVisible(True)

    def update_progress_bar(self, value: float) -> None:
        """
        Updates the progress bar.
        :param value: Value to set the progress bar to.
        :return:
        """
        self.progress_bar.setValue(value)

    def show_export_dialog(self) -> None:
        """
        Shows the export dialog.
        :return:
        """
        export_dialog = ExportDialog(self)
        if export_dialog.exec_() == QDialog.Accepted:
            export_format, save_path = export_dialog.get_export_details()
            if save_path:
                self.controller.export_data(export_format.lower(), save_path)

    def update_last_scrape_label(self) -> None:
        """
        Updates the last scrape label.
        :return:
        """
        last_scrape_date = self.controller.scraper.last_scrape_date
        if last_scrape_date:
            self.last_scrape_label.setText(f"Last Scrape: {last_scrape_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.last_scrape_label.setText("Last Scrape: Never")

    def show_data(self) -> None:
        """
        Shows the scraped data.
        :return:
        """
        if not self.controller.scraper.data_frames:
            return

        # Clear existing views
        while self.stacked_layout.count():
            widget = self.stacked_layout.widget(0)
            self.stacked_layout.removeWidget(widget)
            widget.deleteLater()

        # Add new table views with titles
        for title, df in self.controller.scraper.data_frames.items():
            container_widget = QWidget()
            container_layout = QVBoxLayout(container_widget)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(16)
            title_label.setFont(title_font)
            container_layout.addWidget(title_label)

            table_view = QTableView()
            table_view.setSortingEnabled(True)  # Enable sorting
            model = DataFrameModel(df)
            table_view.setModel(model)
            click_delegate = ClickableDelegate()
            table_view.setItemDelegateForColumn(4, click_delegate)
            table_view.setItemDelegateForColumn(5, click_delegate)
            table_view.resizeColumnsToContents()
            table_view.resizeRowsToContents()

            table_view.setShowGrid(True)
            table_view.setEditTriggers(QTableView.NoEditTriggers)

            # Set up the context menu
            table_view.setContextMenuPolicy(Qt.CustomContextMenu)
            table_view.customContextMenuRequested.connect(self.show_context_menu)

            container_layout.addWidget(table_view)

            self.stacked_layout.addWidget(container_widget)

        # Show the first table
        self.stacked_layout.setCurrentIndex(0)

        # Show only the necessary buttons after data is loaded
        self.prev_button.setVisible(True)
        self.next_button.setVisible(True)
        self.menu_button.setVisible(True)

        # Hide unnecessary buttons
        self.scrape_button.setVisible(False)
        self.view_button.setVisible(False)
        self.export_button.setVisible(False)
        self.view_search_queries_button.setVisible(False)
        self.settings_button.setVisible(False)
        self.update_button_layout_to_horizontal()
        if self.settings_dialog.dark_mode_toggle.isChecked():
            self.apply_dark_mode()

    def show_next(self) -> None:
        """
        Shows the next table.
        :return:
        """
        current_index = self.stacked_layout.currentIndex()
        if current_index < self.stacked_layout.count() - 1:
            self.stacked_layout.setCurrentIndex(current_index + 1)

    def show_previous(self) -> None:
        """
        Shows the previous table.
        :return:
        """
        current_index = self.stacked_layout.currentIndex()
        if current_index > 0:
            self.stacked_layout.setCurrentIndex(current_index - 1)

    def update_button_layout_to_horizontal(self) -> None:
        """
        Updates the button layout to horizontal.
        :return:
        """
        # Clear current button layout
        while self.button_layout.count():
            button = self.button_layout.takeAt(0).widget()
            if button:
                button.setParent(None)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.prev_button)
        horizontal_layout.addWidget(self.next_button)
        horizontal_layout.addWidget(self.menu_button)
        self.button_layout.addLayout(horizontal_layout)

    def show_context_menu(self, position: QPoint) -> None:
        """
        Shows the context menu for the table view.
        :param position: Position of the left upper corner of the context menu.
        :return:
        """
        indexes = self.sender().selectedIndexes()
        if indexes:
            context_menu = QMenu(self)

            show_image_action = QAction('Show Image', self)
            show_image_action.triggered.connect(lambda: self.show_image(indexes[0]))
            context_menu.addAction(show_image_action)

            delete_row_action = QAction('Delete Item', self)
            delete_row_action.triggered.connect(lambda: self.delete_row(indexes[0]))
            context_menu.addAction(delete_row_action)

            context_menu.exec_(self.sender().viewport().mapToGlobal(position))

    def show_settings_dialog(self) -> None:
        """
        Shows the settings dialog.
        :return:
        """
        self.settings_dialog = SettingsDialog(config_path='Resources/config.json')
        self.settings_dialog.exec_()

    def show_image(self, index: QModelIndex) -> None:
        """
        Shows the image in a dialog.
        :param index: Index of the selected row.
        :return:
        """

        image_url = index.sibling(index.row(), 5).data()

        if not image_url:
            QMessageBox.warning(self, "No Image", "No image URL found in the selected row.")
            return

        # Fetches and displays the image
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content

            pixmap = QPixmap()
            pixmap.loadFromData(image_data)

            image_dialog = ImageDialog(self, pixmap)
            image_dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load image: {e}")

    def enable_buttons(self):
        """
        Enables the view and export buttons.
        :return:
        """
        self.view_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def delete_row(self, index: QModelIndex) -> None:
        """
        Deletes the selected row.
        :param index: Index of the selected row.
        :return:
        """
        row = index.row()
        model = index.model()
        model.removeRow(row)

    def set_button_styles(self) -> None:
        """
        Sets the styles of the buttons.
        :return:
        """
        with open('GUI/stylesheets/button_stylesheet.qss') as stylesheet:
            button_style = stylesheet.read()
            self.scrape_button.setStyleSheet(button_style)
            self.view_button.setStyleSheet(button_style)
            self.export_button.setStyleSheet(button_style)
            self.view_search_queries_button.setStyleSheet(button_style)
            self.settings_button.setStyleSheet(button_style)
            self.prev_button.setStyleSheet(button_style)
            self.next_button.setStyleSheet(button_style)
            self.menu_button.setStyleSheet(button_style)

    def apply_dark_mode(self) -> None:
        """
        Applies the dark mode stylesheet.
        :return:
        """
        with open('GUI/stylesheets/main_window_stylesheet.qss') as stylesheet:
            self.setStyleSheet(stylesheet.read())

    def show_scraping_error(self, message: str) -> None:
        """
        Shows a message box with a scraping error.
        :param message: String message to display.
        :return:
        """
        QMessageBox.critical(self, "Scraping Error", f"An error occurred during scraping: {message}")

    def show_scraping_history_dialog(self) -> None:
        """
        Shows the scraping history dialog.
        :return:
        """
        history_dialog = ScrapingHistoryDialog('Resources/scraping_history.json', self)
        history_dialog.exec_()
