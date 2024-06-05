from enum import Enum
from fpdf import FPDF
import pandas as pd
import json
import dicttoxml
from src.Exporting.SpreadsheetManager import SpreadsheetManager


class ExportFormat(Enum):
    """Enum class for supported export formats."""
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"


class ExportManager:
    """Class for exporting data to various formats."""
    def __init__(self, export_format: ExportFormat, output_config: dict, data_frames: dict[str, pd.DataFrame]):
        """
        Initializes the ExportManager with the specified export format, output configuration, and data frames.
        :param export_format: The format to export the data to
        :param output_config: The configuration for the output file
        :param data_frames: The data frames to export
        """

        if not isinstance(export_format, ExportFormat):
            raise TypeError("export_format must be an instance of ExportFormat Enum")
        if not isinstance(output_config, dict):
            raise TypeError("output_config must be a dictionary")
        if not isinstance(data_frames, dict):
            raise TypeError("data_frames must be a dictionary")
        self.export_format = export_format
        self.output_config = output_config
        self.data_frames = data_frames
        self.output_filename = output_config['filename']

    def export_data(self) -> None:
        """
        Exports the data to the specified format.
        :return:
        """

        if self.export_format == ExportFormat.EXCEL:
            self._export_to_excel()
        elif self.export_format == ExportFormat.CSV:
            self._export_to_csv()
        elif self.export_format == ExportFormat.PDF:
            self._export_to_pdf()
        elif self.export_format == ExportFormat.JSON:
            self._export_to_json()
        elif self.export_format == ExportFormat.XML:
            self._export_to_xml()
        else:
            raise ValueError(f"Unsupported export format: {self.export_format}")

    def _export_to_excel(self) -> None:
        """
        Exports the data to an Excel file.
        :return:
        """
        spreadsheet_manager = SpreadsheetManager(self.data_frames, self.output_filename)
        spreadsheet_manager.initialize_spreadsheets(set(self.output_config['hyperlinked_columns']),
                                                    self.output_config['format_column_widths'])

    def _export_to_csv(self) -> None:
        """
        Exports the data to a CSV file.
        :return:
        """
        for key, df in self.data_frames.items():
            filename = f"{self.output_filename}_{key}.csv"
            df.to_csv(filename, index=False)

    def _export_to_pdf(self) -> None:
        """
        Exports the data to a PDF file.
        :return:
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            pdf.set_font('DejaVu', '', 12)
            pdf.set_auto_page_break(auto=True, margin=15)

            col_widths = {}
            for key, df in self.data_frames.items():
                for col in df.columns:
                    col_widths[col] = pdf.get_string_width(col) + 4
                    for val in df[col]:
                        col_width = pdf.get_string_width(str(val)) + 4
                        if col_width > col_widths[col]:
                            col_widths[col] = col_width

                pdf.add_page()
                pdf.set_font('DejaVu', '', 12)
                pdf.cell(200, 10, txt=str(key), ln=True, align='C')

                for col in df.columns:
                    pdf.cell(col_widths[col], 10, col, border=1)
                pdf.ln()

                for index, row in df.iterrows():
                    if pdf.get_y() > pdf.page_break_trigger - 20:
                        pdf.add_page()
                        for col in df.columns:
                            pdf.cell(col_widths[col], 10, col, border=1)
                        pdf.ln()
                    for col in df.columns:
                        pdf.cell(col_widths[col], 10, str(row[col]), border=1)
                    pdf.ln()

            pdf_output_path = f"{self.output_filename}.pdf"
            pdf.output(pdf_output_path)
        except Exception as e:
            raise Exception(f"Error exporting to PDF: {e}")

    def _export_to_json(self) -> None:
        """
        Exports the data to a JSON file.
        :return:
        """
        json_data = {key: df.to_dict(orient='records') for key, df in self.data_frames.items()}
        with open(f"{self.output_filename}.json", 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        print(f"JSON exported successfully to {self.output_filename}.json")

    def _export_to_xml(self) -> None:
        """
        Exports the data to an XML file.
        :return:
        """
        xml_data = {key: df.to_dict(orient='records') for key, df in self.data_frames.items()}
        xml_bytes = dicttoxml.dicttoxml(xml_data, custom_root='data', attr_type=False)
        with open(f"{self.output_filename}.xml", 'wb') as xml_file:
            xml_file.write(xml_bytes)
        print(f"XML exported successfully to {self.output_filename}.xml")
