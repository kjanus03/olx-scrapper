from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QPushButton, QTableView, QVBoxLayout, QWidget, QStackedLayout, \
    QHBoxLayout
from DataFrameModel import DataFrameModel
from Controller import Controller
from ClickableDelegate import ClickableDelegate


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
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        main_layout = QVBoxLayout(centralWidget)

        self.stacked_layout = QStackedLayout()
        main_layout.addLayout(self.stacked_layout)

        self.nav_layout = QHBoxLayout()
        main_layout.addLayout(self.nav_layout)

        # Create and set up the table view
        self.tableView = QTableView()
        click_delegate = ClickableDelegate()
        self.tableView.setItemDelegateForColumn(4, click_delegate)
        self.tableView.setItemDelegateForColumn(5, click_delegate)

        main_layout.addWidget(self.tableView)

        self.setGeometry(100, 100, width, height)
        self.setWindowTitle(title)
        self.init_buttons()
        self.show()

    def init_buttons(self):
        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous)
        self.nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next)
        self.nav_layout.addWidget(self.next_button)

        # Button to initiate scraping
        scrape_button = QPushButton('Scrape Data', self)
        scrape_button.setToolTip('Start scraping data from OLX')
        scrape_button.move(50, 100)
        scrape_button.clicked.connect(self.controller.scrape_data)

        # Button to view data
        view_button = QPushButton('View Data', self)
        view_button.setToolTip('View the scraped data')
        view_button.move(50, 150)
        view_button.clicked.connect(lambda: self.show_data())

    def hide_buttons(self) -> None:
        for widget in self.children():
            if isinstance(widget, QPushButton):
                widget.hide()

    def show_data(self):
        # Clear existing views
        while self.stacked_layout.count():
            widget = self.stacked_layout.widget(0)
            self.stacked_layout.removeWidget(widget)
            widget.deleteLater()

        # Add new table views
        for df in self.controller.scraper.data_frames.values():
            table_view = QTableView()
            model = DataFrameModel(df)
            table_view.setModel(model)
            click_delegate = ClickableDelegate()
            table_view.setItemDelegateForColumn(0, click_delegate)
            table_view.setItemDelegateForColumn(1, click_delegate)
            table_view.resizeColumnsToContents()
            table_view.resizeRowsToContents()
            self.stacked_layout.addWidget(table_view)

        # Show the first table
        self.stacked_layout.setCurrentIndex(0)
        self.hide_buttons()

    def show_next(self):
        current_index = self.stacked_layout.currentIndex()
        if current_index < self.stacked_layout.count() - 1:
            self.stacked_layout.setCurrentIndex(current_index + 1)

    def show_previous(self):
        current_index = self.stacked_layout.currentIndex()
        if current_index > 0:
            self.stacked_layout.setCurrentIndex(current_index - 1)
