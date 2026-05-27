import os
import shutil
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
import asyncio
import re
from PyQt6.QtCore import QThread, pyqtSignal
from pyrogram import Client
from pyrogram.errors import (
    AuthKeyUnregistered, UserDeactivated,
    SessionRevoked, AuthKeyDuplicated, PhoneNumberInvalid, FloodWait
)
from pyrogram.enums import ChatType, ChatMemberStatus
from telethon import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError,
    AuthKeyUnregisteredError, UserDeactivatedBanError
)
from telethon.tl.functions.payments import GetStarsStatusRequest, GetSavedStarGiftsRequest
from telethon.tl.types import Channel
from src.core.sessions import load_data, copy_files, cleanup_temp, detect_library
from src.core.devices import PROFILES, ROTATION_INTERVAL
from src.utils.proxy import parse_proxy, to_pyrogram, to_telethon


TIMEOUT = 15
PROXY_ROTATION = 15
MAX_CONCURRENT = 10
MAX_CONCURRENT_API = 5
GIFTS_LIMIT = 100
DIALOGS_LIMIT = 200
CHANNELS_TIMEOUT = 12
MAX_RETRIES = 2


class CheckerThread(QThread):
    progress = pyqtSignal(str, str, int, int, dict)
    finished_signal = pyqtSignal(str, int, int)
    log_signal = pyqtSignal(str)

    def __init__(self, sessions, proxies, proxy_data, settings, library, api_credentials_list=None):
        super().__init__()
        self.sessions = sessions
        self.proxies = proxies
        self.proxy_data = proxy_data
        self.settings = settings
        self.library = library
        self.api_credentials_list = api_credentials_list or []
        self.is_running = True
        self.output_dir = self._create_output_directory()
        self.current_proxy_index = 0
        self.checks_on_current_proxy = 0
        self.checks_per_proxy = PROXY_ROTATION
        self._proxy_lock = asyncio.Lock()
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
        base_dir = os.path.join('checker', timestamp)
        os.makedirs(os.path.join(base_dir, 'valid', 'all'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'valid', 'premium'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'valid', 'crypto'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'invalid'), exist_ok=True)
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
            if self.checks_on_current_proxy >= self.checks_per_proxy:
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
                self.checks_on_current_proxy = 0
            self.checks_on_current_proxy += 1
            return self.proxies[self.current_proxy_index]

    async def check_session(self, session_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        library = self.library
        if library == 'auto':
            library = detect_library(session_path)

        if library == 'pyrogram':
            return await self._check_pyrogram(session_path)
        else:
            return await self._check_telethon(session_path)

    async def _check_telethon(self, session_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        for attempt in range(MAX_RETRIES):
            temp_session = None
            client = None
            try:
                data = load_data(session_path, self.session_credentials.get(session_path))
                if not data:
                    return False, session_path, {}

                session_name, _, session_data = data
                if session_path in self.session_devices:
                    session_data = {**session_data, **self.session_devices[session_path]}
                temp_session = copy_files(session_path, session_name)

                proxy_line = await self.get_current_proxy()
                proxy_data = parse_proxy(proxy_line, self.proxy_data['format']) if proxy_line else None
                proxy = to_telethon(proxy_data, self.proxy_data['type']) if proxy_data else None

                client = TelegramClient(
                    temp_session,
                    session_data['api_id'],
                    session_data['api_hash'],
                    device_model=session_data.get('device', ''),
                    system_version=session_data.get('sdk', ''),
                    app_version=session_data.get('app_version', ''),
                    lang_code=session_data.get('lang_code', ''),
                    system_lang_code=session_data.get('system_lang_code', ''),
                    proxy=proxy,
                    timeout=TIMEOUT,
                    connection_retries=0,
                    retry_delay=0
                )

                await asyncio.wait_for(client.connect(), timeout=TIMEOUT)
                if not await client.is_user_authorized():
                    return False, session_path, {}

                me = await asyncio.wait_for(client.get_me(), timeout=TIMEOUT)
                info = await self._collect_telethon_info(client, me)
                return True, session_path, info

            except (AuthKeyUnregisteredError, PhoneNumberInvalidError, UserDeactivatedBanError):
                return False, session_path, {}
            except (asyncio.TimeoutError, ConnectionError, OSError):
                if attempt == MAX_RETRIES - 1:
                    return False, session_path, {}
                await asyncio.sleep(0.5)
                continue
            except Exception:
                return False, session_path, {}
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                cleanup_temp(temp_session)

        return False, session_path, {}

    async def _collect_telethon_info(self, client: TelegramClient, me) -> Dict[str, Any]:
        info = {}

        if self.settings.get('check_premium', False):
            info['premium'] = getattr(me, 'premium', False)

        if self.settings.get('check_crypto_bots', False):
            info['crypto_balance'] = await self._check_crypto_telethon(client)

        if self.settings.get('check_stars', False):
            try:
                stars_status = await asyncio.wait_for(
                    client(GetStarsStatusRequest(peer='me', ton=False)),
                    timeout=TIMEOUT
                )
                if hasattr(stars_status, 'balance'):
                    balance = stars_status.balance
                    info['stars'] = balance.amount if hasattr(balance, 'amount') else int(balance) if balance else 0
                else:
                    info['stars'] = 0
            except Exception:
                info['stars'] = 0

        if self.settings.get('check_gifts', False):
            try:
                gifts_result = await asyncio.wait_for(
                    client(GetSavedStarGiftsRequest(
                        peer='me',
                        offset='',
                        limit=GIFTS_LIMIT,
                        exclude_unsaved=True,
                        exclude_saved=True,
                        exclude_unlimited=True,
                        exclude_upgradable=True,
                        exclude_unupgradable=True,
                        exclude_hosted=True
                    )),
                    timeout=TIMEOUT
                )
                info['nft'] = len(gifts_result.gifts) if hasattr(gifts_result, 'gifts') else 0
            except Exception:
                info['nft'] = 0

        if self.settings.get('check_channels', False):
            try:
                async def count_admin_channels():
                    admin_count = 0
                    checked = 0
                    async for dialog in client.iter_dialogs(limit=DIALOGS_LIMIT):
                        checked += 1
                        if isinstance(dialog.entity, Channel):
                            if dialog.entity.creator or dialog.entity.admin_rights:
                                admin_count += 1
                        if checked >= DIALOGS_LIMIT:
                            break
                    return admin_count

                info['admin_groups'] = await asyncio.wait_for(
                    count_admin_channels(),
                    timeout=CHANNELS_TIMEOUT
                )
            except asyncio.TimeoutError:
                info['admin_groups'] = 0
            except Exception:
                info['admin_groups'] = 0

        return info

    async def _check_crypto_telethon(self, client: TelegramClient) -> str:
        try:
            cryptobot_balance = None
            try:
                await client.send_message('@CryptoBot', '/wallet')
                await asyncio.sleep(0.5)
                messages = await client.get_messages('@CryptoBot', limit=3)
                for msg in messages:
                    if msg.text and not msg.out:
                        match = re.search(r'~[^(]+\(\$([\d.]+)\)', msg.text)
                        if match:
                            cryptobot_balance = f"{match.group(1)}$"
                            break
            except Exception:
                pass

            xrocket_balance = None
            try:
                await client.send_message('@xRocket', '/start')
                await asyncio.sleep(0.5)
                messages = await client.get_messages('@xRocket', limit=3)
                for msg in messages:
                    if msg.reply_markup and not msg.out:
                        for row in msg.reply_markup.rows:
                            for button in row.buttons:
                                if hasattr(button, 'text'):
                                    match = re.search(r'\(([\d.]+)\s*\$\)', button.text)
                                    if match:
                                        xrocket_balance = f"{match.group(1)}$"
                                        break
                        if xrocket_balance:
                            break
            except Exception:
                pass

            results = []
            if cryptobot_balance is not None:
                results.append(f"CryptoBot:{cryptobot_balance}")
            if xrocket_balance is not None:
                results.append(f"xRocket:{xrocket_balance}")

            return ' | '.join(results) if results else None
        except Exception:
            return None

    async def _check_pyrogram(self, session_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        for attempt in range(MAX_RETRIES):
            temp_session = None
            try:
                data = load_data(session_path, self.session_credentials.get(session_path))
                if not data:
                    return False, session_path, {}

                session_name, _, session_data = data
                if session_path in self.session_devices:
                    session_data = {**session_data, **self.session_devices[session_path]}
                temp_session = copy_files(session_path, session_name)
                temp_dir = os.path.dirname(temp_session)

                proxy_line = await self.get_current_proxy()
                proxy_data = parse_proxy(proxy_line, self.proxy_data['format']) if proxy_line else None
                proxy = to_pyrogram(proxy_data, self.proxy_data['type']) if proxy_data else None

                client = Client(
                    name=session_name,
                    api_id=session_data['api_id'],
                    api_hash=session_data['api_hash'],
                    workdir=temp_dir,
                    device_model=session_data.get('device'),
                    system_version=session_data.get('sdk'),
                    app_version=session_data.get('app_version'),
                    lang_code=session_data.get('lang_code'),
                    proxy=proxy,
                    no_updates=True,
                    sleep_threshold=0,
                    max_concurrent_transmissions=5
                )

                await asyncio.wait_for(client.connect(), timeout=TIMEOUT)

                try:
                    me = await asyncio.wait_for(client.get_me(), timeout=TIMEOUT)
                    info = await self._collect_pyrogram_info(client, me)
                    await client.disconnect()
                    return True, session_path, info
                except Exception:
                    await client.disconnect()
                    raise

            except (AuthKeyUnregistered, UserDeactivated, SessionRevoked,
                    AuthKeyDuplicated, PhoneNumberInvalid):
                return False, session_path, {}
            except FloodWait:
                return True, session_path, {}
            except (asyncio.TimeoutError, ConnectionError, OSError):
                if attempt == MAX_RETRIES - 1:
                    return False, session_path, {}
                await asyncio.sleep(0.5)
                continue
            except Exception:
                return False, session_path, {}
            finally:
                cleanup_temp(temp_session)

        return False, session_path, {}

    async def _collect_pyrogram_info(self, client: Client, me) -> Dict[str, Any]:
        info = {}

        if self.settings.get('check_premium', False):
            info['premium'] = getattr(me, 'is_premium', False)

        if self.settings.get('check_crypto_bots', False):
            info['crypto_balance'] = await self._check_crypto_pyrogram(client)

        if self.settings.get('check_stars', False):
            try:
                stars_balance = await asyncio.wait_for(client.get_stars_balance(), timeout=TIMEOUT)
                info['stars'] = int(stars_balance) if stars_balance else 0
            except Exception:
                info['stars'] = 0

        if self.settings.get('check_gifts', False):
            try:
                nft_count = 0
                async for gift in client.get_chat_gifts(
                    "me",
                    exclude_unlimited=True,
                    exclude_upgradable=True,
                    exclude_non_upgradable=True,
                    exclude_saved=True,
                    exclude_unsaved=True,
                    exclude_hosted=True,
                    exclude_without_colors=True
                ):
                    nft_count += 1
                info['nft'] = nft_count
            except Exception:
                info['nft'] = 0

        if self.settings.get('check_channels', False):
            try:
                async def count_admin_channels():
                    admin_count = 0
                    checked = 0
                    async for dialog in client.get_dialogs(limit=DIALOGS_LIMIT):
                        checked += 1
                        chat = dialog.chat
                        if chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                            try:
                                me_member = await client.get_chat_member(chat.id, "me")
                                if me_member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                                    admin_count += 1
                            except Exception:
                                pass
                        if checked >= DIALOGS_LIMIT:
                            break
                    return admin_count

                info['admin_groups'] = await asyncio.wait_for(
                    count_admin_channels(),
                    timeout=CHANNELS_TIMEOUT
                )
            except asyncio.TimeoutError:
                info['admin_groups'] = 0
            except Exception:
                info['admin_groups'] = 0

        return info

    async def _check_crypto_pyrogram(self, client: Client) -> str:
        try:
            cryptobot_balance = None
            try:
                await client.send_message('@CryptoBot', '/wallet')
                await asyncio.sleep(0.5)
                async for message in client.get_chat_history('@CryptoBot', limit=3):
                    if message.text and not message.outgoing:
                        match = re.search(r'~[^(]+\(\$([\d.]+)\)', message.text)
                        if match:
                            cryptobot_balance = f"{match.group(1)}$"
                            break
            except Exception:
                pass

            xrocket_balance = None
            try:
                await client.send_message('@xRocket', '/start')
                await asyncio.sleep(0.5)
                async for message in client.get_chat_history('@xRocket', limit=3):
                    if message.reply_markup and hasattr(message.reply_markup, 'inline_keyboard') and not message.outgoing:
                        for row in message.reply_markup.inline_keyboard:
                            for button in row:
                                if hasattr(button, 'text'):
                                    match = re.search(r'\(([\d.]+)\s*\$\)', button.text)
                                    if match:
                                        xrocket_balance = f"{match.group(1)}$"
                                        break
                        if xrocket_balance:
                            break
            except Exception:
                pass

            results = []
            if cryptobot_balance is not None:
                results.append(f"CryptoBot:{cryptobot_balance}")
            if xrocket_balance is not None:
                results.append(f"xRocket:{xrocket_balance}")

            return ' | '.join(results) if results else None
        except Exception:
            return None

    async def check_all_sessions(self) -> None:
        valid_count = 0
        invalid_count = 0
        concurrent = MAX_CONCURRENT_API if self.api_credentials_list else MAX_CONCURRENT
        semaphore = asyncio.Semaphore(concurrent)

        async def check_with_semaphore(session_path: str) -> Tuple[bool, str, Dict[str, Any]]:
            async with semaphore:
                if not self.is_running:
                    return None, None, {}
                return await self.check_session(session_path)

        tasks = {asyncio.create_task(check_with_semaphore(path)) for path in self.sessions}
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

                        is_valid, path, info = result
                        session_name = os.path.basename(path)

                        if is_valid:
                            valid_count += 1
                            self.progress.emit(session_name, 'valid', valid_count, invalid_count, info)
                            self._copy_to_output(path, 'valid', info)
                        else:
                            invalid_count += 1
                            self.progress.emit(session_name, 'invalid', valid_count, invalid_count, {})
                            self._copy_to_output(path, 'invalid', {})
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        continue
        finally:
            self._tasks.clear()

        self.finished_signal.emit(self.output_dir, valid_count, invalid_count)

    def _copy_to_output(self, session_path: str, status: str, info: Dict[str, Any]) -> None:
        try:
            session_name = os.path.basename(session_path)
            session_name_without_ext = os.path.splitext(session_name)[0]
            session_dir = os.path.dirname(session_path)
            json_path = os.path.join(session_dir, f"{session_name_without_ext}.json")

            if status == 'invalid':
                dest_dir = os.path.join(self.output_dir, 'invalid')
                shutil.copy2(session_path, os.path.join(dest_dir, session_name))
                if os.path.exists(json_path):
                    shutil.copy2(json_path, os.path.join(dest_dir, f"{session_name_without_ext}.json"))
            else:
                all_dir = os.path.join(self.output_dir, 'valid', 'all')
                shutil.copy2(session_path, os.path.join(all_dir, session_name))
                if os.path.exists(json_path):
                    shutil.copy2(json_path, os.path.join(all_dir, f"{session_name_without_ext}.json"))

                if info.get('premium', False):
                    premium_dir = os.path.join(self.output_dir, 'valid', 'premium')
                    shutil.copy2(session_path, os.path.join(premium_dir, session_name))
                    if os.path.exists(json_path):
                        shutil.copy2(json_path, os.path.join(premium_dir, f"{session_name_without_ext}.json"))

                crypto_balance = info.get('crypto_balance')
                if crypto_balance and crypto_balance is not None:
                    has_balance = False
                    if 'CryptoBot:' in crypto_balance:
                        amount = crypto_balance.split('CryptoBot:')[1].split('$')[0]
                        if float(amount) > 0:
                            has_balance = True
                    if 'xRocket:' in crypto_balance and not has_balance:
                        amount = crypto_balance.split('xRocket:')[1].split('$')[0] if 'xRocket:' in crypto_balance else '0'
                        if float(amount) > 0:
                            has_balance = True

                    if has_balance:
                        crypto_dir = os.path.join(self.output_dir, 'valid', 'crypto')
                        shutil.copy2(session_path, os.path.join(crypto_dir, session_name))
                        if os.path.exists(json_path):
                            shutil.copy2(json_path, os.path.join(crypto_dir, f"{session_name_without_ext}.json"))
        except Exception:
            pass

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self.check_all_sessions())
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
            self._loop = None
            loop.close()


class SessionChecker:

    def __init__(self, sessions: List[str], proxies: List[str], proxy_data: Dict[str, Any],
                 settings: Dict[str, Any], view, library: str,
                 api_credentials_list: Optional[List[Dict[str, Any]]] = None):
        self.sessions = sessions
        self.proxies = proxies
        self.proxy_data = proxy_data
        self.settings = settings
        self.library = library
        self.api_credentials_list = api_credentials_list or []
        self.view = view
        self.thread = None

    def start(self) -> None:
        self.view.toggle_start_button(False)
        self.view.log('Starting checker...', 'info')

        self.thread = CheckerThread(
            self.sessions,
            self.proxies,
            self.proxy_data,
            self.settings,
            self.library,
            self.api_credentials_list
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.finished_signal.connect(self._on_finished)
        self.thread.log_signal.connect(self._on_log)
        self.thread.start()

        self.view.set_progress(0, len(self.sessions))

    def stop(self) -> None:
        if self.thread:
            self.thread.stop()
            self.view.log('Stopping checker...', 'warning')

    def _on_progress(self, session_name: str, status: str, valid_count: int,
                     invalid_count: int, info: Dict[str, Any]) -> None:
        try:
            if status == 'valid':
                parts = [session_name, 'Valid']

                if 'premium' in info:
                    parts.append(f"Premium:{'True' if info['premium'] else 'False'}")

                if 'stars' in info:
                    parts.append(f"Stars:{info['stars']}")

                if 'nft' in info:
                    parts.append(f"NFT:{info['nft']}")

                if 'admin_groups' in info:
                    parts.append(f"AdminGroups:{info['admin_groups']}")

                if 'crypto_balance' in info and info['crypto_balance'] is not None:
                    parts.append(f"Crypto:{info['crypto_balance']}")

                self.view.log(' | '.join(parts), 'success')
            else:
                self.view.log(f'{session_name} | Invalid', 'error')

            self.view.set_progress(valid_count + invalid_count, len(self.sessions))
        except RuntimeError:
            pass

    def _on_finished(self, output_dir: str, valid_count: int, invalid_count: int) -> None:
        try:
            self.view.toggle_start_button(True)
            self.view.reset_progress()
            self.view.log(f'Check completed!\n\nValid: {valid_count}\n\nInvalid: {invalid_count}', 'success')
            self.view.log(f'Results saved to: {output_dir}', 'info')
        except RuntimeError:
            pass
        self.thread = None

    def _on_log(self, message: str) -> None:
        try:
            self.view.log(message, 'warning')
        except RuntimeError:
            pass
