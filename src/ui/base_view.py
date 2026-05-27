from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class BaseView(QWidget):
    load_sessions_clicked = pyqtSignal()
    load_proxy_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, description: str):
        super().__init__()
        self.description = description
        self.is_running = False
        self.colors = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        self.desc_label = QLabel(self.description)
        self.desc_label.setFont(QFont('Segoe UI', 9))
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        top_bar = QWidget()
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        self.btn_load = QPushButton('Загрузить сессии')
        self.btn_load.setFont(QFont('Segoe UI', 9))
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.setFixedHeight(38)
        self.btn_load.clicked.connect(self.load_sessions_clicked.emit)
        top_layout.addWidget(self.btn_load)

        self.btn_proxy = QPushButton('Загрузить прокси')
        self.btn_proxy.setFont(QFont('Segoe UI', 9))
        self.btn_proxy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_proxy.setFixedHeight(38)
        self.btn_proxy.clicked.connect(self.load_proxy_clicked.emit)
        top_layout.addWidget(self.btn_proxy)

        self.btn_settings = QPushButton('Настройки')
        self.btn_settings.setFont(QFont('Segoe UI', 9))
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setFixedHeight(38)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        top_layout.addWidget(self.btn_settings)

        top_layout.addStretch()

        self.btn_start = QPushButton('Запуск')
        self.btn_start.setFont(QFont('Segoe UI', 9))
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setFixedHeight(38)
        self.btn_start.setFixedWidth(120)
        self.btn_start.clicked.connect(self.on_start_stop_clicked)
        top_layout.addWidget(self.btn_start)

        layout.addWidget(top_bar)

        self.progress_container = QWidget()
        self.progress_container.setStyleSheet("background: transparent;")
        self.progress_container.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 10)
        progress_layout.setSpacing(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(32)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_container)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont('Consolas', 9))
        self.terminal.setPlaceholderText('Логи...')
        layout.addWidget(self.terminal)

    def set_load_button_text(self, text: str):
        self.btn_load.setText(text)

    def log(self, message, level='info'):
        colors = {
            'info': '#4fc3f7',
            'success': '#66bb6a',
            'error': '#ef5350',
            'warning': '#ffb74d'
        }
        color = colors.get(level, '#d4d4d4')
        self.terminal.append(f'<span style="color: {color};">{message}</span>')

    def set_progress(self, current, total):
        if total > 0:
            self.progress_container.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat(f'{current}/{total}')
        else:
            self.progress_container.setVisible(False)

    def reset_progress(self):
        self.progress_container.setVisible(False)
        self.progress_bar.setValue(0)

    def on_start_stop_clicked(self):
        if self.is_running:
            self.stop_clicked.emit()
        else:
            self.start_clicked.emit()

    def toggle_start_button(self, is_start):
        self.is_running = not is_start
        if is_start:
            self.btn_start.setText('Запуск')
        else:
            self.btn_start.setText('Стоп')
        self.apply_button_styles()

    def apply_button_styles(self):
        self.btn_load.setStyleSheet(f"""
            QPushButton {{
                background: {self.colors.get('success', '#28a745')};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #218838;
            }}
        """)

        self.btn_proxy.setStyleSheet(f"""
            QPushButton {{
                background: {self.colors.get('info', '#17a2b8')};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #138496;
            }}
        """)

        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: {self.colors.get('text_secondary', '#6c757d')};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #5a6268;
            }}
        """)

        if self.is_running:
            self.btn_start.setStyleSheet(f"""
                QPushButton {{
                    background: {self.colors.get('error', '#dc3545')};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 0 18px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: #c82333;
                }}
            """)
        else:
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #007bff;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 0 18px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #0056b3;
                }
            """)

    def apply_theme(self, colors):
        self.colors = colors

        self.setStyleSheet(f"background: {colors['main_bg']};")

        self.desc_label.setStyleSheet(f"""
            color: {colors['text_secondary']};
            background: transparent;
            padding: 0 0 10px 0;
        """)

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {colors['input_bg']};
                border: none;
                border-radius: 6px;
                text-align: center;
                font-size: 11px;
                font-weight: 500;
                color: {colors['text_primary']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['success']},
                    stop:1 #20c997
                );
                border-radius: 6px;
            }}
        """)

        self.apply_button_styles()
        self.apply_terminal_style()

    def apply_terminal_style(self):
        terminal_bg = '#1e1e1e' if self.colors.get('main_bg') == '#1a1d23' else '#1e1e1e'
        terminal_border = '#3e3e42' if self.colors.get('main_bg') == '#1e1e1e' else '#2d2d2d'
        self.terminal.setStyleSheet(f"""
            QTextEdit {{
                background: {terminal_bg};
                color: #d4d4d4;
                border: 1px solid {terminal_border};
                border-radius: 10px;
                padding: 15px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #2d2d2d;
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #4a4a4a;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #5a5a5a;
            }}
            QScrollBar::handle:vertical:pressed {{
                background: #4a90e2;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
