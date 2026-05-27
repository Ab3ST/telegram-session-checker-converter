from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector

from src.utils.proxy import parse_proxy_auto, ProxyInfo


class ProxyCheckThread(QThread):
    progress = pyqtSignal(str, str, str, int)
    finished = pyqtSignal(int, int)

    def __init__(self, proxies, proxy_type=None, proxy_format=None):
        super().__init__()
        self.proxies = proxies
        self.valid_count = 0
        self.invalid_count = 0
        self.valid_proxies = []
        self.test_urls = [
            'http://ip-api.com/json/',
            'http://httpbin.org/ip',
            'https://api.ipify.org/'
        ]
        self.timeout = 3

    async def check_single(self, proxy_info: ProxyInfo, test_url: str):
        timeout = aiohttp.ClientTimeout(total=self.timeout, connect=2)
        start_time = asyncio.get_event_loop().time()
        
        try:
            if proxy_info.protocol in ['socks5', 'socks4']:
                connector = ProxyConnector.from_url(proxy_info.to_url())
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(test_url) as response:
                        if response.status == 200:
                            elapsed = int((asyncio.get_event_loop().time() - start_time) * 1000)
                            return True, elapsed
            else:
                connector = aiohttp.TCPConnector(limit=0, ssl=False)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(test_url, proxy=proxy_info.to_url()) as response:
                        if response.status == 200:
                            elapsed = int((asyncio.get_event_loop().time() - start_time) * 1000)
                            return True, elapsed
        except:
            pass
        return False, 0

    async def check_proxy_all_protocols(self, proxy_line: str):
        proxy_infos = parse_proxy_auto(proxy_line)
        if not proxy_infos:
            return None, None, 0
        
        async def try_protocol(proxy_info):
            for test_url in self.test_urls:
                try:
                    valid, speed = await asyncio.wait_for(
                        self.check_single(proxy_info, test_url),
                        timeout=self.timeout
                    )
                    if valid:
                        return proxy_info, speed
                except:
                    continue
            return None, 0
        
        tasks = [try_protocol(p) for p in proxy_infos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple) and result[0]:
                return result[0], result[0].protocol, result[1]
        
        return None, None, 0

    async def check_all(self):
        semaphore = asyncio.Semaphore(200)

        async def check_with_semaphore(proxy_line):
            async with semaphore:
                proxy_info, protocol, speed = await self.check_proxy_all_protocols(proxy_line)
                if protocol:
                    self.valid_count += 1
                    self.valid_proxies.append((proxy_line, protocol))
                    self.progress.emit(proxy_line, 'valid', protocol.upper(), speed)
                else:
                    self.invalid_count += 1
                    self.progress.emit(proxy_line, 'invalid', '', 0)

        tasks = [check_with_semaphore(proxy) for proxy in self.proxies]
        await asyncio.gather(*tasks, return_exceptions=True)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.check_all())
            self.finished.emit(self.valid_count, self.invalid_count)
        finally:
            loop.close()


class ProxyCheckDialog(QDialog):
    def __init__(self, proxies, proxy_type=None, proxy_format=None, parent=None):
        super().__init__(parent)
        self.proxies = proxies
        self.drag_position = None
        self.check_thread = None
        self.valid_proxies = []
        self.setup_ui()
        self.start_check()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(600, 450)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel('Проверка прокси')
        title.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #212529;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.status_label = QLabel('Проверка...')
        self.status_label.setFont(QFont('Segoe UI', 9))
        self.status_label.setStyleSheet("color: #6c757d;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont('Consolas', 8))
        self.terminal.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.terminal)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_save = QPushButton('Сохранить валидные')
        self.btn_save.setFont(QFont('Segoe UI', 9))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(36)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #218838;
            }
            QPushButton:disabled {
                background: #e9ecef;
                color: #adb5bd;
            }
        """)
        self.btn_save.clicked.connect(self.save_valid)
        btn_layout.addWidget(self.btn_save)

        self.btn_close = QPushButton('Закрыть')
        self.btn_close.setFont(QFont('Segoe UI', 9))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(36)
        self.btn_close.setEnabled(False)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:disabled {
                background: #e9ecef;
                color: #adb5bd;
            }
        """)
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def start_check(self):
        self.check_thread = ProxyCheckThread(self.proxies)
        self.check_thread.progress.connect(self.on_progress)
        self.check_thread.finished.connect(self.on_finished)
        self.check_thread.start()

    def on_progress(self, proxy, status, protocol, speed):
        if status == 'valid':
            self.valid_proxies.append(proxy)
            self.terminal.append(f'<span style="color: #66bb6a;">+ {proxy} [{protocol}] {speed}ms</span>')
        else:
            self.terminal.append(f'<span style="color: #ef5350;">- {proxy}</span>')

    def on_finished(self, valid, invalid):
        self.status_label.setText(f'Valid: {valid} | Invalid: {invalid}')
        self.terminal.append('\n<span style="color: #4fc3f7;">Check completed!</span>')
        self.btn_close.setEnabled(True)
        if valid > 0:
            self.btn_save.setEnabled(True)

    def save_valid(self):
        self.accept()

    def get_valid_proxies(self):
        return self.valid_proxies

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
