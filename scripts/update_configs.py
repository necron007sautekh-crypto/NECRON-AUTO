#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v12 — Финляндия на первом месте
Рабочая версия для GitHub Actions
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
VERSION_CORE = "12"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 1000
TIMEOUT = 5          # таймаут проверки конфига (сек)
WORKERS = 20         # кол-во одновременных проверок

# ГЛАВНЫЙ источник (лучшие конфиги)
MAIN_SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

# Дополнительные источники (если не хватит)
EXTRA_SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/1.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2ray",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
]

# ================= ФУНКЦИИ =================

def log(msg: str):
    """Простой лог с временем"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_next_version() -> str:
    """Читает текущую версию из файла и увеличивает её"""
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
    """Разделяет строку на URL и комментарий"""
    if '#' in config_line:
        url, comment = config_line.split('#', 1)
        return {'url': url.strip(), 'comment': '#' + comment.strip()}
    return {'url': config_line.strip(), 'comment': ''}

def extract_host(config_url: str) -> str:
    """Извлекает хост из URL (часть после @ или IP)"""
    m = re.search(r'@([^:]+)', config_url)
    if m:
        return m.group(1)
    m = re.search(r'(\d+\.\d+\.\d+\.\d+)', config_url)
    if m:
        return m.group(1)
    return None

def extract_flag_from_comment(comment: str) -> str:
    """Извлекает эмодзи флага из комментария"""
    # Ищем # за которым два символа флага (эмодзи)
    m = re.search(r'#([🇦-🇿]{2})', comment)
    if m:
        return m.group(1)
    return '🌐'

def extract_country_from_comment(comment: str) -> str:
    """Определяет страну по эмодзи флага"""
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

def check_config(config_line: str) -> Dict[str, Any]:
    """
    Проверяет доступность конфига (TCP-подключение к хосту:порт)
    Возвращает словарь с данными или None, если не работает.
    """
    parts = extract_config_parts(config_line)
    url = parts['url']
    host = extract_host(url)
    if not host:
        return None

    # Определяем порт
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
            return {
                'full_line': config_line,
                'url': url,
                'original_comment': parts['comment'],
                'flag': extract_flag_from_comment(parts['comment']),
                'country': extract_country_from_comment(parts['comment']),
                'host': host,
                'port': port,
                'latency': round(latency, 2),
                'working': True
            }
    except Exception:
        pass
    return None

def fetch_configs(source: str) -> List[str]:
    """Скачивает список строк из источника (с обработкой ошибок)"""
    try:
        resp = requests.get(source, timeout=15)
        if resp.status_code == 200:
            return resp.text.strip().split('\n')
    except Exception as e:
        log(f"⚠️ Ошибка загрузки {source[:60]}: {str(e)[:50]}")
    return []

def is_valid_config(line: str) -> bool:
    """Фильтр – оставляем только строки, начинающиеся с vless://"""
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    return line.startswith('vless://')

def generate_number(index: int) -> str:
    """Трёхзначный номер с ведущими нулями"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Старт сбора конфигов")
    version = get_next_version()
    log(f"📦 Версия: {version}")
    log(f"🎯 Лимит конфигов: {MAX_CONFIGS}")

    # ШАГ 1: Загружаем главный источник
    log(f"\n📡 Загрузка ГЛАВНОГО источника: {MAIN_SOURCE[:80]}...")
    main_lines = fetch_configs(MAIN_SOURCE)
    main_valid = [line.strip() for line in main_lines if is_valid_config(line)]
    log(f"   ✅ Найдено {len(main_valid)} конфигов в главном")

    # ШАГ 2: Загружаем дополнительные источники
    extra_valid = []
    for src in EXTRA_SOURCES:
        log(f"   {src[:60]}... ", end='')
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        extra_valid.extend(valid)
        log(f"✅ +{len(valid)}")

    # ШАГ 3: Объединяем и убираем дубликаты
    all_configs = main_valid + extra_valid
    unique = list(set(all_configs))
    log(f"\n📊 Уникальных конфигов: {len(unique)}")

    if not unique:
        log("❌ Нет ни одного конфига. Проверь источники.")
        sys.exit(1)

    # ШАГ 4: Проверка доступности (многопоточно)
    log(f"\n🔄 Проверка доступности (макс {WORKERS} потоков)...")
    working = []
    checked = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_line = {executor.submit(check_config, line): line for line in unique}
        for future in as_completed(future_to_line):
            checked += 1
            result = future.result()
            if result:
                working.append(result)
            if checked % 100 == 0:
                log(f"   Проверено {checked}/{len(unique)}, найдено {len(working)} рабочих")

    log(f"\n✅ Найдено рабочих конфигов: {len(working)}")
    if not working:
        log("❌ Нет рабочих конфигов. Выход.")
        sys.exit(1)

    # ШАГ 5: Сортируем по скорости
    working.sort(key=lambda x: x['latency'])

    # ШАГ 6: Оставляем только самые быстрые (не больше MAX_CONFIGS)
    best = working[:MAX_CONFIGS]
    log(f"📊 Отобрано лучших (до {MAX_CONFIGS}): {len(best)}")

    # ШАГ 7: Сортировка с приоритетом Финляндии
    finnish = [c for c in best if c['country'] == 'Финляндия']
    others = [c for c in best if c['country'] != 'Финляндия']
    others.sort(key=lambda x: (x['country'], x['latency']))
    final_list = finnish + others
    log(f"   🇫🇮 Финских: {len(finnish)}, 🌍 Других: {len(others)}")

    # ШАГ 8: Генерация итогового файла
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
        # пытаемся извлечь sni из оригинального комментария
        sni_match = re.search(r'sni\s*=\s*([^|\s]+)', cfg['original_comment'])
        sni = sni_match.group(1) if sni_match else 'unknown'
        line = f"{cfg['url']}#{cfg['flag']} {num} {cfg['country']} | sni = {sni} | от catler"
        output.append(line)

    # Сохраняем основной файл
    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    log(f"✅ configs.txt сохранён, строк: {len(output)-7}")

    # ШАГ 9: Сохраняем отладочный JSON
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
    log(f"📁 configs_debug.json сохранён")

    log(f"\n✨ Готово! Средний пинг отобранных: {debug['avg_latency']} ms")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)