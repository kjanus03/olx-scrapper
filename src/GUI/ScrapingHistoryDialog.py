from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QStackedWidget, QWidget
)

from src.GUI.widgets import EmptyState, SearchBar


def _humanise(d: datetime, now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    delta = now - d
    secs = int(delta.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        m = secs // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if secs < 86400:
        h = secs // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if secs < 86400 * 30:
        d_ = secs // 86400
        return f"{d_} day{'s' if d_ != 1 else ''} ago"
    return d.strftime("%Y-%m-%d")


class ScrapingHistoryDialog(QDialog):
    """Dialog to display the scraping history."""

    def __init__(self, history_path: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Scraping History")
        self.setModal(True)
        self.setMinimumSize(520, 540)
        self.history_path = history_path
        self._entries: List[datetime] = self._load_history()
        self._init_ui()
        self._populate(self._entries)

    def _load_history(self) -> List[datetime]:
        try:
            with open(self.history_path, "r") as f:
                raw = json.load(f) or []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        out: List[datetime] = []
        for entry in raw:
            try:
                out.append(datetime.fromisoformat(entry["scrape_date"]))
            except (KeyError, ValueError):
                continue
        out.sort(reverse=True)
        return out

    def _init_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        frame = QFrame()
        frame.setObjectName("DialogFrame")
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(28, 24, 28, 16)
        layout.setSpacing(14)

        title = QLabel("Scraping History")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        sub = QLabel(f"{len(self._entries)} run{'s' if len(self._entries) != 1 else ''} logged.")
        sub.setObjectName("DialogSubtitle")
        layout.addWidget(sub)

        self.search = SearchBar(placeholder="Filter by date…")
        self.search.text_changed.connect(self._on_filter)
        layout.addWidget(self.search)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("HistoryList")
        self.stack.addWidget(self.list_widget)

        empty = EmptyState(
            title="No history yet",
            subtitle="Run your first scrape — entries appear here automatically.",
            icon_name="clock",
        )
        self.stack.addWidget(empty)

        # footer
        divider = QFrame()
        divider.setObjectName("DialogDivider")
        layout.addWidget(divider)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 8, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("PrimaryButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        
    def _populate(self, entries: List[datetime]) -> None:
        self.list_widget.clear()
        if not entries:
            self.stack.setCurrentIndex(1)
            return
        self.stack.setCurrentIndex(0)
        for d in entries:
            item = QListWidgetItem(
                f"{d.strftime('%Y-%m-%d   %H:%M:%S')}     ·     {_humanise(d)}"
            )
            item.setData(Qt.UserRole, d.isoformat())
            self.list_widget.addItem(item)

    def _on_filter(self, needle: str) -> None:
        n = needle.strip().lower()
        if not n:
            self._populate(self._entries)
            return
        filtered = [d for d in self._entries if n in d.strftime("%Y-%m-%d %H:%M:%S").lower()]
        self._populate(filtered)
