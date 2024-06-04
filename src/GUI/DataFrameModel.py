from typing import Optional, Union

from PyQt5 import QtCore
import pandas as pd


class DataFrameModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df: Optional[pd.DataFrame] = pd.DataFrame(),
                 parent: Optional[QtCore.QAbstractTableModel] = None) -> None:
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df
        self._original_dataframe = df.copy()
        self._last_sorted_column: Optional[int] = None
        self._sort_order: Optional[QtCore.Qt.SortOrder] = None

    def setDataFrame(self, dataframe: pd.DataFrame) -> None:
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self._original_dataframe = dataframe.copy()
        self._last_sorted_column = None
        self._sort_order = None
        self.endResetModel()

    def dataFrame(self) -> pd.DataFrame:
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole) -> Union[
        str, QtCore.QVariant]:
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Union[str, QtCore.QVariant]:
        if not index.isValid() or not (0 <= index.row() < self.rowCount() and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()

        val = self._dataframe.iloc[index.row(), index.column()]

        if role == QtCore.Qt.DisplayRole:
            if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://") or val.startswith("/app")):
                return val  # For simplicity, just return the URL. Custom delegate will handle it
            return str(val)
        elif role == DataFrameModel.ValueRole:
            return val
        elif role == DataFrameModel.DtypeRole:
            return self._dataframe.dtypes[index.column()]
        return QtCore.QVariant()

    def sort(self, column: int, order: Optional[QtCore.Qt.SortOrder] = QtCore.Qt.AscendingOrder) -> None:
        colname = self._dataframe.columns[column]

        # Determine sorting order
        if self._last_sorted_column == column:
            if self._sort_order == QtCore.Qt.AscendingOrder:
                order = QtCore.Qt.DescendingOrder
            elif self._sort_order == QtCore.Qt.DescendingOrder:
                self.reset_sorting()
                self._last_sorted_column = None
                self._sort_order = None
                return
            else:
                order = QtCore.Qt.AscendingOrder
        else:
            order = QtCore.Qt.AscendingOrder

        self._last_sorted_column = column
        self._sort_order = order

        self.layoutAboutToBeChanged.emit()
        self._dataframe.sort_values(by=colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
        self.layoutChanged.emit()

    def reset_sorting(self) -> None:
        self.layoutAboutToBeChanged.emit()
        self._dataframe = self._original_dataframe.copy()
        self.layoutChanged.emit()

    def roleNames(self) -> dict:
        roles = {QtCore.Qt.DisplayRole: b'display', DataFrameModel.DtypeRole: b'dtype',
                 DataFrameModel.ValueRole: b'value'}
        return roles
