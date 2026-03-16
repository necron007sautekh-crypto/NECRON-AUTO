#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v27 — JSON с метаданными подписки
- Корневой объект с version, remarks, announce и servers
- Каждый сервер — отдельный конфиг
- Автообновление через Actions (раз в 5 часов)
"""

import requests
import json
import time
import os
import re
import sys
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "27"
VERSION_FILE = "version.txt"
SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

# ================= ФУНКЦИИ =================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_next_version() -> str:
    current = 0
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                current = int(f.read().strip())
        except:
            pass
    next_ver = current + 1
    with open(VERSION_FILE, 'w') as f:
        f.write(str(next_ver))
    return f"{VERSION_CORE}.{next_ver}"

def parse_vless_url(url: str) -> Dict[str, Any]:
    result = {
        'uuid': None,
        'host': None,
        'port': 443,
        'params': {},
        'comment': ''
    }
    try:
        if not url.startswith('vless://'):
            return result
        without_proto = url[8:]
        if '#' in without_proto:
            main_part, comment = without_proto.split('#', 1)
            result['comment'] = '#' + comment
        else:
            main_part = without_proto
        if '?' in main_part:
            host_part, query = main_part.split('?', 1)
            params = urllib.parse.parse_qs(query)
            for key, value in params.items():
                if isinstance(value, list) and len(value) > 0:
                    result['params'][key] = value[0]
        else:
            host_part = main_part
        if '@' in host_part:
            uuid, host_with_port = host_part.split('@', 1)
            result['uuid'] = uuid
            if ':' in host_with_port:
                host, port_str = host_with_port.split(':', 1)
                result['host'] = host
                try:
                    result['port'] = int(port_str)
                except:
                    pass
            else:
                result['host'] = host_with_port
    except Exception as e:
        log(f"⚠️ Ошибка парсинга: {e}")
    return result

def extract_flag_from_comment(comment: str) -> str:
    try:
        decoded = unquote(comment)
        flag_match = re.search(r'([🇦-🇿]{2})', decoded)
        if flag_match:
            return flag_match.group(1)
    except:
        pass
    return '🌐'

def extract_country_from_comment(comment: str) -> str:
    flag = extract_flag_from_comment(comment)
    country_map = {
        '🇫🇮': 'Финляндия', '🇩🇪': 'Германия', '🇳🇱': 'Нидерланды',
        '🇷🇺': 'Россия', '🇺🇸': 'США', '🇬🇧': 'Великобритания',
        '🇫🇷': 'Франция', '🇸🇬': 'Сингапур', '🇸🇪': 'Швеция',
        '🇵🇱': 'Польша', '🇪🇪': 'Эстония', '🇪🇸': 'Испания',
        '🇹🇷': 'Турция', '🇭🇺': 'Венгрия', '🇮🇹': 'Италия',
        '🇳🇴': 'Норвегия', '🇱🇺': 'Люксембург', '🇨🇿': 'Чехия',
        '🇦🇹': 'Австрия', '🇨🇦': 'Канада', '🇯🇵': 'Япония',
        '🇦🇪': 'ОАЭ', '🇮🇳': 'Индия', '🇧🇷': 'Бразилия',
        '🇿🇦': 'ЮАР', '🇦🇺': 'Австралия', '🇪🇺': 'Европа',
        '🌐': 'Anycast',
    }
    return country_map.get(flag, 'Anycast')

def vless_to_server_object(vless_url: str, index: int) -> Dict[str, Any]:
    """Конвертирует vless:// в объект сервера для JSON"""
    parsed = parse_vless_url(vless_url)
    flag = extract_flag_from_comment(parsed['comment'])
    country = extract_country_from_comment(parsed['comment'])
    num = f"{index+1:03d}"
    remark = f"{flag} {num} {country} | 💠 | от catler"

    server = {
        "tag": f"s{index+1}",
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": parsed['host'],
                "port": parsed['port'],
                "users": [{
                    "id": parsed['uuid'],
                    "flow": parsed['params'].get('flow', ''),
                    "encryption": parsed['params'].get('encryption', 'none')
                }]
            }]
        },
        "streamSettings": {
            "network": parsed['params'].get('type', 'tcp'),
            "security": parsed['params'].get('security', 'none'),
        },
        "remarks": remark
    }

    if parsed['params'].get('security') == 'reality':
        server['streamSettings']['realitySettings'] = {
            "publicKey": parsed['params'].get('pbk', ''),
            "shortId": parsed['params'].get('sid', ''),
            "spiderX": parsed['params'].get('spx', ''),
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome'),
            "show": False
        }
    if parsed['params'].get('security') == 'tls':
        server['streamSettings']['tlsSettings'] = {
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome')
        }
    return server

def fetch_configs() -> List[str]:
    try:
        log(f"📡 Загрузка {SOURCE[:80]}...")
        resp = requests.get(SOURCE, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            configs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            log(f"✅ Загружено {len(configs)} конфигов")
            return configs
    except Exception as e:
        log(f"❌ Ошибка: {e}")
    return []

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Catwhite Configs Collector v27 — JSON с метаданными")
    version = get_next_version()
    log(f"📦 Версия: {version}")
    log(f"⏱️  Автообновление: каждые 5 часов")

    configs = fetch_configs()
    if not configs:
        log("❌ Нет конфигов")
        sys.exit(1)

    log(f"\n📊 Всего конфигов: {len(configs)}")

    servers = []
    finnish_count = 0
    other_count = 0
    anycast_count = 0
    failed = 0

    for idx, line in enumerate(configs):
        if not line.startswith('vless://'):
            failed += 1
            continue
        try:
            server = vless_to_server_object(line, idx)
            servers.append(server)
            country = extract_country_from_comment(line)
            if country == 'Финляндия':
                finnish_count += 1
            elif country == 'Anycast':
                anycast_count += 1
            else:
                other_count += 1
        except Exception as e:
            log(f"⚠️ Ошибка строки {idx+1}: {e}")
            failed += 1

    # Формируем итоговый JSON с метаданными
    output = {
        "version": version,
        "remarks": "🌐🌿CatwhiteVPN🌿🌐",
        "announce": f"⚡️Тгк @catlergememe версия: {version}⚡️",
        "support_url": "https://t.me/catlergememe/856",
        "web_page_url": "https://twinkalex1470-crypto.github.io/Catsite/",
        "servers": servers
    }

    with open('configs.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log(f"\n📊 Статистика:")
    log(f"   • Конвертировано: {len(servers)}")
    log(f"   • Не удалось: {failed}")
    log(f"   • 🇫🇮 Финских: {finnish_count}")
    log(f"   • 🌍 Других: {other_count}")
    log(f"   • 🌐 Anycast: {anycast_count}")
    log(f"✅ configs.json сохранён")

    # debug
    with open('debug.json', 'w') as f:
        json.dump({
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'total': len(configs),
            'converted': len(servers),
            'failed': failed,
        }, f, indent=2)

    log(f"\n✨ Готово! Ссылка:")
    log(f"https://twinkalex1470-crypto.github.io/CatwhiteAUTO/configs.json")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)