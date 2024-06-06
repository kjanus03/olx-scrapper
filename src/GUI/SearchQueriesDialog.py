import json
import re
from typing import Union, Any, Optional

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QAbstractItemView, QMessageBox


class SearchQueryTableModel(QAbstractTableModel):
    """Custom model for the search queries table view. It stores the search queries in a list of dictionaries."""
    def __init__(self, queries: list[dict], parent: Optional[Any] = None) -> None:
        """
        :param queries: List of dictionaries containing the search queries
        :param parent: Parent widget
        """
        super(SearchQueryTableModel, self).__init__(parent)
        self.queries = queries

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Return the number of rows in the table view
        :param parent: Parent index
        :return:
        """
        return len(self.queries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Return the number of columns in the table view
        :param parent: Parent index
        :return:
        """
        return 3

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Union[QVariant, str, dict]:
        """
        Return the data for the given index and role
        :param index: Index of the item
        :param role: Role of the item
        :return: Value of the item
        """
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
        """
        Return the header data for the given section, orientation, and role
        :param section: Section number
        :param orientation: Orientation of the header
        :param role: Role of the header
        :return: Data of the header
        """
        headers = ["Item Query", "City", "Distance"]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return headers[section]
        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Return the flags for the given index
        :param index: Index of the item
        :return: Flags for the item
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        Set the data for the given index and role
        :param index: Index of the item
        :param value: Value to set
        :param role: Role of the item
        :return: True if the data was set successfully, False otherwise
        """
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
        """
        Add a new query to the table view
        :param query: Query to add
        :return:
        """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.queries.append(query)
        self.endInsertRows()

    def removeQuery(self, row: int) -> None:
        """
        Remove a query from the table view
        :param row: Row number of the query to remove
        :return:
        """
        self.beginRemoveRows(QModelIndex(), row, row)
        self.queries.pop(row)
        self.endRemoveRows()

    def validate_input(self, text: str) -> bool:
        """
        Validate the input text to ensure it only contains characters that are valid for URLs
        :param text: Text to validate
        :return: True if the text is valid, False otherwise
        """
        pattern = re.compile(r'^[a-z0-9\-_\sąćęłńóśźż]+$')
        return bool(pattern.match(text))

    def remove_polish_signs(self, text: str) -> str:
        """
        Remove Polish signs from the text
        :param text: Text to remove Polish signs from
        :return: Text without Polish signs
        """
        polish_signs = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
        for sign, replacement in polish_signs.items():
            text = text.replace(sign, replacement)
        return text


class SearchQueriesDialog(QDialog):
    """Dialog for managing search queries."""
    def __init__(self, config_path: str, parent: Optional[Any] = None) -> None:
        """
        Initialize the dialog
        :param config_path: Configuration file path
        :param parent: Parent widget
        """
        super(SearchQueriesDialog, self).__init__(parent)
        self.setWindowTitle("Search Queries")
        self.setModal(True)
        self.config_path = config_path
        self.config_data: dict = {}  # To store the entire JSON data
        self.init_ui()
        self.load_queries()
        self.apply_stylesheet()
        self.adjust_size()

    def init_ui(self) -> None:
        """
        Initialize the user interface
        :return:
        """
        layout = QVBoxLayout(self)

        self.table_model = SearchQueryTableModel([])
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

        self.table_view.setColumnWidth(0, 300)  # Width for "Item Query"
        self.table_view.setColumnWidth(1, 250)  # Width for "City"
        self.table_view.setColumnWidth(2, 200)

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
        """
        Load the search queries from the configuration file
        :return:
        """
        with open(self.config_path, 'r') as file:
            self.config_data = json.load(file)
        self.table_model.queries = self.config_data.get('search_queries', [])
        self.table_model.layoutChanged.emit()

    def add_query(self) -> None:
        """
        Add a new query to the table view
        :return:
        """
        new_query = {"item_query": "", "city": "", "distance": ""}
        self.table_model.addQuery(new_query)
        self.adjust_size()

    def delete_query(self) -> None:
        """
        Delete the selected query from the table view
        :return:
        """
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "No query selected for deletion.")
            return
        for index in sorted(selected_indexes, reverse=True):
            self.table_model.removeQuery(index.row())
        self.adjust_size()

    def accept(self) -> None:
        """
        Save the search queries to the configuration file and close the dialog
        :return:
        """
        self.config_data['search_queries'] = self.table_model.queries  # Update only the search_queries part
        with open(self.config_path, 'w') as file:
            json.dump(self.config_data, file, indent=4)
        super().accept()

    def adjust_size(self) -> None:
        """
        Adjust the size of the dialog to fit the table view
        :return:
        """
        row_height = self.table_view.verticalHeader().defaultSectionSize()
        num_rows = self.table_model.rowCount(QModelIndex())
        table_height = row_height * num_rows

        table_width = self.table_view.horizontalHeader().length()

        self.resize(table_width + 40, table_height + 140)

    def apply_stylesheet(self) -> None:
        """
        Apply the stylesheet to the dialog
        :return:
        """
        with open('GUI/stylesheets/search_queries_stylesheet.qss') as stylesheet:
            self.setStyleSheet(stylesheet.read())
