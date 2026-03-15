#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v4
- Заменяем оригинальный комментарий на новый
- Без дублирования
- Сохраняем только нужный формат
"""

import requests
import json
import time
import os
import re
import socket
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= НАСТРОЙКИ =================
VERSION_CORE = "4"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 1000
TIMEOUT = 5
WORKERS = 20

SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/1.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2ray",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
]

# Ключевые слова для определения страны (на случай если в оригинале нет флага)
FALLBACK_COUNTRY_KEYWORDS = {
    '🇷🇺 Россия': ['russia', 'ru', 'moscow', 'spb', 'msk', 'saint-petersburg', 'mosc'],
    '🇫🇮 Финляндия': ['finland', 'helsinki', 'fi', 'finn'],
    '🇳🇱 Нидерланды': ['netherlands', 'amsterdam', 'nl', 'neth'],
    '🇩🇪 Германия': ['germany', 'frankfurt', 'de', 'ger'],
    '🇫🇷 Франция': ['france', 'paris', 'fra', 'fr'],
    '🇬🇧 Великобритания': ['uk', 'london', 'gb', 'britain'],
    '🇺🇸 США': ['usa', 'united states', 'new york', 'us', 'america'],
    '🇨🇦 Канада': ['canada', 'ca'],
    '🇸🇬 Сингапур': ['singapore', 'sg'],
    '🇯🇵 Япония': ['japan', 'jp', 'tokyo'],
    '🇦🇺 Австралия': ['australia', 'au', 'sydney'],
    '🇮🇳 Индия': ['india', 'in'],
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
    with open(VERSION_FILE, 'w') as f:
        f.write(str(next_version))
    
    return f"{VERSION_CORE}.{next_version}"

def extract_flag_from_original(original_line: str) -> str:
    """Извлекает флаг из оригинального комментария"""
    # Ищем эмодзи флага (диапазон флагов)
    flag_match = re.search(r'#([🇦-🇿]{2})', original_line)
    if flag_match:
        return flag_match.group(1)
    
    # Если не нашли флаг, пробуем определить по тексту
    url_lower = original_line.lower()
    for flag, keywords in FALLBACK_COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in url_lower:
                return flag.split()[0]  # берём только эмодзи
    return '🌐'

def extract_country_from_original(original_line: str) -> str:
    """Извлекает название страны из оригинального комментария"""
    # Ищем текст после флага до первого разделителя
    country_match = re.search(r'#[🇦-🇿]{2}\s+([^|\d]+)', original_line)
    if country_match:
        return country_match.group(1).strip()
    
    # Если не нашли, пробуем определить по тексту
    url_lower = original_line.lower()
    for flag, keywords in FALLBACK_COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in url_lower:
                return flag.split()[1]  # берём только название
    return 'Anycast'

def extract_sni(config_url: str) -> str:
    """Извлекает sni из ссылки"""
    sni_match = re.search(r'sni=([^&]+)', config_url)
    if sni_match:
        return sni_match.group(1)
    return 'unknown'

def extract_host(config_url: str) -> str:
    """Извлекает хост из ссылки"""
    match = re.search(r'@([^:]+)', config_url)
    if match:
        return match.group(1)
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', config_url)
    if match:
        return match.group(1)
    return None

def check_config(original_line: str) -> Dict[str, Any]:
    """
    Проверяет работоспособность конфига
    Возвращает словарь с результатами или None если не работает
    """
    # Берём только часть до # (чистый URL)
    clean_url = original_line.split('#')[0].strip()
    
    host = extract_host(clean_url)
    if not host:
        return None
    
    try:
        # Определяем порт
        port_match = re.search(r':(\d+)', clean_url)
        port = int(port_match.group(1)) if port_match else 443
        
        # Проверяем соединение
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            latency = (time.time() - start) * 1000
            
            return {
                'clean_url': clean_url,
                'host': host,
                'port': port,
                'latency': round(latency, 2),
                'flag': extract_flag_from_original(original_line),
                'country': extract_country_from_original(original_line),
                'sni': extract_sni(clean_url),
                'working': True
            }
    except:
        pass
    
    return None

def fetch_configs(source: str) -> List[str]:
    """Скачивает конфиги из источника"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(source, timeout=15, headers=headers)
        if r.status_code == 200:
            return r.text.strip().split('\n')
    except:
        pass
    return []

def is_valid_config(line: str) -> bool:
    """Проверяет, что строка — рабочий конфиг"""
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    if 'vless://' not in line:
        return False
    return True

def generate_number(index: int) -> str:
    """Генерирует трёхзначный номер"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    print("=" * 70)
    print("🐱 Catwhite Configs Collector v9 — без дублирования")
    print("=" * 70)
    
    version = get_next_version()
    print(f"📦 Версия: {version}")
    
    # Собираем конфиги
    all_lines = []
    print(f"\n📡 Загрузка из {len(SOURCES)} источников:")
    
    for i, src in enumerate(SOURCES, 1):
        print(f"  {i}/{len(SOURCES)}... ", end="")
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        all_lines.extend(valid)
        print(f"✅ +{len(valid)}")
        time.sleep(0.2)
    
    # Убираем дубликаты
    unique_lines = list(set(all_lines))
    print(f"\n📊 Уникальных конфигов до проверки: {len(unique_lines)}")
    
    if not unique_lines:
        print("❌ Нет конфигов!")
        return
    
    # Проверяем работоспособность
    print(f"\n🔄 Проверка работоспособности...")
    
    working_configs = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_config = {executor.submit(check_config, line): line for line in unique_lines}
        
        for future in as_completed(future_to_config):
            checked += 1
            result = future.result()
            if result:
                working_configs.append(result)
            
            if checked % 100 == 0:
                print(f"    Проверено {checked}/{len(unique_lines)}, найдено {len(working_configs)} рабочих")
    
    print(f"\n✅ Найдено рабочих: {len(working_configs)}")
    
    if not working_configs:
        print("❌ Нет рабочих конфигов!")
        return
    
    # Сортируем по скорости
    working_configs.sort(key=lambda x: x['latency'])
    
    # Берём самые быстрые
    best_configs = working_configs[:MAX_CONFIGS]
    print(f"📊 Отобрано лучших (до {MAX_CONFIGS}): {len(best_configs)}")
    
    # Сортируем по стране
    best_configs.sort(key=lambda x: x['country'])
    
    # Генерируем итоговый файл
    output_lines = []
    
    # Шапка
    output_lines.append("#profile-title: 🌐🌿CatwhiteVPN🌿🌐")
    output_lines.append("#profile-update-interval: 1")
    output_lines.append(f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️")
    output_lines.append("#support-url: https://t.me/catlergememe/856")
    output_lines.append("#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/")
    output_lines.append("#hide-settings: 1")
    output_lines.append("")
    
    # Добавляем конфиги (полностью заменяем комментарий)
    for idx, cfg in enumerate(best_configs):
        number = generate_number(idx)
        # Новый комментарий полностью заменяет старый
        line = f"{cfg['clean_url']}#{cfg['flag']} {number} {cfg['country']} | sni = {cfg['sni']} | от catler"
        output_lines.append(line)
    
    # Сохраняем
    output_file = "configs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✅ Готово! Сохранено {len(best_configs)} конфигов")
    print(f"📁 configs.txt")
    print(f"⚡ Средний пинг: {sum(c['latency'] for c in best_configs)/len(best_configs):.1f}ms")
    print("=" * 70)

if __name__ == "__main__":
    main()