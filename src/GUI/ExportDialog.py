"""Export dialog — choose a format and target directory.

Modernised: format radio cards (with descriptions), folder picker with
inline validation, and a primary/secondary footer.
"""
from __future__ import annotations

from typing import Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QWidget, QFrame, QButtonGroup, QRadioButton, QLineEdit, QSizePolicy
)

from src.Exporting.ExportManager import ExportFormat
from src.GUI.widgets import icons


_FORMAT_DESCRIPTIONS = {
    "EXCEL": "Multi-sheet .xlsx with formatted columns and clickable links.",
    "CSV":   "One CSV file per query, comma-separated.",
    "PDF":   "A single landscape PDF — handy for printing or archiving.",
    "JSON":  "Structured JSON keyed by query name.",
    "XML":   "Structured XML with the same shape as JSON.",
}


class ExportDialog(QDialog):
    """Dialog for exporting data to a file."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        self.setModal(True)
        self.setMinimumWidth(540)
        self._init_ui()

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
        title = QLabel("Export Data")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        sub = QLabel("Pick a format, then choose where to save.")
        sub.setObjectName("DialogSubtitle")
        layout.addWidget(sub)

        # Format section
        layout.addWidget(self._section("FORMAT"))
        self.format_group = QButtonGroup(self)
        self.format_group.setExclusive(True)
        format_col = QVBoxLayout()
        format_col.setSpacing(6)
        for fmt in ExportFormat:
            row = self._build_format_row(fmt.name)
            format_col.addWidget(row)
        layout.addLayout(format_col)

        # Path section
        layout.addWidget(self._section("DESTINATION"))
        path_label = QLabel("Save to directory")
        path_label.setObjectName("FieldLabel")
        layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Choose a folder…")
        path_row.addWidget(self.path_input, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SecondaryButton")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setIcon(icons.icon("folder", color="#909296", size=14))
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        self.path_error = QLabel("")
        self.path_error.setObjectName("FieldHint")
        self.path_error.setVisible(False)
        layout.addWidget(self.path_error)

        # Footer
        layout.addStretch(1)
        divider = QFrame()
        divider.setObjectName("DialogDivider")
        layout.addWidget(divider)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 8, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("PrimaryButton")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setDefault(True)
        self.export_btn.clicked.connect(self._on_export)
        footer.addWidget(self.export_btn)
        layout.addLayout(footer)

    @staticmethod
    def _section(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("DialogSectionTitle")
        return lbl

    def _build_format_row(self, name: str) -> QFrame:
        row = QFrame()
        row.setProperty("role", "card")
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 10, 14, 10)
        row_layout.setSpacing(12)

        rb = QRadioButton(name)
        rb.setProperty("export_format", name)
        rb.setCursor(Qt.PointingHandCursor)
        if not self.format_group.buttons():
            rb.setChecked(True)
        self.format_group.addButton(rb)
        row_layout.addWidget(rb, 0, Qt.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel(name)
        title.setObjectName("FieldLabel")
        col.addWidget(title)
        sub = QLabel(_FORMAT_DESCRIPTIONS.get(name, ""))
        sub.setObjectName("FieldHint")
        sub.setWordWrap(True)
        col.addWidget(sub)
        row_layout.addLayout(col, 1)
        # Click anywhere on the row to select the radio
        row.mousePressEvent = lambda e, _rb=rb: _rb.setChecked(True)
        # Hide the radio's own label text since we render it in the column
        rb.setText("")
        return row

    # ------------------------------------------------------------------
    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_input.setText(directory)
            self._clear_path_error()

    def _show_path_error(self, msg: str) -> None:
        self.path_error.setObjectName("FieldError")
        self.path_error.setText(msg)
        self.path_error.setVisible(True)
        self.path_error.style().unpolish(self.path_error)
        self.path_error.style().polish(self.path_error)
        self.path_input.setProperty("error", True)
        self.path_input.style().unpolish(self.path_input)
        self.path_input.style().polish(self.path_input)

    def _clear_path_error(self) -> None:
        self.path_error.setVisible(False)
        self.path_input.setProperty("error", False)
        self.path_input.style().unpolish(self.path_input)
        self.path_input.style().polish(self.path_input)

    def _on_export(self) -> None:
        if not self.path_input.text().strip():
            self._show_path_error("Choose a target directory before exporting.")
            return
        self.accept()

    # ------------------------------------------------------------------
    def get_export_details(self) -> Tuple[str, str]:
        checked = self.format_group.checkedButton()
        fmt = checked.property("export_format") if checked else "EXCEL"
        return str(fmt), self.path_input.text().strip()
