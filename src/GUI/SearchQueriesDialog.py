"""Manage the watchlist of OLX search queries.

Modernised: themed toolbar with Add/Remove icons, per-cell validation that
reverts invalid edits, and an empty state when the list is empty.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional, Union

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QAbstractItemView, QFrame, QLabel, QStackedWidget, QToolButton,
    QWidget, QHeaderView, QSizePolicy, QStyledItemDelegate
)

from src.GUI.widgets import icons, EmptyState


class _TableEditDelegate(QStyledItemDelegate):
    """Inline cell editor that removes the global QLineEdit padding/radius so
    text is never clipped by the focus border inside a table row."""

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if editor is not None:
            editor.setStyleSheet(
                "QLineEdit { border: none; border-radius: 0; padding: 0 6px; }"
            )
        return editor


_ALLOWED = re.compile(r"^[a-z0-9\-_\s]+$")
_POLISH = {
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ź": "z", "ż": "z",
}


def _normalise(text: str) -> str:
    text = text.strip().lower()
    for k, v in _POLISH.items():
        text = text.replace(k, v)
    return text


class SearchQueryTableModel(QAbstractTableModel):
    """Three-column editable model: item_query, city, distance (km)."""

    HEADERS = ["Item Query", "City", "Distance (km)"]
    KEYS = ["item_query", "city", "distance"]

    def __init__(self, queries: list, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.queries = queries

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.queries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else 3

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Union[QVariant, str, dict]:
        if not index.isValid():
            return QVariant()
        if role in (Qt.DisplayRole, Qt.EditRole):
            q = self.queries[index.row()]
            return str(q.get(self.KEYS[index.column()], "") or "")
        if role == Qt.TextAlignmentRole and index.column() == 2:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return QVariant()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Union[str, QVariant]:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        new_val = _normalise(str(value))
        col = index.column()
        # distance can be empty or numeric
        if col == 2:
            if new_val and not new_val.isdigit():
                return False
        else:
            if new_val and not _ALLOWED.match(new_val):
                return False
        self.queries[index.row()][self.KEYS[col]] = new_val
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def addQuery(self, query: dict) -> None:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.queries.append(query)
        self.endInsertRows()

    def removeQuery(self, row: int) -> None:
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            self.queries.pop(row)
            self.endRemoveRows()


class SearchQueriesDialog(QDialog):
    """Dialog for managing search queries."""

    def __init__(self, config_path: str, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Search Queries")
        self.setModal(True)
        self.config_path = config_path
        self.config_data: dict = {}
        self.setMinimumSize(720, 480)
        self._init_ui()
        self._load_queries()

    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        frame = QFrame()
        frame.setObjectName("DialogFrame")
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(28, 24, 28, 16)
        layout.setSpacing(16)

        # Header
        title = QLabel("Search Queries")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        sub = QLabel("Edit your watchlist. Each row produces an OLX search URL.")
        sub.setObjectName("DialogSubtitle")
        layout.addWidget(sub)

        # Toolbar row
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.setContentsMargins(0, 0, 0, 0)

        self.add_btn = QPushButton("Add Query")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setIcon(icons.icon("plus", color="#ffffff", size=14))
        self.add_btn.clicked.connect(self._add_query)
        toolbar.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setObjectName("DestructiveButton")
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setIcon(icons.icon("trash", color="#ff8787", size=14))
        self.remove_btn.clicked.connect(self._delete_query)
        toolbar.addWidget(self.remove_btn)

        toolbar.addStretch(1)

        self.count_label = QLabel("")
        self.count_label.setObjectName("FieldHint")
        toolbar.addWidget(self.count_label)
        layout.addLayout(toolbar)

        # Stack: table | empty state
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.table_model = SearchQueryTableModel([])
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setHighlightSections(False)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.setShowGrid(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setDefaultSectionSize(38)

        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_view.setColumnWidth(1, 180)
        self.table_view.setColumnWidth(2, 130)
        self.table_view.setItemDelegate(_TableEditDelegate(self.table_view))
        self.stack.addWidget(self.table_view)

        empty = EmptyState(
            title="No queries yet",
            subtitle="Click \"Add Query\" to start your watchlist.",
            icon_name="search",
        )
        self.stack.addWidget(empty)

        self.table_model.layoutChanged.connect(self._refresh_state)
        self.table_model.modelReset.connect(self._refresh_state)
        self.table_model.rowsInserted.connect(self._refresh_state)
        self.table_model.rowsRemoved.connect(self._refresh_state)

        # Footer
        divider = QFrame()
        divider.setObjectName("DialogDivider")
        layout.addWidget(divider)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 8, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        accept_btn = QPushButton("Save")
        accept_btn.setObjectName("PrimaryButton")
        accept_btn.setCursor(Qt.PointingHandCursor)
        accept_btn.setDefault(True)
        accept_btn.clicked.connect(self.accept)
        footer.addWidget(accept_btn)
        layout.addLayout(footer)

    # ------------------------------------------------------------------
    def _refresh_state(self) -> None:
        n = self.table_model.rowCount()
        self.count_label.setText(f"{n} quer{'y' if n == 1 else 'ies'}")
        self.stack.setCurrentIndex(0 if n > 0 else 1)

    def _load_queries(self) -> None:
        with open(self.config_path, "r") as f:
            self.config_data = json.load(f)
        self.table_model.queries = list(self.config_data.get("search_queries", []))
        self.table_model.layoutChanged.emit()
        self._refresh_state()

    def _add_query(self) -> None:
        self.table_model.addQuery({"item_query": "", "city": "", "distance": ""})
        new_row = self.table_model.rowCount() - 1
        self.table_view.scrollToBottom()
        self.table_view.selectRow(new_row)
        self.table_view.edit(self.table_model.index(new_row, 0))

    def _delete_query(self) -> None:
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            return
        for index in sorted(selected, key=lambda i: i.row(), reverse=True):
            self.table_model.removeQuery(index.row())

    # ------------------------------------------------------------------
    def accept(self) -> None:
        # Strip any rows where item_query is empty after edit
        cleaned = [q for q in self.table_model.queries if (q.get("item_query") or "").strip()]
        self.config_data["search_queries"] = cleaned
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f, indent=4)
        super().accept()
