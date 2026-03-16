#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v21.1 — исправленная проверка
"""

import requests
import json
import time
import os
import re
import socket
import sys
import ssl
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "21.1"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 300
MAX_PER_COUNTRY = 30
MAX_FINNISH = 30
TIMEOUT = 15
WORKERS = 8

# ================= СПИСОК ИСТОЧНИКОВ =================
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt",
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

def extract_config_parts(config_line: str) -> Dict[str, str]:
    if '#' in config_line:
        url, comment = config_line.split('#', 1)
        return {'url': url.strip(), 'comment': '#' + comment.strip()}
    return {'url': config_line.strip(), 'comment': ''}

def extract_host(config_url: str) -> str:
    m = re.search(r'@([^:]+)', config_url)
    if m:
        return m.group(1)
    m = re.search(r'(\d+\.\d+\.\d+\.\d+)', config_url)
    if m:
        return m.group(1)
    return None

def resolve_host(hostname: str) -> str:
    """Пробует получить IPv4, если не получается — IPv6"""
    try:
        return socket.gethostbyname(hostname)
    except:
        try:
            addrs = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            if addrs:
                return addrs[0][4][0]
        except:
            pass
    return None

def check_config(config_line: str) -> Dict[str, Any]:
    parts = extract_config_parts(config_line)
    url = parts['url']
    hostname = extract_host(url)
    if not hostname:
        return None

    port_match = re.search(r':(\d+)', url)
    port = int(port_match.group(1)) if port_match else 443
    
    sni_match = re.search(r'sni=([^&]+)', url)
    sni = sni_match.group(1) if sni_match else hostname

    # Резолвим хост заранее
    host = resolve_host(hostname)
    if not host:
        return None

    for attempt in range(2):
        try:
            start = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect((host, port))
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=sni)
            latency = (time.time() - start) * 1000
            ssl_sock.close()
            
            flag = extract_flag_from_comment(parts['comment'])
            if not is_allowed_flag(flag):
                return None
                
            return {
                'full_line': config_line,
                'url': url,
                'original_comment': parts['comment'],
                'flag': flag,
                'country': extract_country_from_comment(parts['comment']),
                'host': host,
                'port': port,
                'latency': round(latency, 2),
                'working': True
            }
            
        except ssl.SSLError as e:
            if 'WRONG_VERSION_NUMBER' in str(e):
                latency = (time.time() - start) * 1000
                flag = extract_flag_from_comment(parts['comment'])
                if not is_allowed_flag(flag):
                    return None
                return {
                    'full_line': config_line,
                    'url': url,
                    'original_comment': parts['comment'],
                    'flag': flag,
                    'country': extract_country_from_comment(parts['comment']),
                    'host': host,
                    'port': port,
                    'latency': round(latency, 2),
                    'working': True
                }
        except:
            time.sleep(1)
            continue
            
    return None

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
    }
    return country_map.get(flag, 'Anycast')

def is_allowed_flag(flag: str) -> bool:
    allowed_flags = {
        '🇫🇮', '🇩🇪', '🇳🇱', '🇷🇺', '🇺🇸', '🇬🇧', '🇫🇷', '🇸🇬', '🇸🇪', '🇵🇱',
        '🇪🇪', '🇪🇸', '🇹🇷', '🇭🇺', '🇮🇹', '🇳🇴', '🇱🇺', '🇨🇿', '🇦🇹', '🇨🇦',
        '🇯🇵', '🇦🇪', '🇮🇳', '🇧🇷', '🇿🇦', '🇦🇺', '🇪🇺'
    }
    return flag in allowed_flags

def fetch_configs(source: str) -> List[str]:
    try:
        resp = requests.get(source, timeout=15)
        if resp.status_code == 200:
            return resp.text.strip().split('\n')
    except:
        pass
    return []

def is_valid_config(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    if not (line.startswith('vless://') or line.startswith('vmess://')):
        return False
    return True

def generate_number(index: int) -> str:
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Старт сбора")
    version = get_next_version()
    log(f"📦 Версия: {version}")

    all_configs = []
    log(f"\n📡 Загрузка из {len(SOURCES)} источников:")
    
    for src in SOURCES:
        log(f"  {src[:80]}...")
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        all_configs.extend(valid)
        log(f"    ✅ Найдено {len(valid)} конфигов")

    if not all_configs:
        log("❌ Нет конфигов")
        sys.exit(1)

    unique = list(set(all_configs))
    log(f"\n📊 Уникальных: {len(unique)}")

    log(f"\n🔄 Проверка {len(unique)} конфигов...")
    working = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_line = {executor.submit(check_config, line): line for line in unique}
        for future in as_completed(future_to_line):
            checked += 1
            result = future.result()
            if result:
                working.append(result)
            if checked % 20 == 0:
                log(f"   Проверено {checked}/{len(unique)}, найдено {len(working)} рабочих")

    log(f"\n✅ Найдено рабочих: {len(working)}")
    
    if not working:
        log("❌ Нет рабочих")
        sys.exit(1)

    working.sort(key=lambda x: x['latency'])

    finnish_all = [c for c in working if c['country'] == 'Финляндия']
    finnish = finnish_all[:MAX_FINNISH]
    remaining = [c for c in working if c['country'] != 'Финляндия']
    
    log(f"\n🇫🇮 Финских: {len(finnish_all)} всего, взято {len(finnish)}")
    
    countries = {}
    for cfg in remaining:
        country = cfg['country']
        if country not in countries:
            countries[country] = []
        countries[country].append(cfg)
    
    selected_others = []
    for country, cfgs in countries.items():
        selected = cfgs[:MAX_PER_COUNTRY]
        selected_others.extend(selected)
        log(f"   {country}: взято {len(selected)} из {len(cfgs)}")
    
    selected_others.sort(key=lambda x: (x['country'], x['latency']))
    
    final_list = finnish + selected_others
    
    if len(final_list) > MAX_CONFIGS:
        final_list = finnish + selected_others[:MAX_CONFIGS - len(finnish)]
    
    log(f"\n📊 Итого: {len(final_list)} конфигов")
    log(f"   🇫🇮 Финских: {len(finnish)}")
    log(f"   🌍 Других: {len(final_list) - len(finnish)}")

    log("\n📝 Генерация configs.txt ...")
    output = [
        "#profile-title: 👾🌿CatwhiteVPN🌿👾",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]

    for idx, cfg in enumerate(final_list):
        num = generate_number(idx)
        line = f"{cfg['url']}#{cfg['flag']} {num} {cfg['country']} | 💠 | от catler"
        output.append(line)

    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    log(f"✅ configs.txt сохранён")

    debug = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'total_checked': len(unique),
        'working_found': len(working),
        'best_selected': len(final_list),
        'finnish_count': len(finnish),
        'finnish_total': len(finnish_all),
        'per_country': {c: len([x for x in final_list if x['country'] == c]) for c in set(x['country'] for x in final_list)},
        'avg_latency': round(sum(c['latency'] for c in final_list) / len(final_list), 1) if final_list else 0,
    }
    
    with open('configs_debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)

    log(f"\n✨ Готово! Средний пинг: {debug['avg_latency']} ms")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)