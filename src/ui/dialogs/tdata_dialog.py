from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QFrame,
                             QLineEdit, QScrollArea, QFileDialog, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QObject, QEvent, QPoint
from PyQt6.QtGui import QFont
import os
from src.ui.dialogs.base_dialog import BaseDialog
from src.utils.theme import Theme
from src.utils.tdata import find_tdata_folders


class TooltipFilter(QObject):
    def __init__(self, button: QWidget, popup: QLabel, dialog: QWidget):
        super().__init__(button)
        self._button = button
        self._popup = popup
        self._dialog = dialog

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            pos = self._button.mapTo(self._dialog, QPoint(0, 0))
            x = pos.x() + self._button.width() - self._popup.width()
            y = pos.y() - self._popup.sizeHint().height() - 6
            self._popup.move(max(x, 4), max(y, 4))
            self._popup.raise_()
            self._popup.show()
        elif event.type() == QEvent.Type.Leave:
            self._popup.hide()
        return super().eventFilter(obj, event)


class TDataDialog(BaseDialog):
    def __init__(self, parent=None, colors=None):
        self.tdata_path = ''
        self.api_credentials_list = []
        self.output_format = 'auto'
        super().__init__(parent, colors)
        self.setup_ui()

    def setup_ui(self):
        self.setup_frameless(480, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._create_header()
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = self._create_content()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"background: {self.colors['dialog_bg']}; border-radius: 12px 12px 0 0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 25, 30, 20)
        header_layout.setSpacing(15)

        title = QLabel('Загрузка TData')
        title.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        desc = QLabel('Настрой параметры загрузки')
        desc.setFont(QFont('Segoe UI', 9))
        desc.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(desc)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedWidth(120)
        divider.setFixedHeight(2)
        divider.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 #4a90e2, stop:1 transparent); border: none;")
        divider_container = QWidget()
        divider_container.setStyleSheet("background: transparent;")
        divider_layout = QHBoxLayout(divider_container)
        divider_layout.setContentsMargins(0, 0, 0, 0)
        divider_layout.addStretch()
        divider_layout.addWidget(divider)
        divider_layout.addStretch()
        header_layout.addWidget(divider_container)

        return header

    def _create_content(self) -> QWidget:
        content = QWidget()
        content.setStyleSheet(f"background: {self.colors['dialog_bg']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 20)
        content_layout.setSpacing(18)

        self.credentials_widget = self._create_credentials_widget()
        content_layout.addWidget(self.credentials_widget)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet(f"background: {self.colors['divider']}; max-height: 1px; margin: 5px 0;")
        content_layout.addWidget(separator1)

        format_row = QHBoxLayout()
        format_row.setSpacing(15)
        format_row.setContentsMargins(0, 0, 0, 0)

        self.rb_auto = QRadioButton('Auto')
        self.rb_auto.setFont(QFont('Segoe UI', 9))
        self.rb_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rb_auto.setChecked(True)
        self.rb_auto.setStyleSheet(Theme.get_radio_style(self.colors))
        format_row.addWidget(self.rb_auto)

        self.rb_telethon = QRadioButton('Telethon')
        self.rb_telethon.setFont(QFont('Segoe UI', 9))
        self.rb_telethon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rb_telethon.setStyleSheet(Theme.get_radio_style(self.colors))
        format_row.addWidget(self.rb_telethon)

        self.rb_pyrogram = QRadioButton('Pyrogram')
        self.rb_pyrogram.setFont(QFont('Segoe UI', 9))
        self.rb_pyrogram.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rb_pyrogram.setStyleSheet(Theme.get_radio_style(self.colors))
        format_row.addWidget(self.rb_pyrogram)

        format_row.addStretch()
        content_layout.addLayout(format_row)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background: {self.colors['divider']}; max-height: 1px; margin: 5px 0;")
        content_layout.addWidget(separator2)

        path_label = QLabel('Путь к TData')
        path_label.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        path_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
        content_layout.addWidget(path_label)

        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(8)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText('Укажи путь к папке с tdata')
        self.input_path.setFixedHeight(38)
        self.input_path.setStyleSheet(Theme.get_input_style(self.colors))
        path_input_layout.addWidget(self.input_path)

        btn_browse = QPushButton('...')
        btn_browse.setFont(QFont('Segoe UI', 14))
        btn_browse.setFixedSize(38, 38)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['input_border']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {self.colors['button_hover']};
                border-color: {self.colors['input_focus']};
            }}
        """)
        btn_browse.clicked.connect(self.browse_folder)
        path_input_layout.addWidget(btn_browse)

        content_layout.addLayout(path_input_layout)
        content_layout.addStretch()

        return content

    def _create_credentials_widget(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(5)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        self.input_api = QLineEdit()
        self.input_api.setPlaceholderText('api_id:api_hash')
        self.input_api.setFixedHeight(36)
        self.input_api.setStyleSheet(Theme.get_input_style(self.colors))
        row_layout.addWidget(self.input_api)

        btn_bulk = QPushButton('Массовый залив')
        btn_bulk.setFont(QFont('Segoe UI', 8))
        btn_bulk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_bulk.setFixedHeight(36)
        btn_bulk.setStyleSheet(f"""
            QPushButton {{
                background: {self.colors['text_secondary']};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 0 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #5a6268;
            }}
        """)
        btn_bulk.clicked.connect(self.load_bulk_credentials)
        row_layout.addWidget(btn_bulk)

        btn_help = QPushButton('?')
        btn_help.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.setFixedSize(22, 36)
        btn_help.setFlat(True)
        btn_help.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.colors['text_secondary']};
                border: none;
                padding: 0;
                font-weight: 700;
            }}
            QPushButton:hover {{
                color: {self.colors['text_primary']};
                background: transparent;
            }}
        """)

        help_text = 'Пример:\n    api_id:api_hash\n    api_id:api_hash'
        self._help_popup = QLabel(help_text, self)
        self._help_popup.setFont(QFont('Segoe UI', 9))
        self._help_popup.setWordWrap(True)
        self._help_popup.setFixedWidth(280)
        self._help_popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._help_popup.setStyleSheet(f"""
            QLabel {{
                background: {self.colors['dialog_bg']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['border']};
                border-radius: 6px;
                padding: 10px 12px;
            }}
        """)
        self._help_popup.adjustSize()
        self._help_popup.hide()

        self._help_filter = TooltipFilter(btn_help, self._help_popup, self)
        btn_help.installEventFilter(self._help_filter)
        row_layout.addWidget(btn_help)

        layout.addWidget(row)

        self.bulk_status = QLabel('')
        self.bulk_status.setFont(QFont('Segoe UI', 8))
        self.bulk_status.setStyleSheet(f"color: {self.colors['success']}; background: transparent;")
        self.bulk_status.setVisible(False)
        layout.addWidget(self.bulk_status)

        return widget

    def _create_footer(self) -> QWidget:
        footer = QWidget()
        footer.setStyleSheet(f"background: {self.colors['dialog_bg']}; border-radius: 0 0 12px 12px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 15, 25, 20)
        footer_layout.setSpacing(10)

        footer_layout.addStretch()

        btn_cancel = QPushButton('Отмена')
        btn_cancel.setFont(QFont('Segoe UI', 9))
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setFixedSize(90, 36)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.colors['text_secondary']};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                color: {self.colors['text_primary']};
                background: {self.colors['button_hover']};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)

        btn_load = QPushButton('Загрузить')
        btn_load.setFont(QFont('Segoe UI', 9))
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load.setFixedSize(100, 36)
        btn_load.setStyleSheet(f"""
            QPushButton {{
                background: {self.colors['button_active']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #3d7bc7;
            }}
        """)
        btn_load.clicked.connect(self.load_tdata)
        footer_layout.addWidget(btn_load)

        return footer

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с tdata")
        if folder:
            self.input_path.setText(folder)

    def load_tdata(self):
        path = self.input_path.text().strip()
        if not path or not os.path.exists(path):
            self.input_path.setStyleSheet(Theme.get_error_input_style())
            return

        if not self.api_credentials_list:
            raw = self.input_api.text().strip()
            parts = raw.split(':', 1) if ':' in raw else []
            if len(parts) != 2 or not parts[0].strip().isdigit() or not parts[1].strip():
                self.input_api.setStyleSheet(Theme.get_error_input_style())
                return

        if self.rb_auto.isChecked():
            self.output_format = 'auto'
        elif self.rb_telethon.isChecked():
            self.output_format = 'telethon'
        else:
            self.output_format = 'pyrogram'

        self.tdata_path = path
        self.accept()

    def get_data(self):
        tdata_folders = find_tdata_folders(self.tdata_path)

        api_credentials_list = []
        if self.api_credentials_list:
            api_credentials_list = self.api_credentials_list
        else:
            raw = self.input_api.text().strip()
            parts = raw.split(':', 1)
            api_credentials_list = [{
                'api_id': int(parts[0].strip()),
                'api_hash': parts[1].strip(),
            }]

        return {
            'path': self.tdata_path,
            'tdata_folders': tdata_folders,
            'api_credentials_list': api_credentials_list,
            'output_format': self.output_format,
        }

    def load_bulk_credentials(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Загрузить пары api_id:api_hash', '', 'Text Files (*.txt)'
        )
        if not file_path:
            return

        parsed = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' not in line:
                    continue
                parts = line.split(':', 1)
                if parts[0].strip().isdigit() and parts[1].strip():
                    parsed.append({
                        'api_id': int(parts[0].strip()),
                        'api_hash': parts[1].strip(),
                    })

        if not parsed:
            return

        self.api_credentials_list = parsed
        self.input_api.clear()
        self.input_api.setPlaceholderText('api_id:api_hash  (файл загружен)')
        self.input_api.setStyleSheet(Theme.get_input_style(self.colors))
        self.bulk_status.setText(f'Загружено {len(parsed)} пар из файла')
        self.bulk_status.setVisible(True)
