"""Image preview dialog with mouse-wheel zoom and pan."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QWheelEvent, QPainter
from PyQt5.QtWidgets import (
    QDialog, QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame
)


class ImageDialog(QDialog):
    """Dialog for displaying an image with zoom and pan."""

    def __init__(self, parent: QWidget, pixmap: QPixmap) -> None:
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.setMinimumSize(560, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.graphics_view = QGraphicsView(self)
        self.graphics_scene = QGraphicsScene(self.graphics_view)
        self.graphics_view.setScene(self.graphics_scene)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scene.addItem(self.pixmap_item)
        self.graphics_scene.setSceneRect(self.pixmap_item.boundingRect())

        self.graphics_view.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setFrameShape(QGraphicsView.NoFrame)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        outer.addWidget(self.graphics_view, 1)

        # Footer hint bar
        hint_bar = QFrame()
        hint_bar.setObjectName("AppStatusBar")
        hint_bar.setFixedHeight(36)
        hint_layout = QHBoxLayout(hint_bar)
        hint_layout.setContentsMargins(16, 0, 16, 0)
        hint = QLabel("Scroll to zoom · Drag to pan · Esc to close")
        hint.setObjectName("StatusLabel")
        hint_layout.addWidget(hint)
        hint_layout.addStretch(1)
        outer.addWidget(hint_bar)

        self.scale_factor = 1.0
        # Fit the image inside the view initially
        self.graphics_view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_in = 1.25
        zoom_out = 1 / zoom_in
        factor = zoom_in if event.angleDelta().y() > 0 else zoom_out
        # Clamp zoom
        new_scale = self.scale_factor * factor
        if new_scale < 0.1 or new_scale > 20:
            return
        self.scale_factor = new_scale
        self.graphics_view.scale(factor, factor)
