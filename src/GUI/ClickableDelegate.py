from PyQt5.QtCore import QUrl, QEvent, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class ClickableDelegate(QStyledItemDelegate):
    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            data = index.data()  # Get the data from the cell
            if data and data.startswith("http"):  # Check if the data is a URL
                QDesktopServices.openUrl(QUrl(data))  # Open the URL in a web browser
                return True
        return super().editorEvent(event, model, option, index)
