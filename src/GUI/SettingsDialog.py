"""Settings dialog — application preferences with inline validation.

Exposes two signals:
    theme_changed(bool)   — emitted live when the user toggles dark mode
    settings_saved()      — emitted after a successful save
"""
from __future__ import annotations

import json
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QFrame, QSpinBox, QWidget, QSizePolicy
)

from src.Resources.input_validation import (
    validate_filename, validate_page_limit, validate_dimension, validate_fontsize
)


class _Field(QWidget):
    """Composite: label + input + hint/error line. Used for every form row."""

    def __init__(
        self,
        label: str,
        widget: QWidget,
        hint: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.label = QLabel(label)
        self.label.setObjectName("FieldLabel")
        layout.addWidget(self.label)

        self.input = widget
        layout.addWidget(self.input)

        self.message = QLabel(hint)
        self.message.setObjectName("FieldHint" if hint else "FieldHint")
        self.message.setWordWrap(True)
        self.message.setVisible(bool(hint))
        layout.addWidget(self.message)

        self._default_hint = hint

    def show_error(self, msg: str) -> None:
        self.message.setObjectName("FieldError")
        self.message.setText(msg)
        self.message.setVisible(True)
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        # Mark input red via dynamic property
        self.input.setProperty("error", True)
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)

    def clear_error(self) -> None:
        self.message.setObjectName("FieldHint")
        self.message.setText(self._default_hint)
        self.message.setVisible(bool(self._default_hint))
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        self.input.setProperty("error", False)
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)


