#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v31 — JSON внутри .txt
- Файл configs.txt
- Сначала метаданные (с #)
- Потом JSON-массив
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
VERSION_CORE = "31"
VERSION_FILE = "version.txt"
SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

DNS_SERVERS = [
    "https+local://1.1.1.1/dns-query",
    "https+local://8.8.8.8/dns-query",
    "77.88.8.8"
]

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
        '🇫🇮': 'Финляндия',
        '🇩🇪': 'Германия',
        '🇳🇱': 'Нидерланды',
        '🇷🇺': 'Россия',
        '🇺🇸': 'США',
        '🇬🇧': 'Великобритания',
        '🇫🇷': 'Франция',
        '🇸🇬': 'Сингапур',
        '🇸🇪': 'Швеция',
        '🇵🇱': 'Польша',
        '🇪🇪': 'Эстония',
        '🇪🇸': 'Испания',
        '🇹🇷': 'Турция',
        '🇭🇺': 'Венгрия',
        '🇮🇹': 'Италия',
        '🇳🇴': 'Норвегия',
        '🇱🇺': 'Люксембург',
        '🇨🇿': 'Чехия',
        '🇦🇹': 'Австрия',
        '🇨🇦': 'Канада',
        '🇯🇵': 'Япония',
        '🇦🇪': 'ОАЭ',
        '🇮🇳': 'Индия',
        '🇧🇷': 'Бразилия',
        '🇿🇦': 'ЮАР',
        '🇦🇺': 'Австралия',
        '🇪🇺': 'Европа',
        '🌐': 'Anycast',
    }
    return country_map.get(flag, 'Anycast')

def create_full_config(vless_url: str, index: int) -> Dict[str, Any]:
    parsed = parse_vless_url(vless_url)
    flag = extract_flag_from_comment(parsed['comment'])
    country = extract_country_from_comment(parsed['comment'])
    
    num = f"{index+1:03d}"
    remark = f"{flag} {num} {country} | 💠 | от catler"
    
    outbounds = [
        {
            "tag": "s1",
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
            }
        },
        {"protocol": "freedom", "tag": "direct"},
        {"protocol": "blackhole", "tag": "block"}
    ]
    
    if parsed['params'].get('security') == 'reality':
        outbounds[0]['streamSettings']['realitySettings'] = {
            "publicKey": parsed['params'].get('pbk', ''),
            "shortId": parsed['params'].get('sid', ''),
            "spiderX": parsed['params'].get('spx', ''),
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome'),
            "show": False
        }
    if parsed['params'].get('security') == 'tls':
        outbounds[0]['streamSettings']['tlsSettings'] = {
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome')
        }
    
    return {
        "dns": {"queryStrategy": "UseIPv4", "servers": DNS_SERVERS},
        "inbounds": [
            {"listen": "127.0.0.1", "port": 10808, "protocol": "socks", "settings": {"udp": True}, "tag": "socks"},
            {"listen": "127.0.0.1", "port": 10809, "protocol": "http", "tag": "http"}
        ],
        "meta": None,
        "outbounds": outbounds,
        "remarks": remark,
        "burstObservatory": {
            "pingConfig": {"destination": "https://www.google.com/generate_204", "interval": "1s", "sampling": 2, "timeout": "3s"},
            "subjectSelector": ["s1"]
        },
        "routing": {
            "balancers": [{
                "fallbackTag": "s1",
                "selector": ["s1"],
                "strategy": {
                    "settings": {"baselines": ["2s"], "expected": 1, "maxRTT": "3s", "tolerance": 0.3},
                    "type": "leastLoad"
                },
                "tag": "auto_bal"
            }],
            "domainStrategy": "IPIfNonMatch",
            "rules": [
                {"outboundTag": "block", "protocol": ["bittorrent"], "type": "field"},
                {"balancerTag": "auto_bal", "inboundTag": ["socks", "http"], "network": "tcp,udp", "type": "field"}
            ]
        }
    }

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
    log("🚀 Catwhite Configs Collector v31 — JSON внутри .txt")
    version = get_next_version()
    log(f"📦 Версия: {version}")

    configs = fetch_configs()
    if not configs:
        log("❌ Нет конфигов")
        sys.exit(1)

    log(f"\n📊 Всего конфигов: {len(configs)}")

    json_configs = []
    finnish_count = 0
    other_count = 0
    anycast_count = 0
    failed = 0

    for idx, line in enumerate(configs):
        if not line.startswith('vless://'):
            failed += 1
            continue
        try:
            config = create_full_config(line, idx)
            json_configs.append(config)
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

    # Формируем .txt файл с метаданными и JSON
    output_lines = [
        f"#profile-title: 🌐🌿CatwhiteVPN🌿🌐",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        f"#support-url: https://t.me/catlergememe/856",
        f"#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        f"#profile-update-interval: 5",
        "",
        json.dumps(json_configs, ensure_ascii=False, indent=None)
    ]

    output_file = 'configs.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    log(f"\n📊 Статистика:")
    log(f"   • Конвертировано: {len(json_configs)}")
    log(f"   • Не удалось: {failed}")
    log(f"   • 🇫🇮 Финских: {finnish_count}")
    log(f"   • 🌍 Других: {other_count}")
    log(f"   • 🌐 Anycast: {anycast_count}")
    log(f"✅ {output_file} сохранён")

    with open('debug.json', 'w') as f:
        json.dump({
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'total': len(configs),
            'converted': len(json_configs),
            'failed': failed,
        }, f, indent=2)

    log(f"\n✨ Готово! Ссылка:")
    log(f"https://twinkalex1470-crypto.github.io/CatwhiteAUTO/configs.txt")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)