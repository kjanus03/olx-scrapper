from PyQt5.QtCore import QUrl, QEvent, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class ClickableDelegate(QStyledItemDelegate):
    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """
        This method is called when an event is triggered on a cell in the table.
        :param event: The event that was triggered
        :param model: The model that contains the data
        :param option: The style options for the cell
        :param index: The index of the cell in the model
        :return: True if the event was handled, False otherwise
        """
        if event.type() == QEvent.MouseButtonRelease:
            data = index.data()  # Get the data from the cell
            if data and data.startswith("http"):  # Check if the data is a URL
                QDesktopServices.openUrl(QUrl(data))  # Open the URL in a web browser
                return True
        return super().editorEvent(event, model, option, index)
