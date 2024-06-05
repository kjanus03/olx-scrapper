from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QWheelEvent
from PyQt5.QtWidgets import QDialog, QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout


class ImageDialog(QDialog):
    """Dialog for displaying an image."""
    def __init__(self, parent: QWidget, pixmap: QPixmap) -> None:
        """
        Initialize the dialog.
        :param parent: Parent widget of the dialog.
        :param pixmap: Pixel map to display in the dialog.
        """
        super().__init__(parent)
        self.setWindowTitle("Image")
        self.graphics_view = QGraphicsView(self)
        self.graphics_scene = QGraphicsScene(self.graphics_view)
        self.graphics_view.setScene(self.graphics_scene)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scene.addItem(self.pixmap_item)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.graphics_view)

        self.setLayout(self.layout)
        self.setMinimumSize(400, 400)

        self.scale_factor = 1.0
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.graphics_view.setBackgroundBrush(Qt.black)
        self.graphics_view.setFrameShape(QGraphicsView.NoFrame)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle the wheel event.
        :param event: Wheel event.
        :return:
        """
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        old_pos = self.graphics_view.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self.scale_factor *= zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            self.scale_factor *= zoom_out_factor

        self.graphics_view.scale(zoom_factor, zoom_factor)

        new_pos = self.graphics_view.mapToScene(event.pos())

        delta = new_pos - old_pos
        self.graphics_view.translate(delta.x(), delta.y())