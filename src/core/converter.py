import os
import asyncio
import sqlite3
import shutil
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from telethon.sessions import MemorySession
from telethon.crypto import AuthKey
from telethon import TelegramClient
from opentele.api import UseCurrentSession
from src.core.sessions import load_data, copy_files, cleanup_temp
from src.core.devices import PROFILES, ROTATION_INTERVAL
from src.utils.proxy import parse_proxy, to_telethon


TIMEOUT = 15
PROXY_ROTATION = 15
MAX_CONCURRENT = 10
DC_IPS = {
    1: "149.154.175.53",
    2: "149.154.167.51",
    3: "149.154.175.100",
    4: "149.154.167.92",
    5: "91.108.56.130"
}


class ConversionThread(QThread):
    progress = pyqtSignal(str, str, int, int)
    finished_signal = pyqtSignal(str, int, int)

    def __init__(self, sessions, proxies, proxy_data, api_credentials_list=None):
        super().__init__()
        self.sessions = sessions
        self.proxies = proxies
        self.proxy_data = proxy_data
        self.api_credentials_list = api_credentials_list or []
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
        self.session_credentials = {
            path: self.api_credentials_list[i % len(self.api_credentials_list)]
            for i, path in enumerate(self.sessions)
        } if self.api_credentials_list else {}
        self.session_devices = {
            path: PROFILES[(i // ROTATION_INTERVAL) % len(PROFILES)]
            for i, path in enumerate(self.sessions)
        } if self.api_credentials_list else {}

    def _create_output_directory(self) -> str:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        base_dir = os.path.join('converter', timestamp)
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

    async def convert_session(self, session_path: str) -> Tuple[bool, str]:
        temp_session = None
        client = None

        try:
            data = load_data(session_path, self.session_credentials.get(session_path))
            if not data:
                return False, session_path

            session_name, _, session_data = data
            if session_path in self.session_devices:
                session_data = {**session_data, **self.session_devices[session_path]}
            temp_session = copy_files(session_path, session_name)

            conn = sqlite3.connect(temp_session)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            if not cursor.fetchone():
                conn.close()
                return False, session_path

            cursor.execute("SELECT dc_id, auth_key FROM sessions")
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, session_path

            dc_id, auth_key = row
            conn.close()

            session = MemorySession()
            session.set_dc(dc_id, DC_IPS.get(dc_id, "149.154.167.51"), 443)
            session.auth_key = AuthKey(data=auth_key)

            proxy_line = await self.get_current_proxy()
            proxy_data_parsed = parse_proxy(proxy_line, self.proxy_data['format']) if proxy_line else None
            proxy = to_telethon(proxy_data_parsed, self.proxy_data['type']) if proxy_data_parsed else None

            client = TelegramClient(
                session,
                session_data['api_id'],
                session_data['api_hash'],
                device_model=session_data.get('device', ''),
                system_version=session_data.get('sdk', ''),
                app_version=session_data.get('app_version', ''),
                lang_code=session_data.get('lang_code', 'en'),
                system_lang_code=session_data.get('system_lang_code', ''),
                proxy=proxy,
                timeout=TIMEOUT,
                connection_retries=0,
                retry_delay=0
            )

            await asyncio.wait_for(client.connect(), timeout=TIMEOUT)
            if not await client.is_user_authorized():
                return False, session_path

            if not self.is_running:
                return False, session_path

            me = await asyncio.wait_for(client.get_me(), timeout=TIMEOUT)
            if not me:
                return False, session_path

            if not self.is_running:
                return False, session_path

            tdesk_client = await client.ToTDesktop(flag=UseCurrentSession)
            output_path = os.path.join(self.output_dir, f"tdata_{me.id}")
            os.makedirs(output_path, exist_ok=True)
            await asyncio.to_thread(tdesk_client.SaveTData, output_path)

            try:
                session_dir = os.path.dirname(session_path)
                json_path = os.path.join(session_dir, f"{session_name}.json")
                if os.path.exists(json_path):
                    shutil.copy2(json_path, os.path.join(output_path, f"{session_name}.json"))
            except Exception:
                pass

            return True, session_path

        except Exception:
            return False, session_path
        finally:
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            cleanup_temp(temp_session)

    async def convert_all_sessions(self) -> None:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def convert_with_semaphore(session_path: str) -> Tuple[bool, str]:
            async with semaphore:
                if not self.is_running:
                    return None, None
                return await self.convert_session(session_path)

        tasks = {asyncio.create_task(convert_with_semaphore(path)) for path in self.sessions}
        self._tasks = set(tasks)

        try:
            pending = set(tasks)
            while pending:
                if not self.is_running:
                    for task in pending:
                        if not task.done():
                            task.cancel()
                    if pending:
                        await asyncio.wait(pending, timeout=1.0)
                    break

                done, pending = await asyncio.wait(
                    pending,
                    timeout=0.2,
                    return_when=asyncio.FIRST_COMPLETED
                )

                for task in done:
                    try:
                        result = task.result()
                        if result[0] is None and result[1] is None:
                            continue

                        success, path = result
                        session_name = os.path.basename(path)

                        async with self._count_lock:
                            if success:
                                self.success_count += 1
                                self.progress.emit(session_name, 'success', self.success_count, self.fail_count)
                            else:
                                self.fail_count += 1
                                self.progress.emit(session_name, 'fail', self.success_count, self.fail_count)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        continue
        finally:
            self._tasks.clear()

        self.finished_signal.emit(self.output_dir, self.success_count, self.fail_count)

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self.convert_all_sessions())
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
            self._loop = None
            loop.close()


class SessionConverter:

    def __init__(self, sessions: List[str], proxies: List[str], proxy_data: Dict[str, Any],
                 view, api_credentials_list: Optional[List[Dict[str, Any]]] = None):
        self.sessions = sessions
        self.proxies = proxies
        self.proxy_data = proxy_data
        self.api_credentials_list = api_credentials_list or []
        self.view = view
        self.thread = None

    def start(self) -> None:
        self.view.toggle_start_button(False)
        self.view.log('Запуск конвертации...', 'info')

        self.thread = ConversionThread(
            self.sessions,
            self.proxies,
            self.proxy_data,
            self.api_credentials_list
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.finished_signal.connect(self._on_finished)
        self.thread.start()

        self.view.set_progress(0, len(self.sessions))

    def stop(self) -> None:
        if self.thread:
            self.thread.stop()
            self.view.log('Остановка конвертации...', 'warning')

    def _on_progress(self, session_name: str, status: str, success_count: int, fail_count: int) -> None:
        try:
            if status == 'success':
                self.view.log(f'{session_name} | Конвертирован', 'success')
            else:
                self.view.log(f'{session_name} | Ошибка', 'error')

            self.view.set_progress(success_count + fail_count, len(self.sessions))
        except RuntimeError:
            pass

    def _on_finished(self, output_dir: str, success_count: int, fail_count: int) -> None:
        try:
            self.view.toggle_start_button(True)
            self.view.reset_progress()
            self.view.log(f'Конвертация завершена!\n\nУспешно: {success_count}\n\nОшибок: {fail_count}', 'success')
            self.view.log(f'Результаты сохранены в: {output_dir}', 'info')
        except RuntimeError:
            pass
        self.thread = None
