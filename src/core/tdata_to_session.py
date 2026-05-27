import os
import asyncio
import sqlite3
import time
from typing import Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QThread, pyqtSignal
from telethon.sessions import StringSession
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession
from src.utils.proxy import parse_proxy, to_telethon


PROXY_ROTATION = 15
MAX_CONCURRENT = 10
DC_IPS = {
    1: "149.154.175.53",
    2: "149.154.167.51",
    3: "149.154.175.100",
    4: "149.154.167.92",
    5: "91.108.56.130"
}


class TDataToSessionThread(QThread):
    progress = pyqtSignal(str, str, int, int)
    finished_signal = pyqtSignal(str, int, int)

    def __init__(self, tdata_folders, proxies, proxy_data, api_credentials_list, output_format='auto'):
        super().__init__()
        self.tdata_folders = tdata_folders
        self.proxies = proxies
        self.proxy_data = proxy_data
        self.api_credentials_list = api_credentials_list or []
        self.output_format = output_format
        self.is_running = True
        self.output_dir = self._create_output_directory()
        self.current_proxy_index = 0
        self.conversions_on_proxy = 0
        self.conversions_per_proxy = PROXY_ROTATION
        self._proxy_lock = asyncio.Lock()
        self.success_count = 0
        self.fail_count = 0
        self._count_lock = asyncio.Lock()
        self._loop = None
        self._tasks = set()
        self.tdata_credentials = {
            path: self.api_credentials_list[i % len(self.api_credentials_list)]
            for i, path in enumerate(self.tdata_folders)
        } if self.api_credentials_list else {}

    def _create_output_directory(self) -> str:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        base_dir = os.path.join('tdata_to_session', timestamp)
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    def stop(self) -> None:
        self.is_running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._cancel_tasks)

    def _cancel_tasks(self) -> None:
        for task in list(self._tasks):
            if not task.done():
                task.cancel()

    async def get_current_proxy(self) -> Optional[str]:
        if not self.proxies or not self.proxy_data:
            return None
        async with self._proxy_lock:
            if self.conversions_on_proxy >= self.conversions_per_proxy:
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
                self.conversions_on_proxy = 0
            self.conversions_on_proxy += 1
            return self.proxies[self.current_proxy_index]

    def _detect_session_format(self, tdesk) -> str:
        if self.output_format != 'auto':
            return self.output_format
        return 'telethon'

    def _create_telethon_session(self, session_path: str, auth_key: bytes, dc_id: int, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(session_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE sessions (
                    dc_id INTEGER PRIMARY KEY,
                    server_address TEXT,
                    port INTEGER,
                    auth_key BLOB,
                    takeout_id INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE entities (
                    id INTEGER PRIMARY KEY,
                    hash INTEGER NOT NULL,
                    username TEXT,
                    phone INTEGER,
                    name TEXT,
                    date INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE sent_files (
                    md5_digest BLOB,
                    file_size INTEGER,
                    type INTEGER,
                    id INTEGER,
                    hash INTEGER,
                    PRIMARY KEY(md5_digest, file_size, type)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE update_state (
                    id INTEGER PRIMARY KEY,
                    pts INTEGER,
                    qts INTEGER,
                    date INTEGER,
                    seq INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE version (
                    version INTEGER PRIMARY KEY
                )
            ''')
            
            cursor.execute('INSERT INTO version VALUES (?)', (8,))
            
            server = DC_IPS.get(dc_id, DC_IPS[2])
            port = 443
            
            cursor.execute(
                'INSERT INTO sessions VALUES (?, ?, ?, ?, ?)',
                (dc_id, server, port, auth_key, None)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False

    def _create_pyrogram_session(self, session_path: str, auth_key: bytes, dc_id: int, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(session_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE sessions (
                    dc_id INTEGER PRIMARY KEY,
                    api_id INTEGER,
                    test_mode INTEGER,
                    auth_key BLOB,
                    date INTEGER NOT NULL,
                    user_id INTEGER,
                    is_bot INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE peers (
                    id INTEGER PRIMARY KEY,
                    access_hash INTEGER,
                    type INTEGER NOT NULL,
                    username TEXT,
                    phone_number TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE version (
                    number INTEGER PRIMARY KEY
                )
            ''')
            
            cursor.execute('INSERT INTO version VALUES (?)', (3,))
            
            cursor.execute(
                'INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)',
                (dc_id, 0, 0, auth_key, int(time.time()), user_id, 0)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False

    async def convert_tdata(self, tdata_path: str) -> Tuple[bool, str]:
        try:
            if not self.is_running:
                return False, tdata_path

            credentials = self.tdata_credentials.get(tdata_path)
            if not credentials:
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            proxy_str = await self.get_current_proxy()
            proxy = None
            if proxy_str:
                proxy_dict = parse_proxy(proxy_str, self.proxy_data.get('type', 'http'))
                if proxy_dict:
                    proxy = to_telethon(proxy_dict)

            try:
                with ThreadPoolExecutor() as executor:
                    tdesk = await asyncio.wait_for(
                        self._loop.run_in_executor(
                            executor,
                            lambda: TDesktop(tdata_path)
                        ),
                        timeout=5
                    )
            except asyncio.TimeoutError:
                self.progress.emit('unknown.session', 'Ошибка (Load timeout)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            if not tdesk:
                self.progress.emit('unknown.session', 'Ошибка (Failed to load)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            client = None
            try:
                client = await asyncio.wait_for(
                    tdesk.ToTelethon(
                        session=StringSession(),
                        flag=UseCurrentSession,
                        api=API.TelegramDesktop,
                        proxy=proxy
                    ),
                    timeout=10
                )
            except asyncio.TimeoutError:
                self.progress.emit('unknown.session', 'Ошибка (Connection timeout)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            if not client:
                self.progress.emit('unknown.session', 'Ошибка (Client creation failed)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            try:
                await asyncio.wait_for(client.connect(), timeout=8)
            except asyncio.TimeoutError:
                try:
                    await client.disconnect()
                except:
                    pass
                self.progress.emit('unknown.session', 'Ошибка (Connect timeout)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            if not await client.is_user_authorized():
                self.progress.emit('unknown.session', 'Ошибка (Not authorized)', 0, 0)
                try:
                    await client.disconnect()
                except:
                    pass
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

            try:
                me = await asyncio.wait_for(client.get_me(), timeout=5)
            except asyncio.TimeoutError:
                self.progress.emit('unknown.session', 'Ошибка (Get user timeout)', 0, 0)
                try:
                    await client.disconnect()
                except:
                    pass
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path
            user_id = me.id
            dc_id = client.session.dc_id
            auth_key_data = client.session.auth_key.key

            try:
                await client.disconnect()
            except:
                pass

            session_format = self._detect_session_format(tdesk)
            session_name = f"{user_id}_{session_format}.session"
            session_path = os.path.join(self.output_dir, session_name)

            if session_format == 'telethon':
                success = self._create_telethon_session(session_path, auth_key_data, dc_id, user_id)
            else:
                success = self._create_pyrogram_session(session_path, auth_key_data, dc_id, user_id)

            if success:
                self.progress.emit(session_name, 'Конвертирован', 0, 0)
                async with self._count_lock:
                    self.success_count += 1
                return True, tdata_path
            else:
                self.progress.emit(session_name, 'Ошибка (Session creation failed)', 0, 0)
                async with self._count_lock:
                    self.fail_count += 1
                return False, tdata_path

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.progress.emit('unknown.session', f'Ошибка ({str(e)[:30]})', 0, 0)
            async with self._count_lock:
                self.fail_count += 1
            return False, tdata_path

    async def convert_all_tdata(self):
        total = len(self.tdata_folders)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def bounded_convert(tdata_path):
            async with semaphore:
                if not self.is_running:
                    return False, tdata_path
                return await self.convert_tdata(tdata_path)

        tasks = {}
        for tdata_path in self.tdata_folders:
            if not self.is_running:
                break
            task = asyncio.create_task(bounded_convert(tdata_path))
            self._tasks.add(task)
            tasks[task] = tdata_path

        if not self.is_running:
            for task in tasks.keys():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks.keys(), return_exceptions=True)
            return

        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.ALL_COMPLETED)

        for task in pending:
            if not task.done():
                task.cancel()
        
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self.convert_all_tdata())
        except Exception:
            pass
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            self._loop.close()
            
            summary = f'Convert completed! Valid: {self.success_count} Invalid: {self.fail_count}'
            self.finished_signal.emit(summary, self.success_count, self.fail_count)


class TDataToSessionConverter:
    def __init__(self):
        self.thread = None

    def start(self, tdata_folders, proxies, proxy_data, api_credentials_list, output_format='auto'):
        if self.thread and self.thread.isRunning():
            return False
        
        self.thread = TDataToSessionThread(
            tdata_folders,
            proxies,
            proxy_data,
            api_credentials_list,
            output_format
        )
        self.thread.start()
        return True

    def stop(self):
        if self.thread:
            self.thread.stop()

    def is_running(self):
        return self.thread and self.thread.isRunning()
