"""Empty-state placeholder widget."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.GUI.widgets.IconProvider import icons


class EmptyState(QFrame):
    """A centered icon + title + subtitle placeholder.

    Designed to be dropped in any container as a fallback view when there is
    no data to render. The icon is tinted via the IconProvider so it tracks
    the current theme via a stylesheet color on `#EmptyStateIcon`.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str = "inbox",
        icon_color: str = "#4a4d52",
        icon_size: int = 56,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.addStretch(1)

        self._icon_name = icon_name
        self._icon_size = icon_size
        self.icon_label = QLabel()
        self.icon_label.setObjectName("EmptyStateIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(
            icons.pixmap(icon_name, color=icon_color, size=icon_size)
        )
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("EmptyStateTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.sub_label = QLabel(subtitle)
        self.sub_label.setObjectName("EmptyStateSub")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setWordWrap(True)
        self.sub_label.setMaximumWidth(420)
        layout.addWidget(self.sub_label, 0, Qt.AlignCenter)

        layout.addStretch(2)

    def set_icon_color(self, color: str) -> None:
        """Recolor the icon (used when toggling theme)."""
        self.icon_label.setPixmap(
            icons.pixmap(self._icon_name, color=color, size=self._icon_size)
        )
