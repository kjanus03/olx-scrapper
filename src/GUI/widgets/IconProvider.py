"""Theme-aware SVG icon loader.

Icons live in `src/GUI/icons/svg/<name>.svg` and use `currentColor` as a
placeholder for the stroke/fill. `IconProvider.icon(name, color)` reads the
SVG, swaps in the requested color, renders to a QPixmap, and returns a QIcon.
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

from PyQt5.QtCore import QByteArray, Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer


_SVG_DIR = os.path.join(os.path.dirname(__file__), "..", "icons", "svg")


class IconProvider:
    """Loads SVGs once, tints them on demand, caches the rendered pixmaps."""

    def __init__(self, svg_dir: str = _SVG_DIR) -> None:
        self.svg_dir = os.path.normpath(svg_dir)
        self._svg_cache: Dict[str, str] = {}
        self._icon_cache: Dict[Tuple[str, str, int], QIcon] = {}

    def _load_svg(self, name: str) -> str:
        if name in self._svg_cache:
            return self._svg_cache[name]
        path = os.path.join(self.svg_dir, f"{name}.svg")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
        except FileNotFoundError:
            data = ""
        self._svg_cache[name] = data
        return data

    def pixmap(self, name: str, color: str = "#e9ecef", size: int = 18) -> QPixmap:
        svg = self._load_svg(name)
        if not svg:
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
            return pm
        # Two channels: explicit currentColor and any inline stroke we want tinted
        tinted = svg.replace("currentColor", color)
        renderer = QSvgRenderer(QByteArray(tinted.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def icon(self, name: str, color: str = "#e9ecef", size: int = 18) -> QIcon:
        key = (name, color, size)
        cached = self._icon_cache.get(key)
        if cached is not None:
            return cached
        pm = self.pixmap(name, color, size)
        ico = QIcon(pm)
        self._icon_cache[key] = ico
        return ico

    def clear_cache(self) -> None:
        self._icon_cache.clear()


# Module-level singleton — one cache across the app.
icons = IconProvider()
