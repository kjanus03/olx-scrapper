from enum import Enum
from SpreadsheetManager import SpreadsheetManager

import pandas as pd


class ExportFormat(Enum):
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"


class ExportManager:
    def __init__(self, export_format: ExportFormat, output_config: dict, data_frames: pd.Series):
        if not isinstance(export_format, ExportFormat):
            raise TypeError("export_format must be an instance of ExportFormat Enum")
        if not isinstance(output_config, dict):
            raise TypeError("output_config must be a dictionary")
        if not isinstance(data_frames, pd.Series):
            raise TypeError("data_frames must be a pandas Series")
        self.export_format = export_format
        self.output_config = output_config
        self.data_frames = data_frames
        self.output_filename = output_config['filename']

    def export_data(self) -> None:
        """Exports the data to the specified format."""
        if self.export_format == ExportFormat.EXCEL:
            self._export_to_excel()
        elif self.export_format == ExportFormat.CSV:
            self._export_to_csv()
        elif self.export_format == ExportFormat.PDF:
            self._export_to_pdf()
        else:
            raise ValueError(f"Unsupported export format: {self.export_format}")

    def _export_to_excel(self) -> None:
        """Exports the data to an Excel file."""
        spreadsheet_manager = SpreadsheetManager(self.data_frames, self.output_filename)
        spreadsheet_manager.initialize_spreadsheets(set(self.output_config['hyperlinked_columns']),
                                                    self.output_config['format_column_widths'])

    # TODO: Implement the export to PDF functionality.
    def _export_to_csv(self) -> None:
        pass

    # TODO: Implement the export to PDF functionality.
    def _export_to_pdf(self) -> None:
        pass

