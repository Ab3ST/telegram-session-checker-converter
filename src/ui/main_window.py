from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from src.ui.views import CheckerView, ConverterView
from src.ui.dialogs import SessionsDialog, ProxyDialog, SettingsDialog, TDataDialog
from src.core.checker import SessionChecker
from src.core.converter import SessionConverter
from src.core.tdata_to_session import TDataToSessionConverter
from src.utils.config import Config
from src.utils.theme import Theme


class ThemeToggle(QWidget):
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.is_dark = is_dark
        self.setFixedSize(200, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)
        
        self.toggle_container = QWidget(self)
        self.toggle_container.setFixedSize(80, 36)
        
        self.toggle_btn = QWidget(self.toggle_container)
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.move(46, 2) if is_dark else self.toggle_btn.move(2, 2)
        
        self.sun_icon = QLabel(self.toggle_container)
        self.sun_icon.setFixedSize(20, 20)
        self.sun_icon.move(8, 8)
        self.sun_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.sun_icon.setStyleSheet("background: transparent; border: none;")
        self.sun_icon.raise_()
        
        self.separator = QWidget(self.toggle_container)
        self.separator.setFixedSize(1, 16)
        self.separator.move(39, 10)
        
        self.moon_icon = QLabel(self.toggle_container)
        self.moon_icon.setFixedSize(20, 20)
        self.moon_icon.move(52, 8)
        self.moon_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.moon_icon.setStyleSheet("background: transparent; border: none;")
        self.moon_icon.raise_()
        
        layout.addStretch()
        layout.addWidget(self.toggle_container)
        layout.addStretch()
        
        self.animation = QPropertyAnimation(self.toggle_btn, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(250)
        
        self.apply_styles()
    
    def render_svg(self, svg_path, width, height, color):
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        svg_content = svg_content.replace('#ffffff', color)
        svg_bytes = svg_content.encode('utf-8')
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    
    def apply_styles(self):
        bg_color = '#2d2d2d' if self.is_dark else '#e0e0e0'
        toggle_color = '#4a4a4a' if self.is_dark else '#ffffff'
        border_color = '#1a1a1a' if self.is_dark else '#bdbdbd'
        separator_color = '#5a5a5a' if self.is_dark else '#999999'
        icon_color = '#ffffff' if self.is_dark else '#333333'
        
        self.setStyleSheet("""
            QWidget {{
                background: transparent;
            }}
        """)
        
        self.toggle_container.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border-radius: 18px;
            }}
        """)
        
        self.toggle_btn.setStyleSheet(f"""
            QWidget {{
                background: {toggle_color};
                border-radius: 16px;
                border: 1px solid {border_color};
            }}
        """)
        
        self.separator.setStyleSheet(f"""
            QWidget {{
                background: {separator_color};
                border: none;
            }}
        """)
        
        self.sun_icon.setPixmap(self.render_svg('assets/sun.svg', 20, 20, icon_color))
        self.moon_icon.setPixmap(self.render_svg('assets/moon.svg', 20, 20, icon_color))
    
    def mousePressEvent(self, event):
        self.toggle()
        
    def toggle(self):
        self.is_dark = not self.is_dark
        
        start_pos = self.toggle_btn.pos()
        end_pos = QPoint(46, 2) if self.is_dark else QPoint(2, 2)
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()
        
        self.apply_styles()
    
    def set_dark(self, is_dark):
        if self.is_dark == is_dark:
            return
        self.is_dark = is_dark
        self.toggle_btn.move(46, 2) if is_dark else self.toggle_btn.move(2, 2)
        self.apply_styles()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.current_theme = self.config.get('theme', 'light')
        self.colors = Theme.LIGHT if self.current_theme == 'light' else Theme.DARK
        self.sessions = []
        self.proxies = []
        self.session_data = None
        self.proxy_data = None
        self.tdata_data = None
        self.checker = None
        self.converter = None
        self.tdata_converter = None

        self.checker_view = CheckerView()
        self.converter_view = ConverterView()

        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
        self._update_converter_button_text()
        
    def setup_ui(self):
        self.setWindowTitle('Anonymous')
        self.setWindowIcon(QIcon('assets/11062047e576490fbffdd85dfecb4cd9.jpg'))
        self.setFixedSize(1024, 600)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.btn_convert = QPushButton('Конвертация')
        self.btn_convert.setFont(QFont('Segoe UI', 10))
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setFixedHeight(50)
        self.btn_convert.setCheckable(True)
        self.btn_convert.clicked.connect(self.show_convert_view)
        sidebar_layout.addWidget(self.btn_convert)

        self.btn_check = QPushButton('Чек на валид')
        self.btn_check.setFont(QFont('Segoe UI', 10))
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.setFixedHeight(50)
        self.btn_check.setCheckable(True)
        self.btn_check.clicked.connect(self.show_check_view)
        sidebar_layout.addWidget(self.btn_check)

        sidebar_layout.addStretch()

        self.theme_container = QWidget()
        theme_layout = QVBoxLayout(self.theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(0)

        self.btn_theme_collapse = QLabel()
        self.btn_theme_collapse.setFixedSize(200, 24)
        self.btn_theme_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_collapse.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_theme_collapse.mousePressEvent = lambda e: self.toggle_theme_visibility()
        theme_layout.addWidget(self.btn_theme_collapse)

        self.theme_toggle = ThemeToggle(self, is_dark=(self.current_theme == 'dark'))
        self.theme_toggle.mousePressEvent = lambda e: self.on_theme_toggle()
        theme_layout.addWidget(self.theme_toggle)

        sidebar_layout.addWidget(self.theme_container)

        self.theme_visible = self.config.get('theme_visible', True)
        if not self.theme_visible:
            self.theme_toggle.hide()

        self.update_arrow_icon()

        main_layout.addWidget(self.sidebar)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        main_layout.addWidget(self.content)

        self.content_layout.addWidget(self.converter_view)
        self.content_layout.addWidget(self.checker_view)

        self.show_convert_view()
    
    def connect_signals(self):
        self.checker_view.load_sessions_clicked.connect(self.on_checker_load_sessions)
        self.checker_view.load_proxy_clicked.connect(self.on_checker_load_proxy)
        self.checker_view.settings_clicked.connect(self.on_checker_settings)
        self.checker_view.start_clicked.connect(self.on_checker_start)
        self.checker_view.stop_clicked.connect(self.on_checker_stop)

        self.converter_view.load_sessions_clicked.connect(self.on_converter_load_sessions)
        self.converter_view.load_proxy_clicked.connect(self.on_converter_load_proxy)
        self.converter_view.settings_clicked.connect(self.on_converter_settings)
        self.converter_view.start_clicked.connect(self.on_converter_start)
        self.converter_view.stop_clicked.connect(self.on_converter_stop)
    
    def on_theme_toggle(self):
        self.theme_toggle.toggle()
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.colors = Theme.DARK if self.current_theme == 'dark' else Theme.LIGHT
        settings = self.config.get_all()
        settings['theme'] = self.current_theme
        self.config.save(settings)
        self.apply_theme()
    
    def toggle_theme_visibility(self):
        self.theme_visible = not self.theme_visible
        if self.theme_visible:
            self.theme_toggle.show()
        else:
            self.theme_toggle.hide()
        
        self.update_arrow_icon()
        
        settings = self.config.get_all()
        settings['theme_visible'] = self.theme_visible
        self.config.save(settings)
    
    def update_arrow_icon(self):
        arrow_path = 'assets/arrow-down.svg' if self.theme_visible else 'assets/arrow-up.svg'
        with open(arrow_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        arrow_color = '#999999' if self.current_theme == 'light' else '#666666'
        svg_content = svg_content.replace('#808080', arrow_color)
        svg_bytes = svg_content.encode('utf-8')
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.btn_theme_collapse.setPixmap(pixmap)
    
    def _update_converter_button_text(self):
        settings = self.config.get_all()
        conversion_mode = settings.get('conversion_mode', 'session_to_tdata')
        
        if conversion_mode == 'tdata_to_session':
            self.converter_view.set_load_button_text('Загрузить tdata')
        else:
            self.converter_view.set_load_button_text('Загрузить сессии')

    def apply_theme(self):
        self.setStyleSheet(Theme.get_main_window_style(self.colors))
        
        self.sidebar.setStyleSheet(f"""
            QWidget {{
                background: {self.colors['sidebar_bg']};
                border-right: 1px solid {self.colors['sidebar_border']};
            }}
        """)
        
        self.btn_convert.setStyleSheet(Theme.get_sidebar_button_style(self.colors))
        self.btn_check.setStyleSheet(Theme.get_sidebar_button_style(self.colors))
        
        self.btn_theme_collapse.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                border-top: 1px solid {self.colors['sidebar_border']};
                padding: 4px;
            }}
        """)
        
        self.update_arrow_icon()
        
        self.content.setStyleSheet(Theme.get_content_style(self.colors))
        self.checker_view.apply_theme(self.colors)
        self.converter_view.apply_theme(self.colors)
    
    def update_menu_styles(self, active_btn):
        self.btn_convert.setChecked(active_btn == 'convert')
        self.btn_check.setChecked(active_btn == 'check')
    
    def show_convert_view(self):
        self.update_menu_styles('convert')
        self.checker_view.hide()
        self.converter_view.show()
    
    def show_check_view(self):
        self.update_menu_styles('check')
        self.converter_view.hide()
        self.checker_view.show()
    
    def on_checker_load_sessions(self):
        dialog = SessionsDialog(self, colors=self.colors)
        if dialog.exec():
            data = dialog.get_data()
            self.session_data = data
            self.sessions = data['session_files']
            self.checker_view.log(f'Папка: {data["path"]}', 'info')
            self.checker_view.log(f'Найдено сессий: {len(data["session_files"])}', 'success')
            self.checker_view.log(f'Формат: {data["format"]} ({data["library"]})', 'info')
    
    def on_checker_load_proxy(self):
        dialog = ProxyDialog(self, colors=self.colors)
        if dialog.exec():
            data = dialog.get_data()
            self.proxy_data = data
            self.proxies = data['proxies']
            self.checker_view.log(f'Файл: {data["path"]}', 'info')
            self.checker_view.log(f'Загружено прокси: {len(data["proxies"])}', 'success')
            self.checker_view.log(f'Тип: {data["type"]} | Формат: {data["format"]}', 'info')
    
    def on_checker_settings(self):
        dialog = SettingsDialog(self.config.get_all(), self, colors=self.colors)
        if dialog.exec():
            settings = dialog.get_settings()
            if self.config.save(settings):
                self.checker_view.log('Настройки успешно сохранены', 'success')
            else:
                self.checker_view.log('Ошибка сохранения настроек', 'error')
    
    def _get_api_credentials(self):
        if self.session_data and self.session_data.get('format') == 'session_only':
            return self.session_data.get('api_credentials_list', [])
        return []

    def on_checker_start(self):
        if not self.sessions:
            self.checker_view.log('Сначала загрузите сессии', 'error')
            return

        if self.checker and self.checker.thread:
            self.checker_view.log('Чекер уже запущен', 'warning')
            return

        settings = self.config.get_all()
        use_proxy = settings.get('use_proxy', True)

        if use_proxy and not self.proxies:
            self.checker_view.log('Включена опция "Использовать прокси", но прокси не загружены', 'error')
            return

        if not use_proxy and not self.proxies:
            self.checker_view.log('Работа без прокси', 'warning')

        api_credentials = self._get_api_credentials()

        self.checker = SessionChecker(
            self.sessions,
            self.proxies,
            self.proxy_data or {},
            settings,
            self.checker_view,
            self.session_data.get('library', 'telethon') if self.session_data else 'telethon',
            api_credentials
        )
        self.checker.start()
    
    def on_checker_stop(self):
        if self.checker:
            self.checker.stop()
    
    def on_converter_load_sessions(self):
        settings = self.config.get_all()
        conversion_mode = settings.get('conversion_mode', 'session_to_tdata')
        
        if conversion_mode == 'tdata_to_session':
            dialog = TDataDialog(self, colors=self.colors)
            if dialog.exec():
                data = dialog.get_data()
                self.tdata_data = data
                self.sessions = data['tdata_folders']
                self.converter_view.log(f'Папка: {data["path"]}', 'info')
                self.converter_view.log(f'Найдено tdata: {len(data["tdata_folders"])}', 'success')
        else:
            dialog = SessionsDialog(self, is_converter=True, colors=self.colors)
            if dialog.exec():
                data = dialog.get_data()
                self.session_data = data
                self.sessions = data['session_files']
                self.converter_view.log(f'Папка: {data["path"]}', 'info')
                self.converter_view.log(f'Найдено сессий: {len(data["session_files"])}', 'success')
                self.converter_view.log(f'Формат: {data["format"]}', 'info')
    
    def on_converter_load_proxy(self):
        dialog = ProxyDialog(self, colors=self.colors)
        if dialog.exec():
            data = dialog.get_data()
            self.proxy_data = data
            self.proxies = data['proxies']
            self.converter_view.log(f'Файл: {data["path"]}', 'info')
            self.converter_view.log(f'Загружено прокси: {len(data["proxies"])}', 'success')
            self.converter_view.log(f'Тип: {data["type"]} | Формат: {data["format"]}', 'info')
    
    def on_converter_settings(self):
        dialog = SettingsDialog(self.config.get_all(), self, is_converter=True, colors=self.colors)
        if dialog.exec():
            settings = dialog.get_settings()
            if self.config.save(settings):
                self.converter_view.log('Настройки успешно сохранены', 'success')
                self._update_converter_button_text()
            else:
                self.converter_view.log('Ошибка сохранения настроек', 'error')
    
    def on_converter_start(self):
        if not self.sessions:
            self.converter_view.log('Сначала загрузите данные для конвертации', 'error')
            return

        settings = self.config.get_all()
        conversion_mode = settings.get('conversion_mode', 'session_to_tdata')

        if conversion_mode == 'tdata_to_session':
            if self.tdata_converter and self.tdata_converter.is_running():
                self.converter_view.log('Конвертер уже запущен', 'warning')
                return
        else:
            if self.converter and self.converter.thread:
                self.converter_view.log('Конвертер уже запущен', 'warning')
                return

        use_proxy = settings.get('use_proxy', True)

        if use_proxy and not self.proxies:
            self.converter_view.log('Включена опция "Использовать прокси", но прокси не загружены', 'error')
            return

        if not use_proxy and not self.proxies:
            self.converter_view.log('Работа без прокси', 'warning')

        if conversion_mode == 'tdata_to_session':
            api_credentials = self.tdata_data.get('api_credentials_list', []) if self.tdata_data else []
            output_format = self.tdata_data.get('output_format', 'auto') if self.tdata_data else 'auto'
            
            self.tdata_converter = TDataToSessionConverter()
            self.tdata_converter.start(
                self.sessions,
                self.proxies,
                self.proxy_data or {},
                api_credentials,
                output_format
            )
            self.tdata_converter.thread.progress.connect(self._on_tdata_progress)
            self.tdata_converter.thread.finished_signal.connect(self._on_tdata_finished)
        else:
            api_credentials = self._get_api_credentials()

            self.converter = SessionConverter(
                self.sessions,
                self.proxies,
                self.proxy_data or {},
                self.converter_view,
                api_credentials
            )
            self.converter.start()
    
    def on_converter_stop(self):
        settings = self.config.get_all()
        conversion_mode = settings.get('conversion_mode', 'session_to_tdata')
        
        if conversion_mode == 'tdata_to_session':
            if self.tdata_converter:
                self.tdata_converter.stop()
        else:
            if self.converter:
                self.converter.stop()

    def _on_tdata_progress(self, name, status, current, total):
        level = 'success' if status == 'Конвертирован' else 'error'
        self.converter_view.log(f'{name} | {status}', level)

    def _on_tdata_finished(self, summary, success, fail):
        self.converter_view.log(summary, 'success')
        self.converter_view.reset_progress()
