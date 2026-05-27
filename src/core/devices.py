from typing import Dict, Any


ROTATION_INTERVAL = 15

PROFILES: list[Dict[str, Any]] = [
    {'device': 'Samsung Galaxy S25 Ultra', 'sdk': 'Android 15', 'app_version': '10.14.5', 'lang_code': 'en', 'system_lang_code': 'en-US', 'lang_pack': 'android', 'system_lang_pack': 'en-US'},
    {'device': 'Xiaomi 14 Pro', 'sdk': 'Android 14', 'app_version': '10.13.1', 'lang_code': 'ru', 'system_lang_code': 'ru-RU', 'lang_pack': 'android', 'system_lang_pack': 'ru-RU'},
    {'device': 'Google Pixel 9 Pro', 'sdk': 'Android 15', 'app_version': '10.12.2', 'lang_code': 'en', 'system_lang_code': 'en-GB', 'lang_pack': 'android', 'system_lang_pack': 'en-GB'},
    {'device': 'OnePlus 13', 'sdk': 'Android 15', 'app_version': '10.11.0', 'lang_code': 'de', 'system_lang_code': 'de-DE', 'lang_pack': 'android', 'system_lang_pack': 'de-DE'},
    {'device': 'iPhone 16 Pro Max', 'sdk': 'iOS 18.3', 'app_version': '10.14.5', 'lang_code': 'en', 'system_lang_code': 'en-US', 'lang_pack': 'ios', 'system_lang_pack': 'en-US'},
    {'device': 'iPhone 15 Pro', 'sdk': 'iOS 17.7', 'app_version': '10.13.1', 'lang_code': 'ru', 'system_lang_code': 'ru-RU', 'lang_pack': 'ios', 'system_lang_pack': 'ru-RU'},
    {'device': 'Samsung Galaxy S24', 'sdk': 'Android 14', 'app_version': '10.10.1', 'lang_code': 'fr', 'system_lang_code': 'fr-FR', 'lang_pack': 'android', 'system_lang_pack': 'fr-FR'},
    {'device': 'OPPO Find X8 Pro', 'sdk': 'Android 15', 'app_version': '10.9.3', 'lang_code': 'en', 'system_lang_code': 'en-US', 'lang_pack': 'android', 'system_lang_pack': 'en-US'},
    {'device': 'Xiaomi 13T Pro', 'sdk': 'Android 13', 'app_version': '10.8.3', 'lang_code': 'uk', 'system_lang_code': 'uk-UA', 'lang_pack': 'android', 'system_lang_pack': 'uk-UA'},
    {'device': 'iPhone 16', 'sdk': 'iOS 18.2', 'app_version': '10.12.2', 'lang_code': 'en', 'system_lang_code': 'en-GB', 'lang_pack': 'ios', 'system_lang_pack': 'en-GB'},
    {'device': 'iPhone 14 Pro Max', 'sdk': 'iOS 17.4', 'app_version': '10.11.0', 'lang_code': 'de', 'system_lang_code': 'de-DE', 'lang_pack': 'ios', 'system_lang_pack': 'de-DE'},
    {'device': 'Realme GT 6', 'sdk': 'Android 14', 'app_version': '10.7.4', 'lang_code': 'es', 'system_lang_code': 'es-ES', 'lang_pack': 'android', 'system_lang_pack': 'es-ES'},
    {'device': 'Vivo X100 Pro', 'sdk': 'Android 14', 'app_version': '10.6.4', 'lang_code': 'pl', 'system_lang_code': 'pl-PL', 'lang_pack': 'android', 'system_lang_pack': 'pl-PL'},
    {'device': 'Nothing Phone 3', 'sdk': 'Android 15', 'app_version': '10.5.1', 'lang_code': 'en', 'system_lang_code': 'en-US', 'lang_pack': 'android', 'system_lang_pack': 'en-US'},
    {'device': 'iPhone 16 Plus', 'sdk': 'iOS 18.1', 'app_version': '10.10.1', 'lang_code': 'fr', 'system_lang_code': 'fr-FR', 'lang_pack': 'ios', 'system_lang_pack': 'fr-FR'},
    {'device': 'iPhone 13 Pro', 'sdk': 'iOS 16.7', 'app_version': '10.9.0', 'lang_code': 'ru', 'system_lang_code': 'ru-RU', 'lang_pack': 'ios', 'system_lang_pack': 'ru-RU'},
    {'device': 'Motorola Edge 50 Pro', 'sdk': 'Android 14', 'app_version': '10.4.1', 'lang_code': 'it', 'system_lang_code': 'it-IT', 'lang_pack': 'android', 'system_lang_pack': 'it-IT'},
    {'device': 'Samsung Galaxy A55', 'sdk': 'Android 14', 'app_version': '10.3.2', 'lang_code': 'tr', 'system_lang_code': 'tr-TR', 'lang_pack': 'android', 'system_lang_pack': 'tr-TR'},
    {'device': 'iPhone 15', 'sdk': 'iOS 17.5', 'app_version': '10.8.0', 'lang_code': 'en', 'system_lang_code': 'en-US', 'lang_pack': 'ios', 'system_lang_pack': 'en-US'},
    {'device': 'Google Pixel 8 Pro', 'sdk': 'Android 14', 'app_version': '10.2.0', 'lang_code': 'nl', 'system_lang_code': 'nl-NL', 'lang_pack': 'android', 'system_lang_pack': 'nl-NL'},
]


def get_profile(session_index: int) -> Dict[str, Any]:
    return PROFILES[(session_index // ROTATION_INTERVAL) % len(PROFILES)]
