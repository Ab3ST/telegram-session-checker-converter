from pathlib import Path
from typing import List


def find_tdata_folders(root_path: str) -> List[str]:
    tdata_folders = []
    root = Path(root_path)
    
    if not root.exists() or not root.is_dir():
        return []
    
    def is_tdata_folder(folder: Path) -> bool:
        has_key_datas = (folder / 'key_datas').exists()
        has_d877_files = False
        try:
            has_d877_files = any(folder.glob('D877F783D5D3EF8C*'))
        except (PermissionError, OSError):
            pass
        return has_key_datas or has_d877_files
    
    try:
        for item in root.rglob('*'):
            if item.is_dir():
                try:
                    if is_tdata_folder(item):
                        tdata_folders.append(str(item.resolve()))
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        pass
    
    return sorted(set(tdata_folders))


def validate_tdata_folder(folder_path: str) -> bool:
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        return False
    
    has_key_datas = (folder / 'key_datas').exists()
    has_d877_files = False
    try:
        has_d877_files = any(folder.glob('D877F783D5D3EF8C*'))
    except (PermissionError, OSError):
        pass
    
    return has_key_datas or has_d877_files
