"""Main application window.

Architectural notes
-------------------
* Theming is applied at the **QApplication** level via
  `QApplication.setStyleSheet(...)`, so dialogs inherit the active theme
  automatically. Toggling the theme re-applies that single stylesheet and
  every open dialog updates live.
* The MainWindow owns the canonical `dark_mode` state. SettingsDialog reads
  it on open and emits `theme_changed(bool)` if the user toggles in there.
* Iconography flows through `IconProvider` so SVGs are tinted to match the
  current theme tokens. On theme switch the cache is cleared and nav icons
  are re-rendered.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests
from PyQt5.QtCore import (
    Qt, QPoint, QModelIndex, QProcess, QTimer, QPropertyAnimation, QEasingCurve,
    QSortFilterProxyModel, pyqtSignal
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QPushButton, QVBoxLayout, QWidget,
    QStackedWidget, QHBoxLayout, QLabel, QDialog, QTableView, QProgressBar,
    QMenu, QToolButton, QMessageBox, QFrame, QGraphicsOpacityEffect,
    QSizePolicy, QApplication, QTabWidget, QHeaderView, QStyledItemDelegate
)

from src.GUI.DataFrameModel import DataFrameModel
from src.GUI.Controller import Controller
from src.GUI.ExportDialog import ExportDialog
from src.GUI.ImageDialog import ImageDialog
from src.GUI.SettingsDialog import SettingsDialog
from src.GUI.ScrapingHistoryDialog import ScrapingHistoryDialog
from src.GUI.widgets import (
    icons, ToastManager, EmptyState, SearchBar, ToastKind,
    LinkChipDelegate, ThumbnailDelegate,
)


CONFIG_PATH = "src/Resources/config.json"
HISTORY_PATH = "src/Resources/scraping_history.json"
STYLESHEET_DARK = "src/GUI/stylesheets/modern_dark.qss"
STYLESHEET_LIGHT = "src/GUI/stylesheets/modern_light.qss"


# Token colors used when re-tinting icons / model palettes after theme swap.
DARK_TOKENS = {
    "text":       "#e9ecef",
    "text_mid":   "#c1c2c5",
    "text_low":   "#909296",
    "text_dim":   "#6c6f75",
    "accent":     "#a5b4fc",
    "accent_alt": "#5c7cfa",
    "price":      "#ffffff",
    "price_zero": "#6c6f75",
    "icon":       "#909296",
    "icon_active":"#a5b4fc",
    "empty":      "#373a40",
    "new_bg":     "#1a2e1a",
    "deal_fg":    "#51cf66",
}
LIGHT_TOKENS = {
    "text":       "#212529",
    "text_mid":   "#495057",
    "text_low":   "#6c757d",
    "text_dim":   "#adb5bd",
    "accent":     "#364fc7",
    "accent_alt": "#5c7cfa",
    "price":      "#0b0c0f",
    "price_zero": "#adb5bd",
    "icon":       "#6c757d",
    "icon_active":"#364fc7",
    "empty":      "#ced4da",
    "new_bg":     "#e6f9ec",
    "deal_fg":    "#2f9e44",
}


def reboot_application() -> None:
    """Reboots the application."""
    qApp.quit()
    QProcess.startDetached(sys.executable, sys.argv)


class NavButton(QToolButton):
    """A sidebar nav button. SVG icon left, label right. Driven by setChecked()."""

    ICON_SIZE = 18

    def __init__(self, label: str, icon_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.label = label
        self.icon_name = icon_name
        self.setText(label)
        self.setCheckable(True)
        self.setAutoExclusive(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setObjectName("NavButton")
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # Indented look — extra space between icon and text
        self.setStyleSheet("QToolButton#NavButton { padding-left: 14px; }")

    def apply_icon(self, color: str, active_color: str) -> None:
        """Re-render the SVG icon. Caller picks colors based on current theme."""
        from PyQt5.QtCore import QSize
        normal = icons.pixmap(self.icon_name, color=color, size=self.ICON_SIZE)
        active = icons.pixmap(self.icon_name, color=active_color, size=self.ICON_SIZE)
        ico = QIcon()
        ico.addPixmap(normal, QIcon.Normal, QIcon.Off)
        ico.addPixmap(active, QIcon.Normal, QIcon.On)
        ico.addPixmap(active, QIcon.Active, QIcon.On)
        self.setIcon(ico)
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))


class _StatusBarDelegate(QStyledItemDelegate):
    """Draws a 3-px accent stripe on the left edge of the Title cell for new/price-dropped rows.

    Using a custom delegate (rather than Qt.BackgroundRole) is necessary because
    QSS alternate-background-color overrides the model's BackgroundRole in Qt5.
    """

    _DEAL_COLOR = QColor("#51cf66")
    _NEW_COLOR  = QColor("#5c7cfa")

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        is_deal = bool(index.data(DataFrameModel.IsDealRole))
        is_new  = bool(index.data(DataFrameModel.IsNewRole))
        if not (is_deal or is_new):
            return
        color = self._DEAL_COLOR if is_deal else self._NEW_COLOR
        r = option.rect
        painter.save()
        painter.fillRect(r.x(), r.y() + 2, 3, r.height() - 4, color)
        painter.restore()


class _DataTableProxy(QSortFilterProxyModel):
    """Multi-column case-insensitive contains filter.

    Sorts by `DataFrameModel.SortRole` so numeric columns (Price) compare as
    integers instead of formatted display strings ("9 800 zł" lex-sorted).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(DataFrameModel.SortRole)
        self._needle = ""
        self._hide_accessories = True

    def set_needle(self, text: str) -> None:
        self._needle = text.strip().lower()
        self.invalidateFilter()

    def set_hide_accessories(self, hide: bool) -> None:
        if self._hide_accessories != hide:
            self._hide_accessories = hide
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        model = self.sourceModel()
        if model is None:
            return True
        if self._hide_accessories:
            idx = model.index(source_row, 0, source_parent)
            if idx.isValid() and idx.data(DataFrameModel.IsMatchRole) is False:
                return False
        if not self._needle:
            return True
        cols = model.columnCount()
        for c in range(cols):
            idx = model.index(source_row, c, source_parent)
            val = idx.data(Qt.DisplayRole)
            if val is None:
                continue
            if self._needle in str(val).lower():
                return True
        return False


