from typing import Optional

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QPushButton, QVBoxLayout, QWidget, QStackedLayout, QHBoxLayout, \
    QLabel, QDialog, QTableView, QProgressBar, QMenu, QToolButton, QMessageBox
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QPoint, QModelIndex
from src.GUI.DataFrameModel import DataFrameModel
from src.GUI.Controller import Controller
from src.GUI.ClickableDelegate import ClickableDelegate
from src.GUI.ExportDialog import ExportDialog
from src.GUI.ImageDialog import ImageDialog
from src.GUI.SettingsDialog import SettingsDialog
import requests


class MainWindow(QMainWindow):
    def __init__(self, title: str, width: int, height: int, controller: Controller, button_style: Optional[str] = None):
        super().__init__()
        self.controller = controller
        self.controller.progress_updated.connect(self.update_progress_bar)
        self.controller.scraping_done.connect(self.update_last_scrape_label)
        self.controller.scraping_done.connect(self.enable_buttons)
        self.button_style = button_style
        self.settings_dialog=None
        self.init_ui(title, width, height)

    def init_ui(self, title: str, width: int, height: int):
        # Setup action to exit the application
        exit_act = QAction(QIcon('exit.png'), '&Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(qApp.quit)

        self.statusBar()

        # Create menu bar and add exit action
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_act)

        # Set up the central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Add a label to display the last scrape date
        self.last_scrape_label = QLabel(self)
        self.update_last_scrape_label()

        # Navigation and action buttons layout
        self.button_layout = QVBoxLayout()
        main_layout.addLayout(self.button_layout)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous)
        self.prev_button.setVisible(False)  # Initially hidden
        self.button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next)
        self.next_button.setVisible(False)  # Initially hidden
        self.button_layout.addWidget(self.next_button)

        self.scrape_button = QPushButton('Scrape Data', self)
        self.scrape_button.setToolTip('Start scraping data from OLX')
        self.scrape_button.clicked.connect(self.show_progress_bar)
        self.scrape_button.clicked.connect(self.controller.scrape_data)
        self.scrape_button.clicked.connect(self.update_last_scrape_label)
        self.button_layout.addWidget(self.scrape_button)

        self.view_button = QPushButton('View Data', self)
        self.view_button.setToolTip('View the scraped data')
        self.view_button.setEnabled(False)  # Initially disabled
        self.view_button.clicked.connect(lambda: self.show_data())
        self.button_layout.addWidget(self.view_button)

        self.export_button = QPushButton('Export Data', self)
        self.export_button.setToolTip('Export the scraped data')
        self.export_button.setEnabled(False)  # Initially disabled
        self.export_button.clicked.connect(self.show_export_dialog)
        self.button_layout.addWidget(self.export_button)

        self.view_search_queries_button = QPushButton('View Search Queries', self)
        self.view_search_queries_button.setToolTip('View the search queries')
        self.view_search_queries_button.clicked.connect(self.controller.view_search_queries)
        self.button_layout.addWidget(self.view_search_queries_button)

        self.settings_button = QPushButton('Settings', self)
        self.settings_button.setToolTip('Modify settings')
        self.settings_button.clicked.connect(self.show_settings_dialog)
        self.button_layout.addWidget(self.settings_button)

        # Create the drop-down menu button
        self.menu_button = QToolButton(self)
        self.menu_button.setText('Menu')
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setMinimumSize(100, 50)  # Adjust these values as needed
        self.menu = QMenu(self.menu_button)

        self.scrape_action = QAction('Scrape Data', self)
        self.scrape_action.triggered.connect(self.controller.scrape_data)
        self.scrape_action.triggered.connect(self.update_last_scrape_label)
        self.scrape_action.triggered.connect(self.show_progress_bar)
        self.menu.addAction(self.scrape_action)

        self.view_action = QAction('View Data', self)
        self.view_action.triggered.connect(lambda: self.show_data())
        self.menu.addAction(self.view_action)

        self.export_action = QAction('Export Data', self)
        self.export_action.triggered.connect(self.show_export_dialog)
        self.menu.addAction(self.export_action)

        self.view_search_queries_action = QAction('View Search Queries', self)
        self.view_search_queries_action.triggered.connect(self.controller.view_search_queries)
        self.menu.addAction(self.view_search_queries_action)

        self.settings_action = QAction('Settings', self)
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.menu.addAction(self.settings_action)

        self.menu_button.setMenu(self.menu)
        self.menu_button.setVisible(False)  # Initially hidden
        self.button_layout.addWidget(self.menu_button)

        # Initialize QStackedLayout for table views
        self.stacked_layout = QStackedLayout()
        main_layout.addLayout(self.stacked_layout)

        # Progress bar layout
        self.progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)  # Initially hidden
        self.progress_layout.addWidget(self.last_scrape_label)
        self.progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(self.progress_layout)

        self.setGeometry(100, 100, width, height)
        self.set_button_styles()
        if self.settings_dialog:
            if self.settings_dialog.dark_mode_toggle.isChecked():
                self.apply_dark_mode()
        self.setWindowTitle(title)
        self.show()

    def show_progress_bar(self) -> None:
        self.progress_bar.setVisible(True)

    def update_progress_bar(self, value: float) -> None:
        self.progress_bar.setValue(value)

    def show_export_dialog(self) -> None:
        export_dialog = ExportDialog(self)
        if export_dialog.exec_() == QDialog.Accepted:
            export_format, save_path = export_dialog.get_export_details()
            if save_path:
                self.controller.export_data(export_format.lower(), save_path)

    def update_last_scrape_label(self) -> None:
        last_scrape_date = self.controller.scraper.last_scrape_date
        if last_scrape_date:
            self.last_scrape_label.setText(f"Last Scrape: {last_scrape_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.last_scrape_label.setText("Last Scrape: Never")

    def show_data(self) -> None:
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
            # table_view.setAlternatingRowColors(True)
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
        if self.settings_dialog:
            if self.settings_dialog.dark_mode_toggle.isChecked():
                self.apply_dark_mode()

    def show_next(self) -> None:
        current_index = self.stacked_layout.currentIndex()
        if current_index < self.stacked_layout.count() - 1:
            self.stacked_layout.setCurrentIndex(current_index + 1)

    def show_previous(self) -> None:
        current_index = self.stacked_layout.currentIndex()
        if current_index > 0:
            self.stacked_layout.setCurrentIndex(current_index - 1)

    def update_button_layout_to_horizontal(self) -> None:
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
        self.settings_dialog = SettingsDialog(config_path='Resources/config.json')
        self.settings_dialog.exec_()

    def show_image(self, index: QModelIndex) -> None:
        # Extract the image URL from the selected row
        image_url = index.sibling(index.row(), 5).data()

        if not image_url:
            QMessageBox.warning(self, "No Image", "No image URL found in the selected row.")
            return

        # Fetch and display the image
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
        self.view_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def delete_row(self, index: QModelIndex) -> None:
        row = index.row()
        model = index.model()
        model.removeRow(row)

    def set_button_styles(self):
        self.scrape_button.setStyleSheet(self.button_style)
        self.view_button.setStyleSheet(self.button_style)
        self.export_button.setStyleSheet(self.button_style)
        self.view_search_queries_button.setStyleSheet(self.button_style)
        self.settings_button.setStyleSheet(self.button_style)
        self.prev_button.setStyleSheet(self.button_style)
        self.next_button.setStyleSheet(self.button_style)
        self.menu_button.setStyleSheet(self.button_style)

    def apply_dark_mode(self):
        self.setStyleSheet("""
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
                background-color: #2b2b2b;
                alternate-background-color: #323232;
                gridline-color: #444444;
                color: #f0f0f0;
                border: none;
            }
            QTableView QTableCornerButton::section {
                background-color: #2b2b2b;
            }
            QTableView::item {
                border: 1px solid #444444;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #f0f0f0;
                padding: 5px;
                border: 1px solid #5c5c5c;
            }
            QScrollBar:vertical {
                background-color: #2e2e2e;
                width: 15px;
                margin: 22px 0 22px 0;
            }
            QScrollBar::handle:vertical {
                background-color: #5c5c5c;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background-color: #2e2e2e;
                height: 20px;
                subcontrol-origin: margin;
                subcontrol-position: top;
            }
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {
                background-color: #5c5c5c;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #2e2e2e;
                height: 15px;
                margin: 0px 22px 0px 22px;
            }
            QScrollBar::handle:horizontal {
                background-color: #5c5c5c;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background-color: #2e2e2e;
                width: 20px;
                subcontrol-origin: margin;
                subcontrol-position: left;
            }
            QScrollBar::add-line:horizontal:hover, QScrollBar::sub-line:horizontal:hover {
                background-color: #5c5c5c;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                background: #5c5c5c;
            }
            QScrollBar::up-arrow:vertical:hover, QScrollBar::down-arrow:vertical:hover,
            QScrollBar::left-arrow:horizontal:hover, QScrollBar::right-arrow:horizontal:hover {
                background: #4d4d4d;
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
            QHeaderView {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #f0f0f0;
            }
            QTableCornerButton::section {
                background-color: #2b2b2b;
                border: 1px solid #5c5c5c;
            }
        """)



