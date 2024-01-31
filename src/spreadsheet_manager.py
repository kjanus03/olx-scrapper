import openpyxl
import pandas as pd
from formatting import create_hyperlink


class SpreadsheetManager:
    def __init__(self, data_frames: pd.Series(dtype=object), filename: str):
        self.data_frames = data_frames
        self.filename = filename

    def initialize_spreadsheets(self, hyperlinked_columns: set[str], format_column_widths: bool = True) -> None:
        """Creates and formats an MS Excel file with the provided DataFrames."""
        self._create_spreadsheets()
        self._apply_hyperlinking(hyperlinked_columns)
        if format_column_widths:
            self._format_excel_columns()

    def _create_spreadsheets(self) -> None:
        """Creates an MS Excel file with the scraped DataFrames."""
        with pd.ExcelWriter(f"../{self.filename}.xlsx", engine='openpyxl') as writer:
            for key, df in self.data_frames.items():
                df.to_excel(writer, sheet_name=key, index=False)

    def _format_excel_columns(self) -> None:
        """Formats the Excel columns."""
        workbook = openpyxl.load_workbook(f"../{self.filename}.xlsx")
        for sheet in workbook.worksheets:
            self._format_columns(sheet)
        workbook.save(f"../{self.filename}.xlsx")

    def _apply_hyperlinking(self, columns_to_hyperlink: set[str]) -> None:
        """Applies hyperlinking to the given columns in the data frames that have been scrapped
        by the given Scraper instance.
        For example the photo and item_url columns may get hyperlinked."""

        for key, df in self.data_frames.items():
            for column_name in columns_to_hyperlink:
                if column_name in df.columns:
                    df[column_name] = df.apply(
                        lambda row: create_hyperlink(row[column_name], f'{column_name}, click to access'), axis=1)
                else:
                    print(f"Column {column_name} not found in {key} data frame.")

    @staticmethod
    def _format_columns(sheet) -> None:
        """Formats column widths to fit the longest text in the column."""
        hyperlinked_columns = {"item_url", "photo"}
        hyperlinked_columns_width = 25
        for column_cells in sheet.columns:
            column_title = column_cells[0].value
            if column_title is not None:
                column_width = max(
                    len(str(cell.value)) if column_title not in hyperlinked_columns else hyperlinked_columns_width for
                    cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = column_width
