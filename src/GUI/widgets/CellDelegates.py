"""Custom cell delegates for the data table.

Two delegates ship here:

1. **LinkChipDelegate** — renders a URL as an accent-tinted "Open ↗" pill
   instead of the raw URL. Click anywhere on the chip opens the URL in the
   user's browser.

2. **ThumbnailDelegate** — renders a small rounded thumbnail. Images are
   fetched lazily on a background thread (QThreadPool) keyed by URL, then
   cached. Cells that don't have a fetchable URL (relative `/app/static/...`
   placeholders) just show a generic image icon. Clicking the cell opens the
   full-size image in `ImageDialog`.

Both delegates accept a `palette` dict so they can re-tint themselves on
theme switch (see MainWindow.apply_theme).
"""
from __future__ import annotations

from typing import Callable, Dict, Optional, Set

import requests
from PyQt5.QtCore import (
    Qt, QEvent, QSize, QRect, QRectF, QObject, QRunnable, QThreadPool,
    QUrl, QModelIndex, pyqtSignal
)
from PyQt5.QtGui import (
    QPainter, QPainterPath, QColor, QPixmap, QImage, QFont, QFontMetrics,
    QDesktopServices, QBrush, QPen
)
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem

from src.GUI.widgets.IconProvider import icons


# ----------------------------------------------------------------------
# LinkChipDelegate
# ----------------------------------------------------------------------
class LinkChipDelegate(QStyledItemDelegate):
    """Render the cell as an accent pill labelled "Open ↗"."""

    DEFAULT_PALETTE: Dict[str, str] = {
        "chip_bg":     "#2d3142",
        "chip_text":   "#a5b4fc",
        "chip_border": "#2d3142",
        "selection":   "#2d3142",
    }

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.palette: Dict[str, str] = dict(self.DEFAULT_PALETTE)

    def set_palette(self, palette: Dict[str, str]) -> None:
        self.palette.update(palette)

    # ------------------------------------------------------------------
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(96, 40)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        url = str(index.data(Qt.DisplayRole) or "")
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(self.palette["selection"]))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor(0, 0, 0, 12))

        if not url:
            painter.restore()
            return

        # Pill rect — centered vertically, left-aligned with small inset
        pad_x = 12
        chip_h = min(28, option.rect.height() - 8)
        chip_w = min(86, option.rect.width() - 2 * pad_x)
        chip_rect = QRectF(
            option.rect.x() + pad_x,
            option.rect.y() + (option.rect.height() - chip_h) / 2,
            chip_w,
            chip_h,
        )
        painter.setPen(QPen(QColor(self.palette["chip_border"])))
        painter.setBrush(QBrush(QColor(self.palette["chip_bg"])))
        painter.drawRoundedRect(chip_rect, 14, 14)

        painter.setPen(QPen(QColor(self.palette["chip_text"])))
        f = QFont(painter.font())
        f.setWeight(QFont.DemiBold)
        f.setPointSize(max(9, f.pointSize()))
        painter.setFont(f)
        painter.drawText(chip_rect, Qt.AlignCenter, "Open  ↗")
        painter.restore()

    # ------------------------------------------------------------------
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            url = str(index.data(Qt.DisplayRole) or "")
            if url.startswith("http"):
                QDesktopServices.openUrl(QUrl(url))
                return True
        return super().editorEvent(event, model, option, index)


# ----------------------------------------------------------------------
# ThumbnailDelegate
# ----------------------------------------------------------------------
class _ThumbnailSignaler(QObject):
    """A small QObject that owns the cross-thread `ready` signal."""

    ready = pyqtSignal(str, QImage)


