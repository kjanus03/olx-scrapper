"""Non-blocking toast/banner notifications.

A `ToastManager` lives on the MainWindow. Call `show_toast(title, body, kind)`
to drop a toast in the top-right of the parent. They auto-dismiss after a few
seconds with a fade animation. Multiple toasts stack vertically.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QObject
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget,
    QGraphicsOpacityEffect, QToolButton, QSizePolicy
)

from src.GUI.widgets.IconProvider import icons


class ToastKind(Enum):
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"


_KIND_ICON = {
    ToastKind.INFO: ("info", "#a5b4fc"),
    ToastKind.SUCCESS: ("check-circle", "#8ce99a"),
    ToastKind.ERROR: ("alert", "#ffa8a8"),
}


class Toast(QFrame):
    """A single toast. Owns its fade-in/out animation and lifetime."""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        body: str = "",
        kind: ToastKind = ToastKind.INFO,
        duration_ms: int = 3800,
    ) -> None:
        super().__init__(parent)
        self.setObjectName({
            ToastKind.INFO: "ToastInfo",
            ToastKind.SUCCESS: "ToastSuccess",
            ToastKind.ERROR: "ToastError",
        }[kind])
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 12, 12)
        layout.setSpacing(12)

        icon_name, icon_color = _KIND_ICON[kind]
        icon_label = QLabel()
        icon_label.setPixmap(icons.pixmap(icon_name, color=icon_color, size=18))
        icon_label.setFixedSize(18, 18)
        layout.addWidget(icon_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("ToastTitle")
        title_label.setWordWrap(True)
        text_col.addWidget(title_label)

        if body:
            body_label = QLabel(body)
            body_label.setObjectName("ToastBody")
            body_label.setWordWrap(True)
            text_col.addWidget(body_label)
        layout.addLayout(text_col, 1)

        close_btn = QToolButton()
        close_btn.setObjectName("IconButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setIcon(icons.icon("x", color="#909296", size=14))
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self.dismiss)
        layout.addWidget(close_btn, 0, Qt.AlignTop)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(180)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.dismiss)
        self._duration_ms = duration_ms

    # --------------------------------------------------------------
    def show_with_fade(self) -> None:
        self.show()
        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._dismiss_timer.start(self._duration_ms)

    def dismiss(self) -> None:
        self._dismiss_timer.stop()
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)
        try:
            self._fade.finished.disconnect()
        except TypeError:
            pass
        self._fade.finished.connect(self._on_dismissed)
        self._fade.start()

    def _on_dismissed(self) -> None:
        if self._mgr is not None:
            self._mgr._remove(self)
        self.deleteLater()

    _mgr: Optional["ToastManager"] = None


class ToastManager:
    """Stacks toasts in the top-right of a host widget. Re-flows on resize."""

    MARGIN = 18
    GAP = 10

    def __init__(self, host: QWidget) -> None:
        self.host = host
        self._toasts: List[Toast] = []
        host.installEventFilter(_HostResizeFilter(self))

    def show(
        self,
        title: str,
        body: str = "",
        kind: ToastKind = ToastKind.INFO,
        duration_ms: int = 3800,
    ) -> Toast:
        toast = Toast(self.host, title, body, kind, duration_ms)
        toast._mgr = self
        toast.adjustSize()
        self._toasts.append(toast)
        self._reflow()
        toast.show_with_fade()
        toast.raise_()
        return toast

    def info(self, title: str, body: str = "") -> Toast:
        return self.show(title, body, ToastKind.INFO)

    def success(self, title: str, body: str = "") -> Toast:
        return self.show(title, body, ToastKind.SUCCESS)

    def error(self, title: str, body: str = "") -> Toast:
        return self.show(title, body, ToastKind.ERROR)

    # --------------------------------------------------------------
    def _remove(self, toast: Toast) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reflow()

    def _reflow(self) -> None:
        host_w = self.host.width()
        y = self.MARGIN
        for t in self._toasts:
            t.adjustSize()
            x = host_w - t.width() - self.MARGIN
            t.move(QPoint(max(self.MARGIN, x), y))
            y += t.height() + self.GAP


class _HostResizeFilter(QObject):
    """Tiny event filter so toasts re-flow when the host resizes."""

    def __init__(self, mgr: ToastManager) -> None:
        super().__init__(mgr.host)
        self._mgr = mgr

    def eventFilter(self, obj, event):  # noqa: D401 (Qt signature)
        if event.type() == QEvent.Resize:
            self._mgr._reflow()
        return False


class Banner(QFrame):
    """A persistent, in-flow banner for blocking errors/info messages."""

    def __init__(
        self,
        title: str,
        body: str = "",
        kind: ToastKind = ToastKind.INFO,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("BannerError" if kind == ToastKind.ERROR else "Banner")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 12, 10)
        layout.setSpacing(12)

        icon_name, icon_color = _KIND_ICON[kind]
        icon_label = QLabel()
        icon_label.setPixmap(icons.pixmap(icon_name, color=icon_color, size=18))
        icon_label.setFixedSize(18, 18)
        layout.addWidget(icon_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("ToastTitle")
        text_col.addWidget(title_label)
        if body:
            body_label = QLabel(body)
            body_label.setObjectName("ToastBody")
            body_label.setWordWrap(True)
            text_col.addWidget(body_label)
        layout.addLayout(text_col, 1)
