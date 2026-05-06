from typing import Optional, Union, Dict

from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
import pandas as pd


# Default palette mirrors the dark theme. MainWindow swaps it for light.
_DARK_PALETTE = {
    "text":       QColor("#e9ecef"),
    "text_mid":   QColor("#c1c2c5"),
    "text_dim":   QColor("#6c6f75"),
    "accent":     QColor("#a5b4fc"),
    "currency":   QColor("#909296"),
    "price":      QColor("#ffffff"),
    "price_zero": QColor("#6c6f75"),
    "new_bg":     QColor("#1a2e1a"),
    "deal_fg":    QColor("#51cf66"),
}


_LINK_COLUMNS = {"Item URL", "Photo"}
_RIGHT_ALIGN_COLUMNS = {"Price"}
_MUTED_COLUMNS = {"Date"}


class DataFrameModel(QtCore.QAbstractTableModel):
    """Pandas DataFrame -> Qt model with column-aware rendering."""

    DtypeRole   = QtCore.Qt.UserRole + 1000
    ValueRole   = QtCore.Qt.UserRole + 1001
    SortRole    = QtCore.Qt.UserRole + 1002
    IsNewRole   = QtCore.Qt.UserRole + 1003
    IsDealRole  = QtCore.Qt.UserRole + 1004
    IsMatchRole = QtCore.Qt.UserRole + 1005

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        if df is None:
            df = pd.DataFrame()
        df = self._coerce_dtypes(df)
        self._dataframe = df
        self._original_dataframe = df.copy()
        self._last_sorted_column: Optional[int] = None
        self._sort_order: Optional[Qt.SortOrder] = None
        self._palette: Dict[str, QColor] = dict(_DARK_PALETTE)

    @staticmethod
    def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure numeric columns have a numeric dtype so sorts are numeric."""
        if "Price" in df.columns:
            df = df.copy()
            df["Price"] = (
                pd.to_numeric(df["Price"], errors="coerce")
                .fillna(0)
                .astype("int64")
            )
        return df

    # ---------------- Theming ----------------------------------------------
    def set_palette(self, palette: Dict[str, str]) -> None:
        """Update foreground colors for muted/accent/price cells.

        The dict values may be QColor or hex strings.
        """
        for k, v in palette.items():
            self._palette[k] = QColor(v) if not isinstance(v, QColor) else v
        if self.rowCount() > 0:
            top = self.index(0, 0)
            bot = self.index(self.rowCount() - 1, max(0, self.columnCount() - 1))
            self.dataChanged.emit(top, bot, [Qt.ForegroundRole])

    # ---------------- Data ops ---------------------------------------------
    def set_data_frame(self, dataframe: pd.DataFrame) -> None:
        self.beginResetModel()
        coerced = self._coerce_dtypes(dataframe)
        self._dataframe = coerced.copy()
        self._original_dataframe = coerced.copy()
        self._last_sorted_column = None
        self._sort_order = None
        self.endResetModel()

    def data_frame(self) -> pd.DataFrame:
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=data_frame, fset=set_data_frame)

    # ---------------- Qt model interface -----------------------------------
    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.DisplayRole,
    ) -> Union[str, QtCore.QVariant]:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if 0 <= section < len(self._dataframe.columns):
                    return str(self._dataframe.columns[section])
            else:
                if 0 <= section < len(self._dataframe.index):
                    return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def _column_name(self, col: int) -> str:
        if 0 <= col < len(self._dataframe.columns):
            return str(self._dataframe.columns[col])
        return ""

    def _old_price_for_row(self, row: int) -> int:
        if "Old Price" not in self._dataframe.columns:
            return 0
        try:
            return int(self._dataframe.iloc[row]["Old Price"])
        except (TypeError, ValueError, IndexError):
            return 0

    def _is_match_for_row(self, row: int) -> bool:
        if "Is Match" not in self._dataframe.columns:
            return True
        try:
            return bool(self._dataframe.iloc[row]["Is Match"])
        except (TypeError, ValueError, IndexError):
            return True

    def median_match_price(self) -> int:
        """Median price of rows that pass the relevance filter (Is Match=True).
        Returns 0 if no usable rows exist.
        """
        if "Price" not in self._dataframe.columns:
            return 0
        df = self._dataframe
        if "Is Match" in df.columns:
            df = df[df["Is Match"] == True]  # noqa: E712
        df = df[df["Price"] > 0]
        if df.empty:
            return 0
        try:
            return int(df["Price"].median())
        except Exception:
            return 0

    def match_count(self) -> int:
        if "Is Match" not in self._dataframe.columns:
            return self.rowCount()
        try:
            return int(self._dataframe["Is Match"].sum())
        except Exception:
            return self.rowCount()

    def data(
        self,
        index: QModelIndex,
        role: int = QtCore.Qt.DisplayRole,
    ) -> Union[str, QtCore.QVariant]:
        if not index.isValid() or not (
            0 <= index.row() < self.rowCount() and 0 <= index.column() < self.columnCount()
        ):
            return QtCore.QVariant()

        col_name = self._column_name(index.column())
        val = self._dataframe.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if col_name == "Price":
                try:
                    n = int(val)
                except (TypeError, ValueError):
                    return str(val)
                if n <= 0:
                    return "—"
                label = f"{n:,} zł".replace(",", " ")
                if self._old_price_for_row(index.row()) > 0:
                    label += "  ↓"
                return label
            return str(val)

        if role == Qt.TextAlignmentRole:
            if col_name in _RIGHT_ALIGN_COLUMNS:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        if role == Qt.ForegroundRole:
            if col_name in _LINK_COLUMNS and isinstance(val, str) and val:
                return QBrush(self._palette["accent"])
            if col_name in _MUTED_COLUMNS:
                return QBrush(self._palette["text_dim"])
            if col_name == "Price":
                try:
                    n = int(val)
                    if n <= 0:
                        return QBrush(self._palette["price_zero"])
                    if self._old_price_for_row(index.row()) > 0:
                        return QBrush(self._palette.get("deal_fg", QColor("#51cf66")))
                    return QBrush(self._palette["price"])
                except (TypeError, ValueError):
                    return QBrush(self._palette["text"])
            return QBrush(self._palette["text"])

        if role == Qt.FontRole:
            if col_name == "Price":
                f = QFont()
                f.setWeight(QFont.DemiBold)
                return f
            if col_name in _LINK_COLUMNS:
                f = QFont()
                f.setUnderline(True)
                return f

        if role == Qt.BackgroundRole:
            if "Is New" in self._dataframe.columns:
                try:
                    if bool(self._dataframe.iloc[index.row()]["Is New"]):
                        return QBrush(self._palette.get("new_bg", QColor("#1a2e1a")))
                except Exception:
                    pass
            return QtCore.QVariant()

        if role == Qt.ToolTipRole:
            if col_name in _LINK_COLUMNS and isinstance(val, str) and val:
                return f"Click to open: {val}"
            if col_name == "Price":
                old = self._old_price_for_row(index.row())
                if old > 0:
                    try:
                        cur = int(val)
                        saved = old - cur
                        pct = int(saved / old * 100)
                        return f"Was: {old:,} zł  (↓ {saved:,} zł, -{pct}%)".replace(",", " ")
                    except (TypeError, ValueError):
                        pass

        if role == DataFrameModel.IsNewRole:
            if "Is New" in self._dataframe.columns:
                try:
                    return bool(self._dataframe.iloc[index.row()]["Is New"])
                except Exception:
                    pass
            return False

        if role == DataFrameModel.IsDealRole:
            return self._old_price_for_row(index.row()) > 0

        if role == DataFrameModel.IsMatchRole:
            return self._is_match_for_row(index.row())

        if role == DataFrameModel.ValueRole or role == DataFrameModel.SortRole:
            # Raw value — used by QSortFilterProxyModel for numeric sorting.
            if col_name == "Price":
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return 0
            return val
        if role == DataFrameModel.DtypeRole:
            return self._dataframe.dtypes[index.column()]
        return QtCore.QVariant()

    def sort(
        self,
        column: int,
        order: Optional[QtCore.Qt.SortOrder] = QtCore.Qt.AscendingOrder,
    ) -> None:
        if column < 0 or column >= self.columnCount():
            return
        colname = self._dataframe.columns[column]

        if self._last_sorted_column == column:
            if self._sort_order == Qt.AscendingOrder:
                order = Qt.DescendingOrder
            elif self._sort_order == Qt.DescendingOrder:
                self.reset_sorting()
                self._last_sorted_column = None
                self._sort_order = None
                return
            else:
                order = Qt.AscendingOrder
        else:
            order = Qt.AscendingOrder

        self._last_sorted_column = column
        self._sort_order = order

        self.layoutAboutToBeChanged.emit()
        self._dataframe.sort_values(
            by=colname,
            ascending=order == Qt.AscendingOrder,
            inplace=True,
            kind="mergesort",
        )
        self.layoutChanged.emit()

    def reset_sorting(self) -> None:
        self.layoutAboutToBeChanged.emit()
        self._dataframe = self._original_dataframe.copy()
        self.layoutChanged.emit()

    def roleNames(self) -> dict:
        return {
            Qt.DisplayRole: b"display",
            DataFrameModel.DtypeRole: b"dtype",
            DataFrameModel.ValueRole: b"value",
        }

    def removeRow(self, row: int, parent: Optional[QModelIndex] = QModelIndex()) -> bool:
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(parent, row, row)
            self._dataframe.drop(self._dataframe.index[row], inplace=True)
            self.endRemoveRows()
            return True
        return False
