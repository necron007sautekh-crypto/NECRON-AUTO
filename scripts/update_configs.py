#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v4
Формирует подписку в формате CatwhiteVPN
Версия ядра: 4 (не меняется)
Версия сборки: увеличивается при каждом обновлении
"""

import requests
import json
import time
import os
import re
from datetime import datetime
from typing import List, Dict, Any

# ================= НАСТРОЙКИ =================
VERSION_CORE = "4"  # Ядро (не меняется)
VERSION_FILE = "version.txt"  # Файл для хранения текущей версии

SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/1.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2ray",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
]

# Ключевые слова для определения страны (расширенный список)
COUNTRY_KEYWORDS = {
    '🇷🇺 Россия': ['russia', 'ru', 'moscow', 'spb', 'msk', 'saint-petersburg'],
    '🇫🇮 Финляндия': ['finland', 'helsinki', 'fi'],
    '🇳🇱 Нидерланды': ['netherlands', 'amsterdam', 'nl'],
    '🇩🇪 Германия': ['germany', 'frankfurt', 'de'],
    '🇫🇷 Франция': ['france', 'paris', 'fra'],
    '🇬🇧 Великобритания': ['uk', 'london', 'gb'],
    '🇸🇬 Сингапур': ['singapore', 'sg'],
    '🇺🇸 США': ['usa', 'united states', 'new york', 'us'],
    '🇸🇪 Швеция': ['sweden', 'se'],
    '🇵🇱 Польша': ['poland', 'pl'],
    '🇪🇪 Эстония': ['estonia', 'ee'],
    '🇪🇸 Испания': ['spain', 'es'],
    '🇹🇷 Турция': ['turkey', 'tr'],
    '🇭🇺 Венгрия': ['hungary', 'hu'],
    '🇮🇹 Италия': ['italy', 'it'],
    '🇳🇴 Норвегия': ['norway', 'no'],
    '🇱🇺 Люксембург': ['luxembourg', 'lu'],
    '🇨🇿 Чехия': ['czech', 'prague', 'cz'],
    '🇦🇹 Австрия': ['austria', 'vienna', 'at'],
    '🌐 Anycast': ['anycast'],
}

# ================= ФУНКЦИИ =================

def get_next_version():
    """Читает текущую версию из файла и увеличивает её"""
    current_version = 0
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                current_version = int(f.read().strip())
        except:
            pass
    
    next_version = current_version + 1
    # Сохраняем новую версию
    with open(VERSION_FILE, 'w') as f:
        f.write(str(next_version))
    
    return f"{VERSION_CORE}.{next_version}"

def detect_country(config_url: str) -> str:
    """Определяет страну по URL"""
    url_lower = config_url.lower()
    for flag, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in url_lower:
                return flag
    return '🌐 Anycast'

def extract_sni(config_url: str) -> str:
    """Пытается извлечь sni из ссылки"""
    # Ищем sni=... или &sni=...
    sni_match = re.search(r'sni=([^&]+)', config_url)
    if sni_match:
        return sni_match.group(1)
    return 'unknown'

def generate_number(configs: List[str], index: int) -> str:
    """Генерирует трёхзначный номер с ведущими нулями"""
    return f"{index+1:03d}"

def fetch_configs(source: str) -> List[str]:
    """Скачивает конфиги из источника"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(source, timeout=15, headers=headers)
        if r.status_code == 200:
            return r.text.strip().split('\n')
    except Exception as e:
        print(f"  ❌ {source[:50]}...: {str(e)[:50]}")
    return []

def is_valid_config(line: str) -> bool:
    """Проверяет, что строка — рабочий конфиг"""
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    protocols = ['vless://', 'vmess://', 'trojan://', 'ss://', 'hysteria2://']
    return any(line.startswith(proto) for proto in protocols)

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    print("=" * 60)
    print("🐱 Catwhite Configs Collector v4")
    print("=" * 60)
    
    # Получаем новую версию
    version = get_next_version()
    print(f"📦 Версия сборки: {version}")
    
    # Собираем конфиги
    all_configs = []
    print(f"\n📡 Загрузка из {len(SOURCES)} источников:")
    
    for i, src in enumerate(SOURCES, 1):
        print(f"  {i}/{len(SOURCES)}... ", end="")
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        all_configs.extend(valid)
        print(f"✅ +{len(valid)}")
        time.sleep(0.3)
    
    # Убираем дубликаты
    unique = list(set(all_configs))
    print(f"\n📊 Уникальных конфигов: {len(unique)}")
    
    if not unique:
        print("❌ Нет конфигов! Проверь источники.")
        return
    
    # Генерируем итоговый файл с шапкой
    output_lines = []
    
    # Шапка
    output_lines.append("#profile-title: 🌐🌿CatwhiteVPN🌿🌐")
    output_lines.append(f"#profile-update-interval: 1")
    output_lines.append(f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️")
    output_lines.append("#support-url: https://t.me/catlergememe/856")
    output_lines.append("#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/")
    output_lines.append("#hide-settings: 1")
    output_lines.append("")
    
    # Сортируем и добавляем конфиги
    # Сначала по стране, потом по алфавиту
    configs_with_info = []
    for cfg in unique:
        country = detect_country(cfg)
        sni = extract_sni(cfg)
        configs_with_info.append((country, sni, cfg))
    
    configs_with_info.sort(key=lambda x: (x[0], x[2]))
    
    for idx, (country, sni, cfg) in enumerate(configs_with_info):
        number = generate_number(configs_with_info, idx)
        output_lines.append(f"{cfg}#{country} {number} | sni = {sni} | от catler")
    
    # Сохраняем
    output_file = "configs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✅ Сохранено {len(configs_with_info)} конфигов в {output_file}")
    print(f"📁 Файл готов, версия {version}")
    print("=" * 60)

if __name__ == "__main__":
    main()