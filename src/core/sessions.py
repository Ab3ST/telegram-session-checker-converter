import os
import json
import shutil
import tempfile
import sqlite3
from typing import Optional, Tuple, Dict, Any


SQLITE_EXTENSIONS = ['-wal', '-shm', '-journal']


def detect_library(session_path: str) -> str:
    try:
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        if 'peers' in tables:
            return 'pyrogram'
        elif 'entities' in tables or 'sent_files' in tables or 'update_state' in tables:
            return 'telethon'

        if 'sessions' in tables:
            return 'telethon'

        return 'telethon'
    except Exception:
        return 'telethon'


def load_data(
    session_path: str,
    api_credentials: Optional[Dict[str, Any]] = None
) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    session_name = os.path.splitext(os.path.basename(session_path))[0]
    session_dir = os.path.dirname(session_path)

    json_path = os.path.join(session_dir, f"{session_name}.json")

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        api_id = raw.get('app_id') or raw.get('api_id')
        api_hash = raw.get('app_hash') or raw.get('api_hash')

        if not api_id or not api_hash:
            return None

        session_data = {**raw, 'api_id': api_id, 'api_hash': api_hash}

    elif api_credentials:
        api_id = api_credentials.get('api_id')
        api_hash = api_credentials.get('api_hash')
        if not api_id or not api_hash:
            return None
        session_data = {'api_id': api_id, 'api_hash': api_hash}

    else:
        return None

    return session_name, session_dir, session_data


def copy_files(session_path: str, session_name: str) -> str:
    temp_dir = tempfile.mkdtemp()
    temp_session = os.path.join(temp_dir, session_name + '.session')
    shutil.copy2(session_path, temp_session)

    for ext in SQLITE_EXTENSIONS:
        extra_file = session_path + ext
        if os.path.exists(extra_file):
            shutil.copy2(extra_file, temp_session + ext)

    return temp_session


def cleanup_temp(temp_session: Optional[str]) -> None:
    if temp_session and os.path.exists(temp_session):
        temp_dir = os.path.dirname(temp_session)
        shutil.rmtree(temp_dir, ignore_errors=True)
