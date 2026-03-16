#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v22 — финальная версия
- Финские из igareck: без проверки (все)
- Остальные: проверяем
- Лимит: 300 всего
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
VERSION_CORE = "22"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 300
MAX_PER_COUNTRY = 30
TIMEOUT = 10
WORKERS = 10

# ================= ИСТОЧНИКИ =================
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt",
]

# Финские будем брать только из этих источников (igareck)
FINNISH_SOURCES = SOURCES[:3]  # первые три — от igareck

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

def check_config(config_line: str) -> Dict[str, Any]:
    """Проверяет только не-финские конфиги"""
    parts = extract_config_parts(config_line)
    url = parts['url']
    hostname = extract_host(url)
    if not hostname:
        return None

    port_match = re.search(r':(\d+)', url)
    port = int(port_match.group(1)) if port_match else 443
    
    sni_match = re.search(r'sni=([^&]+)', url)
    sni = sni_match.group(1) if sni_match else hostname

    try:
        start = time.time()
        
        # Пробуем резолв
        try:
            host = socket.gethostbyname(hostname)
        except:
            return None
        
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
        return None
    return None

def generate_number(index: int) -> str:
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Старт сбора (финские без проверки, остальные — с проверкой)")
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

    # Убираем дубликаты
    unique = list(set(all_configs))
    log(f"\n📊 Уникальных: {len(unique)}")

    # Разделяем на финские и остальные
    finnish_configs = []
    other_configs = []
    
    for line in unique:
        parts = extract_config_parts(line)
        flag = extract_flag_from_comment(parts['comment'])
        country = extract_country_from_comment(parts['comment'])
        if country == 'Финляндия':
            finnish_configs.append(line)
        else:
            other_configs.append(line)
    
    log(f"\n🇫🇮 Финских конфигов (без проверки): {len(finnish_configs)}")
    log(f"🌍 Остальных конфигов (будут проверены): {len(other_configs)}")

    # Финские просто добавляем (без проверки)
    finnish_working = []
    for line in finnish_configs:
        parts = extract_config_parts(line)
        flag = extract_flag_from_comment(parts['comment'])
        if is_allowed_flag(flag):
            finnish_working.append({
                'full_line': line,
                'url': parts['url'],
                'original_comment': parts['comment'],
                'flag': flag,
                'country': 'Финляндия',
                'host': extract_host(parts['url']) or 'unknown',
                'port': 443,
                'latency': 999,  # высокий пинг, но они всё равно будут первыми
                'working': True
            })
    
    log(f"✅ Финских добавлено: {len(finnish_working)}")

    # Проверяем остальные
    log(f"\n🔄 Проверка {len(other_configs)} остальных конфигов...")
    other_working = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_line = {executor.submit(check_config, line): line for line in other_configs}
        for future in as_completed(future_to_line):
            checked += 1
            result = future.result()
            if result:
                other_working.append(result)
            if checked % 20 == 0:
                log(f"   Проверено {checked}/{len(other_configs)}, найдено {len(other_working)} рабочих")

    log(f"\n✅ Найдено рабочих (не-финских): {len(other_working)}")

    # Сортируем остальные по скорости
    other_working.sort(key=lambda x: x['latency'])

    # Группируем по странам
    countries = {}
    for cfg in other_working:
        country = cfg['country']
        if country not in countries:
            countries[country] = []
        countries[country].append(cfg)
    
    # Для каждой страны оставляем не больше MAX_PER_COUNTRY
    selected_others = []
    for country, cfgs in countries.items():
        selected = cfgs[:MAX_PER_COUNTRY]
        selected_others.extend(selected)
        log(f"   {country}: выбрано {len(selected)} из {len(cfgs)}")
    
    # Сортируем остальные по стране и скорости
    selected_others.sort(key=lambda x: (x['country'], x['latency']))
    
    # Финальный список: сначала все финские, потом остальные
    final_list = finnish_working + selected_others
    
    # Если получилось больше MAX_CONFIGS, обрезаем остальные
    if len(final_list) > MAX_CONFIGS:
        final_list = finnish_working + selected_others[:MAX_CONFIGS - len(finnish_working)]
    
    log(f"\n📊 Итого: {len(final_list)} конфигов")
    log(f"   🇫🇮 Финских: {len(finnish_working)}")
    log(f"   🌍 Других: {len(final_list) - len(finnish_working)}")

    # Генерация файла
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
        'total_configs': len(unique),
        'finnish_total': len(finnish_configs),
        'finnish_added': len(finnish_working),
        'other_checked': len(other_configs),
        'other_working': len(other_working),
        'other_selected': len(selected_others),
        'final_count': len(final_list),
        'per_country': {c: len([x for x in final_list if x['country'] == c]) for c in set(x['country'] for x in final_list)},
    }
    
    with open('configs_debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)

    log(f"\n✨ Готово!")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)