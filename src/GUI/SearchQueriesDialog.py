import json
import re
from typing import List, Union, Any, Optional

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QAbstractItemView, QMessageBox


class SearchQueryTableModel(QAbstractTableModel):
    def __init__(self, queries: List[dict], parent: Optional[Any] = None) -> None:
        super(SearchQueryTableModel, self).__init__(parent)
        self.queries = queries

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.queries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 3

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Union[QVariant, str, dict]:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            query = self.queries[index.row()]
            column = index.column()
            if column == 0:
                return query.get("item_query", "")
            elif column == 1:
                return query.get("city", "")
            elif column == 2:
                return query.get("distance", "")

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Union[str, QVariant]:
        headers = ["Item Query", "City", "Distance"]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return headers[section]
        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if index.isValid() and role == Qt.EditRole:
            value = self.remove_polish_signs(value.strip().lower())
            if not self.validate_input(value):
                QMessageBox.warning(None, "Invalid Input", "Item Query contains invalid characters.")
                return False
            query = self.queries[index.row()]
            column = index.column()
            if column == 0:
                query["item_query"] = value
            elif column == 1:
                query["city"] = value
            elif column == 2:
                query["distance"] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def addQuery(self, query: dict) -> None:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.queries.append(query)
        self.endInsertRows()

    def removeQuery(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)
        self.queries.pop(row)
        self.endRemoveRows()

    def validate_input(self, text: str) -> bool:
        # Validate input to ensure it only contains characters that are valid for URLs
        pattern = re.compile(r'^[a-z0-9\-_\sąćęłńóśźż]+$')
        return bool(pattern.match(text))

    def remove_polish_signs(self, text: str) -> str:
        # Remove Polish signs from the text
        polish_signs = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
        for sign, replacement in polish_signs.items():
            text = text.replace(sign, replacement)
        return text


class SearchQueriesDialog(QDialog):
    def __init__(self, config_path: str, parent: Optional[Any] = None) -> None:
        super(SearchQueriesDialog, self).__init__(parent)
        self.setWindowTitle("Search Queries")
        self.setModal(True)
        self.config_path = config_path
        self.config_data: dict = {}  # To store the entire JSON data
        self.init_ui()
        self.load_queries()
        self.adjust_size()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.table_model = SearchQueryTableModel([])
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

        self.table_view.setColumnWidth(0, 200)  # Width for "Item Query"
        self.table_view.setColumnWidth(1, 150)  # Width for "City"
        self.table_view.setColumnWidth(2, 100)

        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton()
        self.add_button.setIcon(QIcon("GUI/icons/add_icon.png"))
        self.add_button.setFixedSize(40, 40)
        self.add_button.setStyleSheet("background-color: lightgreen; color: white; border: none;")
        self.add_button.clicked.connect(self.add_query)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QIcon("GUI/icons/remove_icon.png"))
        self.delete_button.setFixedSize(40, 40)
        self.delete_button.setStyleSheet("background-color: lightcoral; color: white; border: none;")
        self.delete_button.clicked.connect(self.delete_query)
        button_layout.addWidget(self.delete_button)

        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        button_layout.addWidget(self.accept_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_queries(self) -> None:
        with open(self.config_path, 'r') as file:
            self.config_data = json.load(file)
        self.table_model.queries = self.config_data.get('search_queries', [])
        self.table_model.layoutChanged.emit()

    def add_query(self) -> None:
        new_query = {"item_query": "", "city": "", "distance": ""}
        self.table_model.addQuery(new_query)
        self.adjust_size()

    def delete_query(self) -> None:
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "No query selected for deletion.")
            return
        for index in sorted(selected_indexes, reverse=True):
            self.table_model.removeQuery(index.row())
        self.adjust_size()

    def accept(self) -> None:
        self.config_data['search_queries'] = self.table_model.queries  # Update only the search_queries part
        with open(self.config_path, 'w') as file:
            json.dump(self.config_data, file, indent=4)
        super().accept()

    def adjust_size(self) -> None:
        # Adjust the dialog size based on the number of rows in the table view
        row_height = self.table_view.verticalHeader().defaultSectionSize()
        num_rows = self.table_model.rowCount(QModelIndex())
        table_height = row_height * num_rows

        table_width = self.table_view.horizontalHeader().length()

        self.resize(table_width + 40, table_height + 140)
