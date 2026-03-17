#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import re
from datetime import datetime
from urllib.parse import unquote

# ========== НАСТРОЙКИ ==========
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
]
OUTPUT_FILE = "configs.txt"
VERSION_FILE = "version.txt"

# ========== СЛОВАРЬ СТРАН ==========
COUNTRIES = {
    '🇦🇹': 'Австрия', '🇦🇺': 'Австралия', '🇧🇪': 'Бельгия', '🇧🇷': 'Бразилия',
    '🇬🇧': 'Великобритания', '🇭🇺': 'Венгрия', '🇩🇪': 'Германия', '🇮🇱': 'Израиль',
    '🇮🇳': 'Индия', '🇪🇸': 'Испания', '🇮🇹': 'Италия', '🇨🇦': 'Канада',
    '🇱🇻': 'Латвия', '🇱🇹': 'Литва', '🇱🇺': 'Люксембург', '🇳🇱': 'Нидерланды',
    '🇳🇴': 'Норвегия', '🇦🇪': 'ОАЭ', '🇵🇱': 'Польша', '🇷🇺': 'Россия',
    '🇺🇸': 'США', '🇹🇷': 'Турция', '🇫🇮': 'Финляндия', '🇫🇷': 'Франция',
    '🇨🇿': 'Чехия', '🇸🇪': 'Швеция', '🇪🇪': 'Эстония', '🇯🇵': 'Япония',
    '🇪🇺': 'Европа', '🌐': 'Anycast'
}

# ========== СООТВЕТСТВИЕ URL-КОДИРОВОК ФЛАГАМ ==========
FLAG_PATTERNS = {
    '%F0%9F%87%AB%F0%9F%87%B7': '🇫🇷',  # Франция
    '%F0%9F%87%A9%F0%9F%87%AA': '🇩🇪',  # Германия
    '%F0%9F%87%AB%F0%9F%87%AE': '🇫🇮',  # Финляндия
    '%F0%9F%87%AA%F0%9F%87%AA': '🇪🇪',  # Эстония
    '%F0%9F%87%A7%F0%9F%87%AA': '🇧🇪',  # Бельгия
    '%F0%9F%87%B1%F0%9F%87%BB': '🇱🇻',  # Латвия
    '%F0%9F%87%B3%F0%9F%87%B4': '🇳🇴',  # Норвегия
    '%F0%9F%87%B5%F0%9F%87%B1': '🇵🇱',  # Польша
    '%F0%9F%87%B3%F0%9F%87%B1': '🇳🇱',  # Нидерланды
    '%F0%9F%87%AC%F0%9F%87%A7': '🇬🇧',  # Великобритания
    '%F0%9F%87%BA%F0%9F%87%B8': '🇺🇸',  # США
    '%F0%9F%87%B7%F0%9F%87%BA': '🇷🇺',  # Россия
    '%F0%9F%87%A6%F0%9F%87%B9': '🇦🇹',  # Австрия
    '%F0%9F%87%A7%F0%9F%87%BE': '🇧🇾',  # Беларусь
    '%F0%9F%87%A8%F0%9F%87%BF': '🇨🇿',  # Чехия
    '%F0%9F%87%B0%F0%9F%87%BF': '🇰🇿',  # Казахстан
    '%F0%9F%87%B1%F0%9F%87%B9': '🇱🇹',  # Литва
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_version():
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                current = int(f.read().strip())
        else:
            current = 0
    except:
        current = 0
    
    next_ver = current + 1
    with open(VERSION_FILE, 'w') as f:
        f.write(str(next_ver))
    
    return f"22.1.{next_ver}"

def extract_flag_from_comment(comment):
    # Сначала пробуем найти по URL-кодировкам
    for encoded, flag in FLAG_PATTERNS.items():
        if encoded in comment:
            return flag
    
    # Если не нашли, пробуем декодировать и искать эмодзи
    try:
        decoded = unquote(comment)
        for flag in COUNTRIES.keys():
            if flag in decoded:
                return flag
    except:
        pass
    
    return '🌐'

def fetch_and_process_source(url, source_name):
    """Скачивает и обрабатывает один источник"""
    log(f"📡 Загрузка из {source_name}...")
    
    try:
        r = requests.get(url, timeout=30)
        r.encoding = 'utf-8'
        
        if r.status_code != 200:
            log(f"❌ Ошибка {source_name}: HTTP {r.status_code}")
            return [], 0, 0
        
        lines = r.text.strip().split('\n')
        log(f"✅ {source_name}: {len(lines)} строк")
        
        configs = []
        skipped = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith(('vless://', 'vmess://', 'trojan://', 'hysteria2://', 'ss://')):
                try:
                    if '#' in line:
                        url_part, comment = line.split('#', 1)
                    else:
                        url_part, comment = line, ''
                    
                    flag = extract_flag_from_comment(comment)
                    country = COUNTRIES.get(flag, 'Anycast')
                    
                    new_line = f"{url_part}#{flag} {country} |💠| от катлер"
                    configs.append(new_line)
                    
                except Exception as e:
                    skipped += 1
            else:
                skipped += 1
        
        return configs, skipped, len(configs)
        
    except Exception as e:
        log(f"❌ Ошибка скачивания {source_name}: {e}")
        return [], 0, 0

def main():
    log("=" * 50)
    log("🚀 CatwhiteVPN - Сбор из двух источников")
    
    version = get_version()
    log(f"📦 Версия: {version}")
    
    all_configs = []
    total_skipped = 0
    source_stats = []
    
    # Обрабатываем каждый источник
    for i, url in enumerate(SOURCES, 1):
        source_name = f"Источник {i}"
        configs, skipped, count = fetch_and_process_source(url, source_name)
        all_configs.extend(configs)
        total_skipped += skipped
        source_stats.append((source_name, count, skipped))
    
    # Удаляем возможные дубликаты (по URL до #)
    unique_configs = []
    seen_urls = set()
    for cfg in all_configs:
        url_part = cfg.split('#')[0]
        if url_part not in seen_urls:
            seen_urls.add(url_part)
            unique_configs.append(cfg)
    
    log(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    for name, count, skipped in source_stats:
        log(f"  {name}: +{count} конфигов (пропущено {skipped})")
    log(f"  Уникальных после удаления дубликатов: {len(unique_configs)}")
    
    # Заголовок
    header = [
        "#profile-title: 👾🌿CatwhiteVPN🌿👾",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]
    
    # Сохраняем
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header + unique_configs))
        
        log(f"\n✅ Файл сохранён: {OUTPUT_FILE}")
        log(f"   Размер: {os.path.getsize(OUTPUT_FILE)} байт")
        log(f"   Всего конфигов: {len(unique_configs)}")
        
        # Статистика по странам
        stats = {}
        for cfg in unique_configs[:100]:  # Анализируем первые 100 для статистики
            if '#' in cfg:
                name = cfg.split('#')[1]
                flag = name.split()[0] if name else '🌐'
                stats[flag] = stats.get(flag, 0) + 1
        
        if stats:
            log("\n📊 Статистика по странам (первые 100 конфигов):")
            for flag, count in sorted(stats.items(), key=lambda x: -x[1])[:10]:
                country = COUNTRIES.get(flag, 'Anycast')
                log(f"  {flag} {country}: {count}")
        
        # Показываем пример
        if unique_configs:
            log("\n📝 Пример первого конфига:")
            sample = unique_configs[0]
            if '#' in sample:
                url_short = sample.split('#')[0][:60] + "..."
                name = sample.split('#')[1]
                log(f"  {url_short}#{name}")
        
    except Exception as e:
        log(f"❌ Ошибка сохранения: {e}")
    
    log("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()