class _DataTab(QWidget):
    """Single tab containing a search bar, data table and empty-state fallback."""

    def __init__(
        self,
        title: str,
        df_model: DataFrameModel,
        link_columns: List[int],
        photo_columns: List[int],
        link_delegate: LinkChipDelegate,
        thumb_delegate: ThumbnailDelegate,
        status_delegate: _StatusBarDelegate,
        on_context_menu,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.source_model = df_model
        self._status_delegate = status_delegate

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ---- header row ---------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        self.section_title = QLabel(title)
        self.section_title.setObjectName("SectionTitle")
        header.addWidget(self.section_title)

        self.section_count = QLabel()
        self.section_count.setObjectName("SectionCount")
        header.addWidget(self.section_count)

        self.section_median = QLabel()
        self.section_median.setObjectName("SectionCount")
        header.addWidget(self.section_median)
        header.addStretch(1)

        # Chip toggle for accessories. Wrapped in a FilterChipRow so the
        # existing chip styles (rounded pill, accent on :checked) apply.
        chip_row = QWidget()
        chip_row.setObjectName("FilterChipRow")
        chip_layout = QHBoxLayout(chip_row)
        chip_layout.setContentsMargins(0, 0, 0, 0)
        chip_layout.setSpacing(0)
        self.toggle_accessories_btn = QPushButton("Show accessories")
        self.toggle_accessories_btn.setCheckable(True)
        self.toggle_accessories_btn.setChecked(False)
        self.toggle_accessories_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_accessories_btn.setVisible(False)  # only shown when there's something to filter
        self.toggle_accessories_btn.clicked.connect(self._on_toggle_accessories)
        chip_layout.addWidget(self.toggle_accessories_btn)
        header.addWidget(chip_row)

        self.search_bar = SearchBar(placeholder="Filter rows…")
        self.search_bar.setMinimumWidth(220)
        self.search_bar.setMaximumWidth(320)
        header.addWidget(self.search_bar)

        layout.addLayout(header)

        # ---- stack: table | empty state ----------------------------------
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        # Table
        self.proxy = _DataTableProxy(self)
        self.proxy.setSourceModel(df_model)
        self.search_bar.text_changed.connect(self.proxy.set_needle)
        self.search_bar.text_changed.connect(self._refresh_count)

        self.table_view = QTableView()
        self.table_view.setObjectName("DataTable")
        self.table_view.setModel(self.proxy)
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setHighlightSections(False)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table_view.setShowGrid(False)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setMouseTracking(True)
        self.table_view.setWordWrap(False)
        self.table_view.verticalHeader().setDefaultSectionSize(60)

        for col in link_columns:
            self.table_view.setItemDelegateForColumn(col, link_delegate)
        for col in photo_columns:
            self.table_view.setItemDelegateForColumn(col, thumb_delegate)
        thumb_delegate.register_view(self.table_view)

        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            lambda pos, tv=self.table_view: on_context_menu(pos, tv)
        )

        self._auto_size_columns()
        self.stack.addWidget(self.table_view)

        # Empty state
        self.empty_state = EmptyState(
            title="No matches",
            subtitle="No rows match your search filter.",
            icon_name="search",
        )
        self.stack.addWidget(self.empty_state)

        # Empty state for source 0-row
        self.zero_state = EmptyState(
            title="Nothing scraped yet",
            subtitle=(
                "OLX returned no listings for this search — "
                "try widening the city/distance or adjusting the query."
            ),
            icon_name="inbox",
        )
        self.stack.addWidget(self.zero_state)

        self._refresh_count()
        self._refresh_visible_state()
        self.proxy.layoutChanged.connect(self._refresh_visible_state)
        self.proxy.layoutChanged.connect(self._refresh_count)
        self.proxy.modelReset.connect(self._refresh_visible_state)
        self.proxy.modelReset.connect(self._refresh_count)

    # ------------------------------------------------------------------
    def _auto_size_columns(self) -> None:
        header = self.table_view.horizontalHeader()
        cols = [str(self.source_model.headerData(c, Qt.Horizontal, Qt.DisplayRole))
                for c in range(self.proxy.columnCount())]
        # Defaults sized to content, capped to keep one column from dominating.
        self.table_view.resizeColumnsToContents()
        for col in range(self.proxy.columnCount()):
            current = header.sectionSize(col)
            header.resizeSection(col, min(max(current, 80), 280))

        # Per-column overrides
        for i, name in enumerate(cols):
            if name == "Photo":
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                header.resizeSection(i, 78)
            elif name == "Item URL":
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                header.resizeSection(i, 116)
            elif name == "Price":
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                header.resizeSection(i, 130)
            elif name == "Date":
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            elif name == "Location":
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            elif name == "Title":
                header.setSectionResizeMode(i, QHeaderView.Stretch)
                self.table_view.setItemDelegateForColumn(i, self._status_delegate)
            elif name in ("Is New", "Old Price", "Is Match"):
                self.table_view.setColumnHidden(i, True)

    def _refresh_count(self) -> None:
        total = self.source_model.rowCount()
        shown = self.proxy.rowCount()
        if shown == total:
            self.section_count.setText(f"·  {total} listing" + ("" if total == 1 else "s"))
        else:
            self.section_count.setText(f"·  {shown} of {total}")

        # Median price of matching (real product) listings
        median = self.source_model.median_match_price()
        if median > 0:
            self.section_median.setText(
                ("·  median " + f"{median:,} zł").replace(",", " ")
            )
        else:
            self.section_median.setText("")

        # Show the accessory toggle only when there's actually something to filter
        match_n = self.source_model.match_count()
        accessory_n = total - match_n
        if accessory_n > 0:
            self.toggle_accessories_btn.setVisible(True)
            checked = self.toggle_accessories_btn.isChecked()
            label = (
                f"Hide accessories ({accessory_n})"
                if checked
                else f"Show accessories ({accessory_n})"
            )
            self.toggle_accessories_btn.setText(label)
        else:
            self.toggle_accessories_btn.setVisible(False)

    def _on_toggle_accessories(self, checked: bool) -> None:
        self.proxy.set_hide_accessories(not checked)
        self._refresh_count()

    def _refresh_visible_state(self) -> None:
        if self.source_model.rowCount() == 0:
            self.stack.setCurrentWidget(self.zero_state)
        elif self.proxy.rowCount() == 0:
            self.stack.setCurrentWidget(self.empty_state)
        else:
            self.stack.setCurrentWidget(self.table_view)


