#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector
Автоматический сбор и проверка VPN-конфигов
Версия: 2.0
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any

# ================= НАСТРОЙКИ =================
# Тут можно менять под себя
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/1.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2ray",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
]

# Ключевые слова для определения страны (можно дополнять)
COUNTRY_KEYWORDS = {
    # Финляндия
    'finland': '🇫🇮 Финляндия', 'helsinki': '🇫🇮 Финляндия', 'fi': '🇫🇮 Финляндия',
    # Нидерланды
    'netherlands': '🇳🇱 Нидерланды', 'amsterdam': '🇳🇱 Нидерланды', 'nl': '🇳🇱 Нидерланды',
    # Германия
    'germany': '🇩🇪 Германия', 'frankfurt': '🇩🇪 Германия', 'de': '🇩🇪 Германия',
    # Франция
    'france': '🇫🇷 Франция', 'paris': '🇫🇷 Франция', 'fra': '🇫🇷 Франция',
    # Великобритания
    'uk': '🇬🇧 Великобритания', 'london': '🇬🇧 Великобритания', 'gb': '🇬🇧 Великобритания',
    # Сингапур
    'singapore': '🇸🇬 Сингапур', 'sg': '🇸🇬 Сингапур',
    # США
    'usa': '🇺🇸 США', 'united states': '🇺🇸 США', 'new york': '🇺🇸 США', 'us': '🇺🇸 США',
    # Швеция
    'sweden': '🇸🇪 Швеция', 'se': '🇸🇪 Швеция',
    # Польша
    'poland': '🇵🇱 Польша', 'pl': '🇵🇱 Польша',
    # Эстония
    'estonia': '🇪🇪 Эстония', 'ee': '🇪🇪 Эстония',
    # Испания
    'spain': '🇪🇸 Испания', 'es': '🇪🇸 Испания',
    # Турция
    'turkey': '🇹🇷 Турция', 'tr': '🇹🇷 Турция',
    # Венгрия
    'hungary': '🇭🇺 Венгрия', 'hu': '🇭🇺 Венгрия',
    # Италия
    'italy': '🇮🇹 Италия', 'it': '🇮🇹 Италия',
    # Норвегия
    'norway': '🇳🇴 Норвегия', 'no': '🇳🇴 Норвегия',
    # Люксембург
    'luxembourg': '🇱🇺 Люксембург', 'lu': '🇱🇺 Люксембург',
}

# ================= ФУНКЦИИ =================

def fetch_configs(source: str) -> List[str]:
    """Скачивает конфиги из источника"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        r = requests.get(source, timeout=15, headers=headers)
        if r.status_code == 200:
            return r.text.strip().split('\n')
        else:
            print(f"  ⚠️ HTTP {r.status_code} for {source}")
    except Exception as e:
        print(f"  ❌ Error fetching {source}: {str(e)[:50]}")
    return []

def is_valid_config(line: str) -> bool:
    """Проверяет, что строка похожа на конфиг"""
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    # Проверяем начало строки на известные протоколы
    protocols = ['vless://', 'vmess://', 'trojan://', 'ss://', 'hysteria2://']
    return any(line.startswith(proto) for proto in protocols)

def detect_country(config_url: str) -> str:
    """Определяет страну по URL"""
    url_lower = config_url.lower()
    for key, flag in COUNTRY_KEYWORDS.items():
        if key in url_lower:
            return flag
    return '🌐 Anycast'

def save_json(data: Dict[str, Any], filename: str):
    """Сохраняет данные в JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_txt(lines: List[str], filename: str):
    """Сохраняет текстовый файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    print("=" * 60)
    print(f"🐱 Catwhite Configs Collector v2.0")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Собираем все конфиги
    all_configs = []
    print(f"\n📡 Сбор из {len(SOURCES)} источников:")
    
    for i, src in enumerate(SOURCES, 1):
        print(f"\n  {i}/{len(SOURCES)}: {src[:60]}...")
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        all_configs.extend(valid)
        print(f"    ✅ Найдено: {len(valid)} конфигов")
        time.sleep(0.5)  # Не ддосим источники
    
    # Убираем дубликаты
    unique_configs = list(set(all_configs))
    print(f"\n📊 Уникальных конфигов: {len(unique_configs)}")
    
    if not unique_configs:
        print("❌ Нет конфигов! Проверь источники.")
        return
    
    # Сортируем с флагами
    configs_with_flags = []
    for cfg in unique_configs:
        configs_with_flags.append({
            'url': cfg,
            'country': detect_country(cfg),
            'added': datetime.now().isoformat()
        })
    
    # Сортируем по стране
    configs_with_flags.sort(key=lambda x: x['country'])
    
    # Создаём итоговый JSON
    output_json = {
        'version': '2.0',
        'updated': datetime.now().isoformat(),
        'total': len(configs_with_flags),
        'sources_count': len(SOURCES),
        'configs': configs_with_flags
    }
    
    # Создаём TXT версию (для Happ)
    txt_lines = [f"{cfg['country']} | {cfg['url']}" for cfg in configs_with_flags]
    
    # Сохраняем файлы
    save_json(output_json, 'configs.json')
    save_txt(txt_lines, 'configs.txt')
    
    print(f"\n✅ Успешно сохранено:")
    print(f"   • configs.json  — {len(configs_with_flags)} конфигов")
    print(f"   • configs.txt   — {len(txt_lines)} строк")
    print(f"\n📁 Размер JSON: {os.path.getsize('configs.json')} байт")
    print("=" * 60)

if __name__ == "__main__":
    main()