class _FetchRunnable(QRunnable):
    """Fetch a single image URL on a background thread, emit the result."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    def __init__(self, url: str, signaler: _ThumbnailSignaler) -> None:
        super().__init__()
        self.url = url
        self.signaler = signaler

    def run(self) -> None:  # noqa: D401 (QRunnable signature)
        img = QImage()
        try:
            r = requests.get(self.url, timeout=8, headers=self.HEADERS)
            r.raise_for_status()
            img.loadFromData(r.content)
        except Exception:
            img = QImage()
        # PyQt signals across threads queue automatically — this is safe.
        self.signaler.ready.emit(self.url, img)


class ThumbnailDelegate(QStyledItemDelegate):
    """Renders a 48×48 rounded thumbnail per row, lazy-loaded by URL.

    A single instance can serve every Photo cell in the app — the cache and
    the fetch queue are shared so the same image is never fetched twice.
    """

    THUMB = 48
    CELL_SIZE = QSize(74, 60)

    DEFAULT_PALETTE: Dict[str, str] = {
        "placeholder_bg":     "#25262b",
        "placeholder_border": "#373a40",
        "placeholder_icon":   "#6c6f75",
        "selection":          "#2d3142",
    }

    def __init__(
        self,
        on_open: Callable[[QModelIndex], None],
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._on_open = on_open
        self.palette: Dict[str, str] = dict(self.DEFAULT_PALETTE)
        self._cache: Dict[str, QPixmap] = {}
        self._pending: Set[str] = set()
        self._views: list = []  # views to repaint when a thumbnail arrives

        self._signaler = _ThumbnailSignaler()
        self._signaler.ready.connect(self._on_image_ready)
        self._pool = QThreadPool.globalInstance()

    # ------------------------------------------------------------------
    def set_palette(self, palette: Dict[str, str]) -> None:
        self.palette.update(palette)
        for v in self._views:
            try:
                v.viewport().update()
            except Exception:
                pass

    def register_view(self, view) -> None:
        if view is not None and view not in self._views:
            self._views.append(view)

    # ------------------------------------------------------------------
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return self.CELL_SIZE

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(self.palette["selection"]))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor(0, 0, 0, 12))

        # Centered square inside the cell
        size = self.THUMB
        cx = option.rect.x() + (option.rect.width() - size) // 2
        cy = option.rect.y() + (option.rect.height() - size) // 2
        target = QRect(cx, cy, size, size)

        url = str(index.data(Qt.DisplayRole) or "")
        pm = self._cache.get(url)

        path = QPainterPath()
        path.addRoundedRect(QRectF(target), 8, 8)
        painter.setClipPath(path)

        if pm is not None and not pm.isNull():
            scaled = pm.scaled(
                size, size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            # Crop to center if oversized
            sx = max(0, (scaled.width() - size) // 2)
            sy = max(0, (scaled.height() - size) // 2)
            painter.drawPixmap(target, scaled, QRect(sx, sy, size, size))
        else:
            # Placeholder
            painter.fillRect(target, QColor(self.palette["placeholder_bg"]))
            painter.setClipping(False)
            painter.setPen(QPen(QColor(self.palette["placeholder_border"]), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(target.adjusted(0, 0, -1, -1), 8, 8)
            icon_pm = icons.pixmap("image", color=self.palette["placeholder_icon"], size=20)
            ix = target.x() + (size - 20) // 2
            iy = target.y() + (size - 20) // 2
            painter.drawPixmap(ix, iy, icon_pm)
            self._maybe_request(url)
        painter.restore()

    # ------------------------------------------------------------------
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            self._on_open(index)
            return True
        return super().editorEvent(event, model, option, index)

    # ------------------------------------------------------------------
    def _maybe_request(self, url: str) -> None:
        if not url or url in self._pending:
            return
        if url in self._cache:
            return
        # OLX returns relative no-thumbnail SVG paths for missing photos.
        # Skip fetch — the placeholder icon is the right outcome.
        if not (url.startswith("http://") or url.startswith("https://")):
            self._cache[url] = QPixmap()
            return
        self._pending.add(url)
        self._pool.start(_FetchRunnable(url, self._signaler))

    def _on_image_ready(self, url: str, image: QImage) -> None:
        self._pending.discard(url)
        if image.isNull():
            self._cache[url] = QPixmap()
        else:
            self._cache[url] = QPixmap.fromImage(image)
        for v in self._views:
            try:
                v.viewport().update()
            except Exception:
                pass