class SettingsDialog(QDialog):
    """Application preferences. Non-destructive — only writes on Save."""

    theme_changed = pyqtSignal(bool)
    settings_saved = pyqtSignal()

    def __init__(
        self,
        config_path: str,
        current_dark_mode: Optional[bool] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.config_path = config_path
        self.config = self._load_config()
        if current_dark_mode is not None:
            self.config.setdefault("gui_config", {})["dark_mode"] = current_dark_mode
        self._original_dark_mode = bool(
            self.config.get("gui_config", {}).get("dark_mode", False)
        )
        self._init_ui()

    # ------------------------------------------------------------------
    def _load_config(self) -> dict:
        with open(self.config_path, "r") as f:
            return json.load(f)

    def _save_config(self) -> None:
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

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

        # ---- header ------------------------------------------------------
        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        sub = QLabel("Configure file output, window dimensions and theme.")
        sub.setObjectName("DialogSubtitle")
        layout.addWidget(sub)

        layout.addSpacing(4)

        # ---- General section --------------------------------------------
        layout.addWidget(self._section_label("OUTPUT"))

        gui_cfg = self.config.get("gui_config", {})
        out_cfg = self.config.get("output_config", {})

        self.f_filename = _Field(
            "Output filename (without extension)",
            QLineEdit(out_cfg.get("filename", "scraped_data")),
            hint="Letters, numbers and underscores only.",
        )
        self.f_filename.input.setPlaceholderText("scraped_data")
        layout.addWidget(self.f_filename)

        page_limit = QSpinBox()
        page_limit.setRange(1, 10)
        page_limit.setValue(int(gui_cfg.get("page_limit", 2)))
        self.f_page_limit = _Field(
            "Page limit per query",
            page_limit,
            hint="OLX pages to fetch per query (1–10).",
        )
        layout.addWidget(self.f_page_limit)

        # ---- Appearance section -----------------------------------------
        layout.addSpacing(4)
        layout.addWidget(self._section_label("APPEARANCE"))

        font = QSpinBox()
        font.setRange(8, 24)
        font.setValue(int(gui_cfg.get("fontsize", 14)))
        font.setSuffix(" pt")
        self.f_font = _Field(
            "Application font size",
            font,
            hint="Restart required (8–24 pt).",
        )
        layout.addWidget(self.f_font)

        dim_row = QHBoxLayout()
        dim_row.setSpacing(12)
        width = QSpinBox()
        width.setRange(100, 3000)
        width.setSingleStep(50)
        width.setValue(int(gui_cfg.get("width", 1600)))
        width.setSuffix(" px")
        self.f_width = _Field("Default width", width, hint="100–3000 px (restart required).")
        dim_row.addWidget(self.f_width, 1)

        height = QSpinBox()
        height.setRange(100, 3000)
        height.setSingleStep(50)
        height.setValue(int(gui_cfg.get("height", 900)))
        height.setSuffix(" px")
        self.f_height = _Field("Default height", height, hint="100–3000 px (restart required).")
        dim_row.addWidget(self.f_height, 1)
        layout.addLayout(dim_row)

        # Dark mode toggle row
        theme_row = QFrame()
        theme_row.setProperty("role", "card")
        theme_layout = QHBoxLayout(theme_row)
        theme_layout.setContentsMargins(14, 12, 14, 12)
        theme_layout.setSpacing(12)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("Dark mode")
        t.setObjectName("FieldLabel")
        col.addWidget(t)
        h = QLabel("Toggle the indigo-on-charcoal palette.")
        h.setObjectName("FieldHint")
        col.addWidget(h)
        theme_layout.addLayout(col, 1)

        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(bool(gui_cfg.get("dark_mode", False)))
        # Live preview as the user toggles. Reverted in reject() if cancelled.
        self.dark_mode_toggle.toggled.connect(self.theme_changed.emit)
        theme_layout.addWidget(self.dark_mode_toggle, 0, Qt.AlignVCenter)
        layout.addWidget(theme_row)

        # ---- footer ------------------------------------------------------
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

        save = QPushButton("Save Changes")
        save.setObjectName("PrimaryButton")
        save.setCursor(Qt.PointingHandCursor)
        save.setDefault(True)
        save.clicked.connect(self._on_save)
        footer.addWidget(save)
        layout.addLayout(footer)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("DialogSectionTitle")
        return lbl

    # ------------------------------------------------------------------
    def _on_save(self) -> None:
        for f in (self.f_filename, self.f_page_limit, self.f_font, self.f_width, self.f_height):
            f.clear_error()

        errors = 0
        try:
            output_filename = validate_filename(self.f_filename.input.text())
        except ValueError as e:
            self.f_filename.show_error(str(e))
            errors += 1
            output_filename = None

        try:
            page_limit = validate_page_limit(int(self.f_page_limit.input.value()))
        except ValueError as e:
            self.f_page_limit.show_error(str(e))
            errors += 1
            page_limit = None

        try:
            fontsize = validate_fontsize(int(self.f_font.input.value()))
        except ValueError as e:
            self.f_font.show_error(str(e))
            errors += 1
            fontsize = None

        try:
            width = validate_dimension(int(self.f_width.input.value()))
        except ValueError as e:
            self.f_width.show_error(str(e))
            errors += 1
            width = None

        try:
            height = validate_dimension(int(self.f_height.input.value()))
        except ValueError as e:
            self.f_height.show_error(str(e))
            errors += 1
            height = None

        if errors:
            return

        cfg = self.config
        cfg.setdefault("output_config", {})["filename"] = output_filename
        gui = cfg.setdefault("gui_config", {})
        gui["page_limit"] = page_limit
        gui["fontsize"] = fontsize
        gui["width"] = width
        gui["height"] = height
        gui["dark_mode"] = self.dark_mode_toggle.isChecked()

        self._save_config()
        self._original_dark_mode = self.dark_mode_toggle.isChecked()
        self.settings_saved.emit()
        self.accept()

    def reject(self) -> None:  # type: ignore[override]
        # Revert any live theme preview the user made before cancelling.
        if self.dark_mode_toggle.isChecked() != self._original_dark_mode:
            self.theme_changed.emit(self._original_dark_mode)
        super().reject()
