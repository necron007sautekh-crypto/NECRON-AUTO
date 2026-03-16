#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v24 — только JSON для клиентов
- Берём всё из WHITE-CIDR-RU-all.txt
- Без проверок
- Сохраняем порядок (финские первые)
- Генерируем только JSON
- Автообновление раз в 5 часов
"""

import requests
import json
import time
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "24"
VERSION_FILE = "version.txt"

# Единственный источник — полный файл от igareck
SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

# ================= ФУНКЦИИ =================

def log(msg: str):
    """Вывод сообщения с временной меткой"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_next_version() -> str:
    """Читает и увеличивает номер версии"""
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

def extract_flag_from_comment(comment: str) -> str:
    """Извлекает флаг из комментария (поддержка URL-кодировки)"""
    try:
        decoded = unquote(comment)
        flag_match = re.search(r'([🇦-🇿]{2})', decoded)
        if flag_match:
            return flag_match.group(1)
    except:
        pass
    return '🌐'

def extract_country_from_comment(comment: str) -> str:
    """Определяет страну по флагу"""
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

def fetch_configs() -> List[str]:
    """Скачивает конфиги из источника"""
    try:
        log(f"📡 Загрузка {SOURCE[:80]}...")
        resp = requests.get(SOURCE, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            # Пропускаем заголовки (строки, начинающиеся с #)
            configs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            log(f"✅ Загружено {len(configs)} конфигов")
            return configs
    except Exception as e:
        log(f"❌ Ошибка загрузки: {e}")
    return []

def generate_number(index: int) -> str:
    """Генерирует трёхзначный номер"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Catwhite Configs Collector v24 — только JSON")
    version = get_next_version()
    log(f"📦 Версия: {version}")
    log(f"⏱️  Автообновление: каждые 5 часов")

    # Загружаем конфиги
    configs = fetch_configs()
    
    if not configs:
        log("❌ Нет конфигов, выход")
        sys.exit(1)

    log(f"\n📊 Всего конфигов: {len(configs)}")

    # Подготавливаем список конфигов для JSON
    config_list = []
    finnish_count = 0
    other_count = 0
    anycast_count = 0

    for idx, line in enumerate(configs):
        # Пропускаем явно некорректные строки
        if not (line.startswith('vless://') or line.startswith('vmess://') or 
                line.startswith('hysteria2://') or line.startswith('trojan://')):
            continue
            
        parts = extract_config_parts(line)
        flag = extract_flag_from_comment(parts['comment'])
        country = extract_country_from_comment(parts['comment'])
        
        if country == 'Финляндия':
            finnish_count += 1
        elif country == 'Anycast':
            anycast_count += 1
        else:
            other_count += 1
        
        num = generate_number(idx)
        
        # Формируем полную строку конфига
        full_config = f"{parts['url']}#{flag} {num} {country} | 💠 | от catler"
        
        config_list.append(full_config)

    # Создаём JSON-структуру
    json_data = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "total": len(config_list),
        "finnish_count": finnish_count,
        "other_count": other_count,
        "anycast_count": anycast_count,
        "configs": config_list
    }

    # Сохраняем только JSON (без txt)
    json_file = "configs.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    log(f"✅ {json_file} сохранён")
    log(f"\n📊 Статистика:")
    log(f"   • Всего конфигов: {len(config_list)}")
    log(f"   • 🇫🇮 Финских: {finnish_count}")
    log(f"   • 🌍 Других стран: {other_count}")
    log(f"   • 🌐 Anycast: {anycast_count}")

    # Отладочная информация (опционально, можно удалить)
    debug = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'source': SOURCE,
        'total_original': len(configs),
        'processed': len(config_list),
        'finnish_count': finnish_count,
        'other_count': other_count,
        'anycast_count': anycast_count,
    }
    
    with open('debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)

    log(f"\n✨ Готово! Подписка (JSON) обновится через 5 часов")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)