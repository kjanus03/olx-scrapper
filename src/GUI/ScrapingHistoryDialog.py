import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QMessageBox


class ScrapingHistoryDialog(QDialog):
    def __init__(self, history_path: str, parent=None) -> None:
        super(ScrapingHistoryDialog, self).__init__(parent)
        self.setWindowTitle("Scraping History")
        self.setModal(True)
        self.history_path = history_path
        self.history_data = self.load_history()
        self.init_ui()
        self.apply_stylesheet()

    def load_history(self) -> list[str]:
        try:
            with open(self.history_path, 'r') as file:
                return [date_dict['scrape_date'].replace('T', ' ')[:-7] for date_dict in json.load(file)]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.warning(self, "Error", f"Could not load scraping history: {e}")
            return []

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for entry in self.history_data:
            self.list_widget.addItem(entry)

        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def apply_stylesheet(self):
        with open('GUI/stylesheets/scraping_history_dialog_stylesheet.qss') as stylesheet:
            self.setStyleSheet(stylesheet.read())
