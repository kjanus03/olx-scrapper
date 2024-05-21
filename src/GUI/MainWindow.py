from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QPushButton, QVBoxLayout, QWidget, QStackedLayout, QHBoxLayout, \
    QLabel, QDialog, QTableView
from PyQt5.QtGui import QFont, QIcon
from src.GUI.DataFrameModel import DataFrameModel
from src.GUI.Controller import Controller
from src.GUI.ClickableDelegate import ClickableDelegate
from src.GUI.ExportDialog import ExportDialog


class MainWindow(QMainWindow):
    def __init__(self, title: str, width: int, height: int, controller: Controller):
        super().__init__()
        self.controller = controller
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
        main_layout.addWidget(self.last_scrape_label)
        self.update_last_scrape_label()

        # Navigation and action buttons layout
        self.button_layout = QHBoxLayout()
        main_layout.addLayout(self.button_layout)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous)
        self.button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next)
        self.button_layout.addWidget(self.next_button)

        self.scrape_button = QPushButton('Scrape Data', self)
        self.scrape_button.setToolTip('Start scraping data from OLX')
        self.scrape_button.clicked.connect(self.controller.scrape_data)
        self.scrape_button.clicked.connect(self.update_last_scrape_label)
        self.button_layout.addWidget(self.scrape_button)

        self.view_button = QPushButton('View Data', self)
        self.view_button.setToolTip('View the scraped data')
        self.view_button.clicked.connect(lambda: self.show_data())
        self.button_layout.addWidget(self.view_button)

        self.export_button = QPushButton('Export Data', self)
        self.export_button.setToolTip('Export the scraped data')
        self.export_button.clicked.connect(self.show_export_dialog)
        self.button_layout.addWidget(self.export_button)

        self.view_search_queries_button = QPushButton('View Search Queries', self)
        self.view_search_queries_button.setToolTip('View the search queries')
        self.view_search_queries_button.clicked.connect(self.controller.view_search_queries)
        self.button_layout.addWidget(self.view_search_queries_button)

        self.prev_button.setVisible(False)
        self.next_button.setVisible(False)
        self.export_button.setVisible(False)

        # Initialize QStackedLayout for table views
        self.stacked_layout = QStackedLayout()
        main_layout.addLayout(self.stacked_layout)

        self.setGeometry(100, 100, width, height)
        self.setWindowTitle(title)
        self.show()

    def show_export_dialog(self):
        export_dialog = ExportDialog(self)
        if export_dialog.exec_() == QDialog.Accepted:
            export_format, save_path = export_dialog.get_export_details()
            if save_path:
                self.controller.export_data(export_format.lower(), save_path)

    def update_last_scrape_label(self):
        last_scrape_date = self.controller.scraper.last_scrape_date
        if last_scrape_date:
            self.last_scrape_label.setText(f"Last Scrape: {last_scrape_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.last_scrape_label.setText("Last Scrape: Never")

    def show_data(self):
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
            container_layout.addWidget(table_view)

            self.stacked_layout.addWidget(container_widget)

        # Show the first table
        self.stacked_layout.setCurrentIndex(0)

        # Show buttons after data is loaded
        self.prev_button.setVisible(True)
        self.next_button.setVisible(True)
        self.export_button.setVisible(True)

    def show_next(self):
        current_index = self.stacked_layout.currentIndex()
        if current_index < self.stacked_layout.count() - 1:
            self.stacked_layout.setCurrentIndex(current_index + 1)

    def show_previous(self):
        current_index = self.stacked_layout.currentIndex()
        if current_index > 0:
            self.stacked_layout.setCurrentIndex(current_index - 1)
