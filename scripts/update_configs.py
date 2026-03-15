#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v14 — только нормальные страны, без Anycast
"""

import requests
import json
import time
import os
import re
import socket
import sys
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= НАСТРОЙКИ =================
VERSION_CORE = "14"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 300
TIMEOUT = 5
WORKERS = 20

# Единственный источник
MAIN_SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

# Список разрешённых флагов (все, кроме Anycast)
# Если флаг не в этом списке – конфиг будет отброшен
ALLOWED_FLAGS = {
    '🇫🇮', '🇩🇪', '🇳🇱', '🇷🇺', '🇺🇸', '🇬🇧', '🇫🇷', '🇸🇬', '🇸🇪', '🇵🇱',
    '🇪🇪', '🇪🇸', '🇹🇷', '🇭🇺', '🇮🇹', '🇳🇴', '🇱🇺', '🇨🇿', '🇦🇹', '🇨🇦',
    '🇯🇵', '🇦🇪', '🇮🇳', '🇧🇷', '🇿🇦', '🇦🇺', '🇪🇺'
}

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
    m = re.search(r'#([🇦-🇿]{2})', comment)
    return m.group(1) if m else '🌐'

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
    """Проверяет, что флаг в списке разрешённых (не Anycast)"""
    return flag in ALLOWED_FLAGS

def check_config(config_line: str) -> Dict[str, Any]:
    parts = extract_config_parts(config_line)
    url = parts['url']
    host = extract_host(url)
    if not host:
        return None

    port_match = re.search(r':(\d+)', url)
    port = int(port_match.group(1)) if port_match else 443

    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            latency = (time.time() - start) * 1000
            flag = extract_flag_from_comment(parts['comment'])
            # Если флаг не разрешён – возвращаем None (отбрасываем сразу)
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
    return line.startswith('vless://')

def generate_number(index: int) -> str:
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Старт сбора (только нормальные страны, без Anycast)")
    version = get_next_version()
    log(f"📦 Версия: {version}")

    # Загружаем источник
    log(f"\n📡 Загрузка {MAIN_SOURCE[:80]}...")
    lines = fetch_configs(MAIN_SOURCE)
    valid = [line.strip() for line in lines if is_valid_config(line)]
    log(f"✅ Найдено {len(valid)} конфигов в источнике")

    if not valid:
        log("❌ Нет конфигов, выход")
        sys.exit(1)

    # Убираем дубликаты
    unique = list(set(valid))
    log(f"📊 Уникальных: {len(unique)}")

    # Проверка доступности
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
            if checked % 50 == 0:
                log(f"   Проверено {checked}/{len(unique)}, найдено {len(working)} рабочих (уже без Anycast)")

    log(f"\n✅ Найдено рабочих (с нормальными флагами): {len(working)}")
    if not working:
        log("❌ Нет рабочих с нормальными флагами, выход")
        sys.exit(1)

    # Сортируем по скорости
    working.sort(key=lambda x: x['latency'])

    # Берём только 300 самых быстрых
    best = working[:MAX_CONFIGS]
    log(f"📊 Отобрано лучших (до {MAX_CONFIGS}): {len(best)}")

    # Сортировка с приоритетом Финляндии
    finnish = [c for c in best if c['country'] == 'Финляндия']
    others = [c for c in best if c['country'] != 'Финляндия']
    others.sort(key=lambda x: (x['country'], x['latency']))
    final_list = finnish + others
    log(f"   🇫🇮 Финских: {len(finnish)}, 🌍 Других стран: {len(others)}")

    # Генерация файла
    log("\n📝 Формирование configs.txt ...")
    output = [
        "#profile-title: 🌐🌿CatwhiteVPN🌿🌐",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]

    for idx, cfg in enumerate(final_list):
        num = generate_number(idx)
        sni_match = re.search(r'sni\s*=\s*([^|\s]+)', cfg['original_comment'])
        sni = sni_match.group(1) if sni_match else 'unknown'
        line = f"{cfg['url']}#{cfg['flag']} {num} {cfg['country']} | sni = {sni} | от catler"
        output.append(line)

    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    log(f"✅ configs.txt сохранён, {len(final_list)} конфигов (все с нормальными флагами)")

    # Отладочный JSON
    debug = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'total_checked': len(unique),
        'working_found': len(working),
        'best_selected': len(best),
        'finnish_count': len(finnish),
        'avg_latency': round(sum(c['latency'] for c in best) / len(best), 1) if best else 0,
    }
    with open('configs_debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)

    log(f"\n✨ Готово! Средний пинг отобранных: {debug['avg_latency']} ms")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)