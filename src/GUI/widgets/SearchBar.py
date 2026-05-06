"""Themed search input — icon + line edit packaged into a single rounded frame."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QWidget

from src.GUI.widgets.IconProvider import icons


class SearchBar(QFrame):
    """Composite search field. Emits `text_changed` (str) on input."""

    text_changed = pyqtSignal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
        icon_color: str = "#6c6f75",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(0)

        self._icon_color = icon_color
        self.icon_label = QLabel()
        self.icon_label.setObjectName("SearchIcon")
        self.icon_label.setPixmap(icons.pixmap("search", color=icon_color, size=14))
        self.icon_label.setFixedWidth(34)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("SearchInput")
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.textChanged.connect(self.text_changed.emit)
        layout.addWidget(self.line_edit, 1)

    def text(self) -> str:
        return self.line_edit.text()

    def clear(self) -> None:
        self.line_edit.clear()

    def set_icon_color(self, color: str) -> None:
        self._icon_color = color
        self.icon_label.setPixmap(icons.pixmap("search", color=color, size=14))