class MainWindow(QMainWindow):
    """Main window of the application."""

    theme_changed = pyqtSignal(bool)

    def __init__(self, title: str, width: int, height: int, controller: Controller) -> None:
        super().__init__()
        self.controller = controller
        self.controller.progress_updated.connect(self.update_progress_bar)
        self.controller.scraping_done.connect(self.update_last_scrape_label)
        self.controller.scraping_done.connect(self.enable_data_buttons)
        self.controller.scraping_done.connect(self.handle_scraping_done)
        self.controller.scraping_failed.connect(self.show_scraping_error)

        # State -------------------------------------------------------------
        self._config = self._load_config()
        self.dark_mode: bool = self._config.get("gui_config", {}).get("dark_mode", True)
        self.has_data = False
        self.nav_buttons: List[NavButton] = []
        self._data_models: List[DataFrameModel] = []
        self._data_tabs: List[_DataTab] = []
        # Shared singleton delegates so the thumbnail cache is reused across tabs
        self._link_delegate = LinkChipDelegate(self)
        self._thumb_delegate = ThumbnailDelegate(on_open=self._open_image_for_index, parent=self)
        self._status_delegate = _StatusBarDelegate(self)

        # Build UI ----------------------------------------------------------
        self.init_ui(title, width, height)
        self.toast_manager = ToastManager(self.centralWidget())
        self.apply_theme()

    # ==================================================================
    # UI construction
    # ==================================================================
    def init_ui(self, title: str, width: int, height: int) -> None:
        self.setWindowIcon(QIcon("src/GUI/icons/scraper_icon.png"))
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        self.setup_menu()

        root = QWidget(self)
        root.setObjectName("Root")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        body = QWidget()
        body.setObjectName("Body")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        body_layout.addWidget(self._build_sidebar())
        body_layout.addWidget(self._build_content_area(), 1)

        root_layout.addWidget(body, 1)
        root_layout.addWidget(self._build_status_bar())

        self.show_home_page()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        self.brand_icon = QLabel()
        self.brand_icon.setFixedSize(22, 22)
        brand_row.addWidget(self.brand_icon)
        brand_text = QLabel("olx-scrapper")
        brand_text.setObjectName("Brand")
        brand_row.addWidget(brand_text)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)

        subtitle = QLabel("MARKETPLACE SCRAPER")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        section_main = QLabel("WORKSPACE")
        section_main.setObjectName("NavSectionLabel")
        layout.addWidget(section_main)

        self.nav_home = self._add_nav(layout, "Home", "home", self.show_home_page)
        self.nav_scrape = self._add_nav(layout, "Scrape Data", "play", self.start_scraping)
        self.nav_data = self._add_nav(layout, "View Data", "table", self.show_data_page)
        self.nav_data.setEnabled(False)
        self.nav_export = self._add_nav(layout, "Export", "download", self.show_export_dialog)
        self.nav_export.setEnabled(False)

        layout.addSpacing(16)
        section_admin = QLabel("MANAGE")
        section_admin.setObjectName("NavSectionLabel")
        layout.addWidget(section_admin)

        self.nav_queries = self._add_nav(
            layout, "Search Queries", "search", self.show_search_queries
        )
        self.nav_history = self._add_nav(
            layout, "History", "clock", self.show_scraping_history_dialog
        )

        layout.addStretch(1)

        self.nav_settings = self._add_nav(
            layout, "Settings", "settings", self.show_settings_dialog
        )

        self.theme_toggle = QToolButton()
        self.theme_toggle.setObjectName("ThemeToggle")
        self.theme_toggle.setCursor(Qt.PointingHandCursor)
        self.theme_toggle.setMinimumHeight(36)
        self.theme_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        self.theme_toggle.setStyleSheet("QToolButton#ThemeToggle { padding-left: 14px; }")
        layout.addWidget(self.theme_toggle)

        return sidebar

    def _add_nav(self, layout, label: str, icon_name: str, callback) -> NavButton:
        btn = NavButton(label, icon_name)
        btn.clicked.connect(callback)
        layout.addWidget(btn)
        self.nav_buttons.append(btn)
        return btn

    def _build_content_area(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("ContentWrapper")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(32, 24, 32, 16)
        wrapper_layout.setSpacing(16)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.page_title = QLabel("Welcome")
        self.page_title.setObjectName("PageTitle")
        title_col.addWidget(self.page_title)
        self.page_subtitle = QLabel("")
        self.page_subtitle.setObjectName("PageSubtitle")
        title_col.addWidget(self.page_subtitle)
        top_bar.addLayout(title_col, 1)

        self.scrape_again_btn = QPushButton("Scrape Again")
        self.scrape_again_btn.setObjectName("PrimaryButton")
        self.scrape_again_btn.setCursor(Qt.PointingHandCursor)
        self.scrape_again_btn.clicked.connect(self.start_scraping)
        self.scrape_again_btn.setVisible(False)
        top_bar.addWidget(self.scrape_again_btn)

        self.export_btn = QPushButton("Export…")
        self.export_btn.setObjectName("SecondaryButton")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self.show_export_dialog)
        self.export_btn.setVisible(False)
        top_bar.addWidget(self.export_btn)

        wrapper_layout.addLayout(top_bar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        wrapper_layout.addWidget(self.content_stack, 1)

        # Page 0 — home
        self.home_page = self._build_home_page()
        self.content_stack.addWidget(self.home_page)

        # Page 1 — data view (tabs)
        self.data_page = QWidget()
        data_layout = QVBoxLayout(self.data_page)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.setSpacing(8)
        self.data_tabs = QTabWidget()
        self.data_tabs.setObjectName("DataTabs")
        self.data_tabs.setDocumentMode(True)
        self.data_tabs.setTabsClosable(False)
        self.data_tabs.setMovable(False)
        data_layout.addWidget(self.data_tabs, 1)
        self.content_stack.addWidget(self.data_page)

        return wrapper

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 24, 0, 0)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Hero
        hero = QFrame()
        hero.setObjectName("HomeCard")
        hero.setMaximumWidth(640)
        hero.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(32, 32, 32, 32)
        hero_l.setSpacing(8)
        hero_l.setAlignment(Qt.AlignCenter)

        self.home_icon_label = QLabel()
        self.home_icon_label.setObjectName("HomeIcon")
        self.home_icon_label.setAlignment(Qt.AlignCenter)
        self.home_icon_label.setFixedSize(72, 72)
        hero_l.addWidget(self.home_icon_label, 0, Qt.AlignCenter)

        heading = QLabel("Ready to scrape")
        heading.setObjectName("HomeHeading")
        heading.setAlignment(Qt.AlignCenter)
        hero_l.addWidget(heading)

        sub = QLabel(
            'Click <b>Scrape Data</b> in the sidebar to fetch fresh listings, '
            'or open <b>Search Queries</b> to edit your watchlist.'
        )
        sub.setObjectName("HomeSub")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setMaximumWidth(440)
        sub.setTextFormat(Qt.RichText)
        hero_l.addWidget(sub, 0, Qt.AlignCenter)

        hero_l.addSpacing(12)

        cta_row = QHBoxLayout()
        cta_row.setSpacing(8)
        cta_row.setAlignment(Qt.AlignCenter)
        cta_primary = QPushButton("Start Scrape")
        cta_primary.setObjectName("PrimaryButton")
        cta_primary.setCursor(Qt.PointingHandCursor)
        cta_primary.clicked.connect(self.start_scraping)
        cta_secondary = QPushButton("Manage Queries")
        cta_secondary.setObjectName("SecondaryButton")
        cta_secondary.setCursor(Qt.PointingHandCursor)
        cta_secondary.clicked.connect(self.show_search_queries)
        cta_row.addWidget(cta_primary)
        cta_row.addWidget(cta_secondary)
        hero_l.addLayout(cta_row)

        layout.addWidget(hero, 0, Qt.AlignHCenter)

        # Stats card
        stats = QFrame()
        stats.setObjectName("HomeCard")
        stats.setMaximumWidth(640)
        stats.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(32, 24, 32, 24)
        stats_layout.setSpacing(48)
        stats_layout.setAlignment(Qt.AlignCenter)

        n_queries = len(self._config.get("search_queries", []))
        self.home_stat_queries = self._make_stat(str(n_queries), "WATCHED QUERIES")
        self.home_stat_last = self._make_stat("—", "LAST SCRAPE")
        self.home_stat_runs = self._make_stat(str(self._scrape_count()), "TOTAL RUNS")

        stats_layout.addLayout(self.home_stat_queries)
        stats_layout.addLayout(self.home_stat_last)
        stats_layout.addLayout(self.home_stat_runs)

        layout.addWidget(stats, 0, Qt.AlignHCenter)
        layout.addStretch(1)

        return page

    def _make_stat(self, value: str, label: str) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setAlignment(Qt.AlignCenter)
        v = QLabel(value)
        v.setObjectName("HomeStatValue")
        v.setAlignment(Qt.AlignCenter)
        col.addWidget(v)
        l = QLabel(label)
        l.setObjectName("HomeStatLabel")
        l.setAlignment(Qt.AlignCenter)
        col.addWidget(l)
        # store value label so we can update later
        col.value_label = v  # type: ignore[attr-defined]
        return col

    def _scrape_count(self) -> int:
        try:
            with open(HISTORY_PATH, "r") as f:
                return len(json.load(f) or [])
        except Exception:
            return 0

    def _build_status_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("AppStatusBar")
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(14)

        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("StatusDot")
        layout.addWidget(self.status_dot)

        self.last_scrape_label = QLabel()
        self.last_scrape_label.setObjectName("StatusLabel")
        self.update_last_scrape_label()
        layout.addWidget(self.last_scrape_label)

        layout.addStretch(1)

        self.scraping_label = QLabel("Scraping…")
        self.scraping_label.setObjectName("StatusLabel")
        self.scraping_label.setVisible(False)
        layout.addWidget(self.scraping_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("Progress")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(280)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_text = QLabel()
        self.progress_text.setObjectName("ProgressText")
        self.progress_text.setVisible(False)
        layout.addWidget(self.progress_text)

        return bar

    # ==================================================================
    # Theming
    # ==================================================================
    def apply_theme(self) -> None:
        path = STYLESHEET_DARK if self.dark_mode else STYLESHEET_LIGHT
        try:
            with open(path) as f:
                qss = f.read()
        except FileNotFoundError:
            print(f"[theme] stylesheet not found at {path}")
            qss = ""
        QApplication.instance().setStyleSheet(qss)

        # Re-tint icons
        icons.clear_cache()
        tokens = DARK_TOKENS if self.dark_mode else LIGHT_TOKENS
        for btn in self.nav_buttons:
            btn.apply_icon(color=tokens["icon"], active_color=tokens["icon_active"])
        # Brand storefront icon (uses accent gradient origin)
        self.brand_icon.setPixmap(icons.pixmap("shopping-bag", color=tokens["accent_alt"], size=22))
        # Theme toggle icon + label
        self._refresh_theme_toggle()
        # Home hero icon
        if hasattr(self, "home_icon_label"):
            self.home_icon_label.setPixmap(
                icons.pixmap("shopping-bag", color=tokens["accent_alt"], size=72)
            )
        # Top-bar action buttons icon (export icon for the export button)
        if hasattr(self, "export_btn"):
            self.export_btn.setIcon(icons.icon("download", color=tokens["text_mid"], size=14))
        if hasattr(self, "scrape_again_btn"):
            self.scrape_again_btn.setIcon(icons.icon("play", color="#ffffff", size=12))

        # Re-color all data models so cells match the theme
        palette = {
            "text":       tokens["text"],
            "text_mid":   tokens["text_mid"],
            "text_dim":   tokens["text_dim"],
            "accent":     tokens["accent"],
            "currency":   tokens["text_low"],
            "price":      tokens["price"],
            "price_zero": tokens["price_zero"],
            "new_bg":     tokens["new_bg"],
            "deal_fg":    tokens["deal_fg"],
        }
        for m in self._data_models:
            m.set_palette(palette)
        for tab in self._data_tabs:
            tab.empty_state.set_icon_color(tokens["empty"])
            tab.zero_state.set_icon_color(tokens["empty"])
            tab.search_bar.set_icon_color(tokens["text_dim"])

        self._refresh_delegate_palettes()
        self.theme_changed.emit(self.dark_mode)

    def _refresh_delegate_palettes(self) -> None:
        if self.dark_mode:
            self._link_delegate.set_palette({
                "chip_bg":     "#2d3142",
                "chip_text":   "#a5b4fc",
                "chip_border": "#2d3142",
                "selection":   "#2d3142",
            })
            self._thumb_delegate.set_palette({
                "placeholder_bg":     "#25262b",
                "placeholder_border": "#373a40",
                "placeholder_icon":   "#6c6f75",
                "selection":          "#2d3142",
            })
        else:
            self._link_delegate.set_palette({
                "chip_bg":     "#edf0ff",
                "chip_text":   "#364fc7",
                "chip_border": "#edf0ff",
                "selection":   "#edf0ff",
            })
            self._thumb_delegate.set_palette({
                "placeholder_bg":     "#f1f3f5",
                "placeholder_border": "#e3e5e8",
                "placeholder_icon":   "#adb5bd",
                "selection":          "#edf0ff",
            })

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        try:
            self._config["gui_config"]["dark_mode"] = self.dark_mode
            self._save_config()
        except Exception as e:
            print(f"[theme] failed to persist dark_mode: {e}")
        self.apply_theme()

    def _refresh_theme_toggle(self) -> None:
        tokens = DARK_TOKENS if self.dark_mode else LIGHT_TOKENS
        if self.dark_mode:
            self.theme_toggle.setText("  Light Mode")
            self.theme_toggle.setIcon(icons.icon("sun", color=tokens["icon"], size=16))
        else:
            self.theme_toggle.setText("  Dark Mode")
            self.theme_toggle.setIcon(icons.icon("moon", color=tokens["icon"], size=16))

    # ==================================================================
    # Config helpers
    # ==================================================================
    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"gui_config": {}, "search_queries": [], "output_config": {}}

    def _save_config(self) -> None:
        with open(CONFIG_PATH, "w") as f:
            json.dump(self._config, f, indent=4)

    # ==================================================================
    # Menu
    # ==================================================================
    def setup_menu(self) -> None:
        exit_act = QAction("&Exit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(qApp.quit)

        reboot_act = QAction("&Reboot", self)
        reboot_act.setShortcut("Ctrl+R")
        reboot_act.triggered.connect(reboot_application)

        view_history_act = QAction("&View Scraping History", self)
        view_history_act.triggered.connect(self.show_scraping_history_dialog)

        settings_act = QAction("&Settings", self)
        settings_act.setShortcut("Ctrl+,")
        settings_act.triggered.connect(self.show_settings_dialog)

        toggle_theme_act = QAction("Toggle &Theme", self)
        toggle_theme_act.setShortcut("Ctrl+T")
        toggle_theme_act.triggered.connect(self.toggle_theme)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(exit_act)
        file_menu.addAction(reboot_act)
        file_menu.addSeparator()
        file_menu.addAction(view_history_act)
        file_menu.addAction(settings_act)
        file_menu.addSeparator()
        file_menu.addAction(toggle_theme_act)

    # ==================================================================
    # Navigation
    # ==================================================================
    def _set_active_nav(self, btn: Optional[NavButton]) -> None:
        for b in self.nav_buttons:
            b.setChecked(b is btn)

    def show_home_page(self) -> None:
        self._set_active_nav(self.nav_home)
        self.page_title.setText("Welcome")
        self.page_subtitle.setText("Configure your scraper and run a fresh fetch when you're ready.")
        self.scrape_again_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.content_stack.setCurrentIndex(0)
        self._refresh_home_stats()
        self._fade_in(self.content_stack.currentWidget())

    def show_data_page(self) -> None:
        if not self.has_data:
            return
        self._set_active_nav(self.nav_data)
        self.page_title.setText("Scraped Data")
        n = self.data_tabs.count()
        self.page_subtitle.setText(
            f"{n} quer{'y' if n == 1 else 'ies'} · sortable, searchable, click links to open in browser."
        )
        self.scrape_again_btn.setVisible(True)
        self.export_btn.setVisible(True)
        self.content_stack.setCurrentIndex(1)
        self._fade_in(self.content_stack.currentWidget())

    def _refresh_home_stats(self) -> None:
        n = len(self._config.get("search_queries", []))
        self.home_stat_queries.value_label.setText(str(n))  # type: ignore[attr-defined]
        last = self.controller.scraper.last_scrape_date
        self.home_stat_last.value_label.setText(  # type: ignore[attr-defined]
            last.strftime("%b %d") if last else "—"
        )
        self.home_stat_runs.value_label.setText(str(self._scrape_count()))  # type: ignore[attr-defined]

    def _fade_in(self, widget: QWidget, duration: int = 220) -> None:
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    # ==================================================================
    # Scraping
    # ==================================================================
    def start_scraping(self) -> None:
        self._set_active_nav(self.nav_scrape)
        self.progress_bar.setVisible(True)
        self.progress_text.setVisible(True)
        self.scraping_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_text.setText("0%")
        QTimer.singleShot(0, self.controller.scrape_data)

    def update_progress_bar(self, value: float) -> None:
        v = int(value)
        self.progress_bar.setValue(v)
        self.progress_text.setText(f"{v}%")

    def handle_scraping_done(self) -> None:
        self.has_data = True
        self._populate_data_page()
        total_rows = sum(m.rowCount() for m in self._data_models)
        n_queries = len(self._data_models)
        new_count = 0
        deal_count = 0
        for df in self.controller.scraper.data_frames.values():
            if df.empty:
                continue
            if "Is New" in df.columns:
                new_count += int(df["Is New"].sum())
            if "Old Price" in df.columns:
                deal_count += int((df["Old Price"] > 0).sum())
        self.show_data_page()
        QTimer.singleShot(900, self._hide_progress)
        body = (
            f"{total_rows} listing{'s' if total_rows != 1 else ''} across "
            f"{n_queries} quer{'ies' if n_queries != 1 else 'y'}"
        )
        if new_count:
            body += f"  ·  {new_count} new"
        if deal_count:
            body += f"  ·  {deal_count} price drop{'s' if deal_count != 1 else ''}"
        self.toast_manager.success("Scrape complete", body + ".")

    def _hide_progress(self) -> None:
        self.progress_bar.setVisible(False)
        self.progress_text.setVisible(False)
        self.scraping_label.setVisible(False)

    def _populate_data_page(self) -> None:
        # Clear existing tabs
        while self.data_tabs.count():
            w = self.data_tabs.widget(0)
            self.data_tabs.removeTab(0)
            w.deleteLater()
        self._data_models = []
        self._data_tabs = []

        for title, df in self.controller.scraper.data_frames.items():
            model = DataFrameModel(df)
            self._data_models.append(model)

            link_cols, photo_cols = self._special_column_indices(df)
            tab = _DataTab(
                title=title,
                df_model=model,
                link_columns=link_cols,
                photo_columns=photo_cols,
                link_delegate=self._link_delegate,
                thumb_delegate=self._thumb_delegate,
                status_delegate=self._status_delegate,
                on_context_menu=self.show_context_menu,
            )
            self._data_tabs.append(tab)
            # Tab label: just the item query (first segment of "query - city - dist").
            # The full title is shown in the section header and tooltip.
            parts = [p.strip() for p in title.split(" - ")]
            short = parts[0] if parts else title
            if len(short) > 28:
                short = short[:26] + "…"
            self.data_tabs.addTab(tab, short)
            self.data_tabs.setTabToolTip(self.data_tabs.count() - 1, title)

        # Apply current theme palette to fresh models
        tokens = DARK_TOKENS if self.dark_mode else LIGHT_TOKENS
        palette = {
            "text":       tokens["text"],
            "text_mid":   tokens["text_mid"],
            "text_dim":   tokens["text_dim"],
            "accent":     tokens["accent"],
            "currency":   tokens["text_low"],
            "price":      tokens["price"],
            "price_zero": tokens["price_zero"],
            "new_bg":     tokens["new_bg"],
            "deal_fg":    tokens["deal_fg"],
        }
        for m in self._data_models:
            m.set_palette(palette)
        for tab in self._data_tabs:
            tab.empty_state.set_icon_color(tokens["empty"])
            tab.zero_state.set_icon_color(tokens["empty"])
            tab.search_bar.set_icon_color(tokens["text_dim"])

    @staticmethod
    def _special_column_indices(df) -> Tuple[List[int], List[int]]:
        """Return (link_cols, photo_cols) by name lookup."""
        link_cols: List[int] = []
        photo_cols: List[int] = []
        try:
            for i, col in enumerate(df.columns):
                name = str(col)
                if name == "Item URL":
                    link_cols.append(i)
                elif name == "Photo":
                    photo_cols.append(i)
        except Exception:
            pass
        return link_cols, photo_cols

    def enable_data_buttons(self) -> None:
        self.nav_data.setEnabled(True)
        self.nav_export.setEnabled(True)

    # ==================================================================
    # Dialogs
    # ==================================================================
    def show_export_dialog(self) -> None:
        if not self.has_data:
            self.toast_manager.info("Nothing to export", "Run a scrape first.")
            return
        dlg = ExportDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            export_format, save_path = dlg.get_export_details()
            if not save_path:
                self.toast_manager.error("Export failed", "No save path provided.")
                return
            try:
                self.controller.export_data(export_format.lower(), save_path)
                self.toast_manager.success(
                    "Export complete",
                    f"{export_format} written to {save_path}",
                )
            except Exception as e:
                self.toast_manager.error("Export failed", str(e))

    def show_settings_dialog(self) -> None:
        dlg = SettingsDialog(
            config_path=CONFIG_PATH,
            current_dark_mode=self.dark_mode,
            parent=self,
        )
        dlg.theme_changed.connect(self._on_settings_theme_change)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec_()

    def _on_settings_theme_change(self, dark: bool) -> None:
        if dark != self.dark_mode:
            self.dark_mode = dark
            self.apply_theme()

    def _on_settings_saved(self) -> None:
        self._config = self._load_config()
        self.toast_manager.success(
            "Settings saved",
            "Restart the app to apply font size, width and height changes.",
        )

    def show_search_queries(self) -> None:
        self._set_active_nav(self.nav_queries)
        from src.GUI.SearchQueriesDialog import SearchQueriesDialog
        dlg = SearchQueriesDialog(config_path=CONFIG_PATH, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.controller.scraper.update_url_list(dlg.config_data)
            self._config = self._load_config()
            self._refresh_home_stats()
            self.toast_manager.success(
                "Queries updated",
                f"{len(dlg.config_data.get('search_queries', []))} queries saved.",
            )

    def show_scraping_history_dialog(self) -> None:
        self._set_active_nav(self.nav_history)
        dlg = ScrapingHistoryDialog(HISTORY_PATH, self)
        dlg.exec_()

    def _open_image_for_index(self, index: QModelIndex) -> None:
        """Click handler bound to the ThumbnailDelegate."""
        self.show_image(index)

    def show_image(self, index: QModelIndex) -> None:
        # `index` here is from a proxy/source — find the photo via column name
        model = index.model()
        # Resolve to source dataframe model so we can look up the Photo column
        source_model = model
        proxy_index = index
        if isinstance(model, QSortFilterProxyModel):
            proxy_index = model.mapToSource(index)
            source_model = model.sourceModel()
        if not isinstance(source_model, DataFrameModel):
            QMessageBox.warning(self, "No Image", "No image URL found.")
            return
        df = source_model.data_frame()
        try:
            row = proxy_index.row()
            photo_col = list(df.columns).index("Photo")
            image_url = str(df.iloc[row, photo_col])
        except (ValueError, IndexError):
            QMessageBox.warning(self, "No Image", "No image URL found.")
            return
        if not image_url or image_url == "nan":
            QMessageBox.warning(self, "No Image", "No image URL on this row.")
            return
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            ImageDialog(self, pixmap).exec_()
        except Exception as e:
            self.toast_manager.error("Could not load image", str(e))

    def show_context_menu(self, position: QPoint, table_view: QTableView) -> None:
        indexes = table_view.selectedIndexes()
        if not indexes:
            return
        menu = QMenu(self)
        show_image_action = QAction("Show Image", self)
        show_image_action.triggered.connect(lambda: self.show_image(indexes[0]))
        menu.addAction(show_image_action)
        delete_row_action = QAction("Delete Item", self)
        delete_row_action.triggered.connect(lambda: self.delete_row(indexes[0]))
        menu.addAction(delete_row_action)
        menu.exec_(table_view.viewport().mapToGlobal(position))

    def delete_row(self, index: QModelIndex) -> None:
        model = index.model()
        if isinstance(model, QSortFilterProxyModel):
            src_idx = model.mapToSource(index)
            model.sourceModel().removeRow(src_idx.row())
        else:
            model.removeRow(index.row())

    # ==================================================================
    # Status updates
    # ==================================================================
    def update_last_scrape_label(self) -> None:
        last = self.controller.scraper.last_scrape_date
        if last:
            self.last_scrape_label.setText(
                f"Last scrape  ·  {last.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            self.last_scrape_label.setText("Last scrape  ·  Never")
        if hasattr(self, "home_stat_last"):
            self._refresh_home_stats()

    def show_scraping_error(self, message: str) -> None:
        self._hide_progress()
        self.toast_manager.error("Scraping failed", message)
