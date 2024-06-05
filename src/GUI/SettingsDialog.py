from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox
import json
from src.Resources.input_validation import validate_filename, validate_page_limit, validate_dimension, validate_fontsize

class SettingsDialog(QDialog):
    def __init__(self, config_path: str, dark_mode: bool = False, parent=None) -> None:
        super(SettingsDialog, self).__init__(parent)
        self.config_path = config_path
        self.dark_mode = dark_mode
        self.load_config()
        self.init_ui()

        if self.dark_mode:
            self.apply_dark_mode()

    def load_config(self) -> None:
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

    def save_config(self) -> None:
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file, indent=4)

    def init_ui(self) -> None:
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)

        # Output Filename
        output_filename_layout = QHBoxLayout()
        output_filename_label = QLabel("Output Filename:")
        self.output_filename_input = QLineEdit(self.config['output_config']['filename'])
        output_filename_layout.addWidget(output_filename_label)
        output_filename_layout.addWidget(self.output_filename_input)
        layout.addLayout(output_filename_layout)

        # Page Limit
        page_limit_layout = QHBoxLayout()
        page_limit_label = QLabel("Page Limit:")
        self.page_limit_input = QLineEdit(str(self.config['gui_config']['page_limit']))
        page_limit_layout.addWidget(page_limit_label)
        page_limit_layout.addWidget(self.page_limit_input)
        layout.addLayout(page_limit_layout)

        # Font Size
        fontsize_layout = QHBoxLayout()
        fontsize_label = QLabel("Font Size:")
        self.fontsize_input = QLineEdit(str(self.config['gui_config']['fontsize']))
        fontsize_layout.addWidget(fontsize_label)
        fontsize_layout.addWidget(self.fontsize_input)
        layout.addLayout(fontsize_layout)

        # Width
        width_layout = QHBoxLayout()
        width_label = QLabel("Width:")
        self.width_input = QLineEdit(str(self.config['gui_config']['width']))
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)

        # Height
        height_layout = QHBoxLayout()
        height_label = QLabel("Height:")
        self.height_input = QLineEdit(str(self.config['gui_config']['height']))
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        layout.addLayout(height_layout)

        # Dark Mode Toggle
        dark_mode_layout = QHBoxLayout()
        dark_mode_label = QLabel("Dark Mode:")
        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(self.config['gui_config'].get('dark_mode', False))
        dark_mode_layout.addWidget(dark_mode_label)
        dark_mode_layout.addWidget(self.dark_mode_toggle)
        layout.addLayout(dark_mode_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def apply_dark_mode(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #3e3e3e;
                color: #f0f0f0;
            }
            QLabel, QLineEdit, QPushButton, QCheckBox {
                background-color: #3e3e3e;
                color: #f0f0f0;
            }
        """)

    def save_settings(self) -> None:
        """Validates and saves the settings."""
        try:
            output_filename = validate_filename(self.output_filename_input.text())
            page_limit = validate_page_limit(int(self.page_limit_input.text()))
            fontsize = validate_fontsize(int(self.fontsize_input.text()))
            width = validate_dimension(int(self.width_input.text()))
            height = validate_dimension(int(self.height_input.text()))

            self.config['output_config']['filename'] = output_filename
            self.config['gui_config']['page_limit'] = page_limit
            self.config['gui_config']['fontsize'] = fontsize
            self.config['gui_config']['width'] = width
            self.config['gui_config']['height'] = height
            self.config['gui_config']['dark_mode'] = self.dark_mode_toggle.isChecked()
            self.save_config()
            QMessageBox.information(self, "Settings Saved",
                                    "Settings have been saved. Restart the application to apply changes to font size, width, height, and dark mode.")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
