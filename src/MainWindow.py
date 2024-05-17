from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, qApp


class MainWindow(QMainWindow):
    def __init__(self, title: str, width: int, height: int):
        super().__init__()
        self.init_ui(title, width, height)

    def init_ui(self, title: str, width: int, height: int):
        exit_act = QAction(QIcon('exit.png'), '&Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(qApp.quit)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_act)

        self.setGeometry(100, 100, width, height)
        self.setWindowTitle(title)
        self.show()
