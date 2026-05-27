import re
import socks
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ProxyInfo:
    protocol: str
    host: str
    port: int
    username: str = ''
    password: str = ''
    
    def to_url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'host': self.host,
            'port': str(self.port),
            'login': self.username,
            'password': self.password,
            'protocol': self.protocol
        }


def parse_proxy_auto(line: str) -> List[ProxyInfo]:
    line = line.strip()
    if not line or line.startswith('#'):
        return []
    
    if '://' in line:
        if '@' in line:
            match = re.match(r'(https?|socks[45]?)://(.+):(.+)@([\d\.]+|[\w\.-]+):(\d+)', line)
            if match:
                protocol, user, pwd, host, port = match.groups()
                return [ProxyInfo(protocol, host, int(port), user, pwd)]
        else:
            match = re.match(r'(https?|socks[45]?)://([\d\.]+|[\w\.-]+):(\d+)', line)
            if match:
                protocol, host, port = match.groups()
                return [ProxyInfo(protocol, host, int(port))]
        return []
    
    if '@' in line:
        match = re.match(r'(.+):(.+)@([\d\.]+|[\w\.-]+):(\d+)', line)
        if match:
            user, pwd, host, port = match.groups()
            return [
                ProxyInfo('socks5', host, int(port), user, pwd),
                ProxyInfo('http', host, int(port), user, pwd)
            ]
        return []
    
    parts = line.split(':')
    if len(parts) == 2:
        host, port_str = parts
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return [
                    ProxyInfo('socks5', host, port),
                    ProxyInfo('http', host, port)
                ]
        except ValueError:
            pass
        return []
    
    if len(parts) == 4:
        if parts[0].replace('.', '').isdigit() or '.' in parts[0]:
            host, port_str, user, pwd = parts
        else:
            user, pwd, host, port_str = parts
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return [
                    ProxyInfo('socks5', host, port, user, pwd),
                    ProxyInfo('http', host, port, user, pwd)
                ]
        except ValueError:
            pass
    
    return []


def parse_proxy(proxy_line: str, proxy_format: str = 'auto') -> Optional[Dict[str, str]]:
    proxies = parse_proxy_auto(proxy_line)
    if proxies:
        return proxies[0].to_dict()
    return None


def to_pyrogram(proxy_data: Dict[str, str], proxy_type: str) -> Optional[Dict[str, Any]]:
    if not proxy_data:
        return None
    if proxy_type == 'auto':
        proxy_type = proxy_data.get('protocol', 'socks5')
    result = {
        'scheme': proxy_type,
        'hostname': proxy_data['host'],
        'port': int(proxy_data['port'])
    }
    if proxy_data.get('login'):
        result['username'] = proxy_data['login']
        result['password'] = proxy_data['password']
    return result


def to_telethon(proxy_data: Dict[str, str], proxy_type: str = 'socks5') -> Optional[Tuple]:
    if not proxy_data:
        return None

    if proxy_type == 'auto':
        proxy_type = proxy_data.get('protocol', 'socks5')

    proxy_type_map = {
        'socks5': socks.SOCKS5,
        'socks4': socks.SOCKS4,
        'http': socks.HTTP,
        'https': socks.HTTP
    }

    if proxy_data.get('login'):
        return (
            proxy_type_map.get(proxy_type, socks.SOCKS5),
            proxy_data['host'],
            int(proxy_data['port']),
            True,
            proxy_data['login'],
            proxy_data['password']
        )
    else:
        return (
            proxy_type_map.get(proxy_type, socks.SOCKS5),
            proxy_data['host'],
            int(proxy_data['port'])
        )


def to_url(proxy_data: Dict[str, str], proxy_type: str) -> str:
    if proxy_data.get('login'):
        return f"{proxy_type}://{proxy_data['login']}:{proxy_data['password']}@{proxy_data['host']}:{proxy_data['port']}"
    return f"{proxy_type}://{proxy_data['host']}:{proxy_data['port']}"
