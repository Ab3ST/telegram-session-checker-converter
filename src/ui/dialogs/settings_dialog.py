from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel, QWidget, QFrame)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QCursor, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from src.ui.dialogs.base_dialog import BaseDialog


class Tooltip(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QLabel {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 9pt;
            }
        """)
        self.setMargin(0)


class InfoIcon(QLabel):
    def __init__(self, tooltip_text, colors, parent=None):
        super().__init__(parent)
        self.tooltip_text = tooltip_text
        self.colors = colors
        self.custom_tooltip = None
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent;")

    def enterEvent(self, event):
        if self.custom_tooltip is None:
            self.custom_tooltip = Tooltip(self.tooltip_text)

        pos = QCursor.pos()
        self.custom_tooltip.move(pos + QPoint(10, 10))
        self.custom_tooltip.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.custom_tooltip:
            self.custom_tooltip.hide()
        super().leaveEvent(event)


class SettingsDialog(BaseDialog):
    def __init__(self, current_settings=None, parent=None, is_converter=False, colors=None):
        self.settings = current_settings or {
            'check_gifts': False,
            'check_stars': False,
            'check_premium': False,
            'check_channels': False,
            'check_crypto_bots': False,
            'use_proxy': True,
            'conversion_mode': 'session_to_tdata',
            'output_session_format': 'auto'
        }
        self.is_converter = is_converter
        super().__init__(parent, colors)
        self.setup_ui()

    def setup_ui(self):
        self.setup_frameless(380, 320 if self.is_converter else 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._create_header()
        layout.addWidget(header)

        content = self._create_content()
        layout.addWidget(content)

        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"background: {self.colors['dialog_bg']}; border-radius: 12px 12px 0 0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 25, 30, 20)
        header_layout.setSpacing(15)

        desc = QLabel('Выбери параметры для ' + ('конвертера' if self.is_converter else 'чекера'))
        desc.setFont(QFont('Segoe UI', 11))
        desc.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent;")
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

        if self.is_converter:
            self.settings['_session_to_tdata'] = self.settings.get('conversion_mode', 'session_to_tdata') == 'session_to_tdata'
            self.settings['_tdata_to_session'] = self.settings.get('conversion_mode', 'session_to_tdata') == 'tdata_to_session'
            
            self.cb_session_to_tdata = self._create_checkbox('Session → TData', '_session_to_tdata')
            self.cb_tdata_to_session = self._create_checkbox('TData → Session', '_tdata_to_session')
            
            self.cb_session_to_tdata.toggled.connect(lambda checked: self.cb_tdata_to_session.setChecked(not checked) if checked else None)
            self.cb_tdata_to_session.toggled.connect(lambda checked: self.cb_session_to_tdata.setChecked(not checked) if checked else None)
            
            content_layout.addWidget(self.cb_session_to_tdata)
            content_layout.addWidget(self.cb_tdata_to_session)

            separator1 = QFrame()
            separator1.setFrameShape(QFrame.Shape.HLine)
            separator1.setStyleSheet(f"background: {self.colors['divider']}; max-height: 1px; margin: 10px 0;")
            content_layout.addWidget(separator1)

        if not self.is_converter:
            self.cb_gifts = self._create_checkbox('Подарки', 'check_gifts')
            content_layout.addWidget(self.cb_gifts)

            self.cb_stars = self._create_checkbox('Звёзды', 'check_stars')
            content_layout.addWidget(self.cb_stars)

            self.cb_premium = self._create_checkbox('Премиум', 'check_premium')
            content_layout.addWidget(self.cb_premium)

            self.cb_channels = self._create_checkbox('Админ-каналы', 'check_channels')
            content_layout.addWidget(self.cb_channels)

            self.cb_crypto = self._create_checkbox_with_info('Крипто-боты(баланс)', 'check_crypto_bots', 'Поддерживается (CryptoBot, xRocket)')
            content_layout.addWidget(self.cb_crypto)

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet(f"background: {self.colors['divider']}; max-height: 1px; margin: 10px 0;")
            content_layout.addWidget(separator)

        self.cb_proxy = self._create_checkbox('Использовать прокси', 'use_proxy')
        content_layout.addWidget(self.cb_proxy)

        content_layout.addStretch()

        return content

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

        btn_save = QPushButton('Сохранить')
        btn_save.setFont(QFont('Segoe UI', 9))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setFixedSize(100, 36)
        btn_save.setStyleSheet(f"""
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
        btn_save.clicked.connect(self.save_settings)
        footer_layout.addWidget(btn_save)

        return footer

    def _create_checkbox(self, text: str, key: str) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setFont(QFont('Segoe UI', 10))
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setChecked(self.settings.get(key, False))
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {self.colors['text_primary']};
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.colors['input_border']};
                border-radius: 4px;
                background: {self.colors['input_bg']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.colors['input_focus']};
            }}
            QCheckBox::indicator:checked {{
                background: {self.colors['button_active']};
                border-color: {self.colors['button_active']};
            }}
        """)
        return cb

    def _create_checkbox_with_info(self, text: str, key: str, tooltip: str) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        cb = QCheckBox(text)
        cb.setFont(QFont('Segoe UI', 10))
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setChecked(self.settings.get(key, False))
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {self.colors['text_primary']};
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.colors['input_border']};
                border-radius: 4px;
                background: {self.colors['input_bg']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.colors['input_focus']};
            }}
            QCheckBox::indicator:checked {{
                background: {self.colors['button_active']};
                border-color: {self.colors['button_active']};
            }}
        """)
        layout.addWidget(cb)

        layout.addStretch()

        icon = InfoIcon(tooltip, self.colors)
        icon.setFixedSize(16, 16)
        icon.setPixmap(self._render_svg('assets/info.svg', 16, 16))
        icon.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(icon)

        setattr(self, f'_{key}_checkbox', cb)

        return container

    def _render_svg(self, svg_path: str, width: int, height: int):
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    def save_settings(self):
        if self.is_converter:
            if self.cb_session_to_tdata.isChecked():
                self.settings['conversion_mode'] = 'session_to_tdata'
            else:
                self.settings['conversion_mode'] = 'tdata_to_session'
        
        if not self.is_converter:
            self.settings['check_gifts'] = self.cb_gifts.isChecked()
            self.settings['check_stars'] = self.cb_stars.isChecked()
            self.settings['check_premium'] = self.cb_premium.isChecked()
            self.settings['check_channels'] = self.cb_channels.isChecked()
            self.settings['check_crypto_bots'] = self._check_crypto_bots_checkbox.isChecked()
        self.settings['use_proxy'] = self.cb_proxy.isChecked()
        self.accept()

    def get_settings(self):
        return self.settings
