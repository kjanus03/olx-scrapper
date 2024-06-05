from typing import Optional

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog, \
    QWidget
from src.Exporting.ExportManager import ExportFormat


class ExportDialog(QDialog):
    """Dialog for exporting data to a file."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the dialog.
        :param parent: Parent widget of the dialog.
        """
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        self.setModal(True)
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the UI of the dialog.
        :return:
        """
        layout = QVBoxLayout(self)

        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems([export_format.name for export_format in ExportFormat])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # Save path selection
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Save Path:")
        self.path_line_edit = QLineEdit()
        self.path_button = QPushButton("Browse...")
        self.path_button.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_line_edit)
        path_layout.addWidget(self.path_button)
        layout.addLayout(path_layout)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_save_path(self) -> None:
        """
        Browse for a directory to save the file.
        :return:
        """
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.path_line_edit.setText(directory)

    def get_export_details(self) -> tuple[str, str]:
        """
        Get the export format and save path.
        :return:
        """
        return self.format_combo.currentText(), self.path_line_edit.text()
