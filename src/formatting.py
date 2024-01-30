from __future__ import annotations
from typing import ForwardRef

import locale
import datetime

import openpyxl


def format_price(price: str) -> str:
    """Returns price without "do negocjacji"."""
    if "do negocjacji" in price:
        price = price.replace("do negocjacji", "")
    return price


def format_location_date(location_date: str) -> tuple[str, str]:
    """Returns tuple of location and date. Converts date to Polish format if it's today."""
    location, date = location_date.split(" - ")[:2]
    if "dzisiaj" in date.lower():
        locale.setlocale(locale.LC_ALL, 'pl_PL')
        formatted_date = datetime.datetime.now().strftime("%d %B %Y")
        date = formatted_date
    return location, date


def create_hyperlink(url, name):
    """Returns a hyperlink to the given URL with the given name."""
    return f'=HYPERLINK("{url}", "{name}")'


Scraper = ForwardRef("Scraper")


def apply_hyperlinking(scraper_inst: Scraper, columns_to_hyperlink: set[str]) -> None:
    """Applies hyperlinking to the given columns in the data frames that have been scrapped by the given Scraper instance
    For instance the photo and item_url columns may get hyperlinked."""

    for key, df in scraper_inst.data_frames.items():
        for column_name in columns_to_hyperlink:
            if column_name in df.columns:
                df[column_name] = df.apply(
                    lambda row: create_hyperlink(row[column_name], f'{column_name}, click to access'), axis=1)
            else:
                print(f"Column {column_name} not found in {key} data frame.")


def format_columns(sheet: openpyxl.worksheet.worksheet.Worksheet):
    """Formats column widths to fit the longest text in the column."""
    hyperlinked_columns = {"item_url", "photo"}
    hyperlinked_columns_width = 25
    for column_cells in sheet.columns:
        column_title = column_cells[0].value
        if column_title is not None:
            length = max(
                len(str(cell.value)) if column_title not in hyperlinked_columns else hyperlinked_columns_width for cell
                in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = length
