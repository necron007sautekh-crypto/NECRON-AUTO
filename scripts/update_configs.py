#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import re
import sys
from datetime import datetime
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
SOURCE_URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"
OUTPUT_FILE = "configs.txt"
VERSION_FILE = "version.txt"

# ================= МАППИНГ ФЛАГОВ =================
COUNTRY_MAP = {
    '🇦🇹': 'Австрия', '🇦🇺': 'Австралия', '🇧🇪': 'Бельгия', '🇧🇷': 'Бразилия',
    '🇬🇧': 'Великобритания', '🇭🇺': 'Венгрия', '🇩🇪': 'Германия', '🇮🇱': 'Израиль',
    '🇮🇳': 'Индия', '🇪🇸': 'Испания', '🇮🇹': 'Италия', '🇨🇦': 'Канада',
    '🇱🇻': 'Латвия', '🇱🇹': 'Литва', '🇱🇺': 'Люксембург', '🇳🇱': 'Нидерланды',
    '🇳🇴': 'Норвегия', '🇦🇪': 'ОАЭ', '🇵🇱': 'Польша', '🇷🇺': 'Россия',
    '🇷🇸': 'Сербия', '🇸🇬': 'Сингапур', '🇺🇸': 'США', '🇹🇷': 'Турция',
    '🇫🇮': 'Финляндия', '🇫🇷': 'Франция', '🇨🇿': 'Чехия', '🇨🇭': 'Швейцария',
    '🇸🇪': 'Швеция', '🇪🇪': 'Эстония', '🇯🇵': 'Япония',
    '🇪🇺': 'Европа', '🌐': 'Anycast'
}

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
    return f"22.1.{next_ver}"  # Формат как у вас

def extract_flag_and_country(comment: str) -> tuple:
    try:
        decoded = unquote(comment)
        flag_match = re.search(r'([🇦-🇿]{2})', decoded)
        if flag_match:
            flag = flag_match.group(1)
            country = COUNTRY_MAP.get(flag, 'Неизвестно')
            return flag, country
    except:
        pass
    return '🌐', 'Anycast'

def process_config_line(line: str) -> str:
    line = line.strip()
    if not line or '#' not in line:
        return ""
    
    url_part, old_comment = line.split('#', 1)
    url_part = url_part.strip()
    flag, country = extract_flag_and_country(old_comment)
    
    # Новое название БЕЗ номера, только флаг и страна
    new_name = f"{flag} {country} |💠| от катлер"
    
    return f"{url_part}#{new_name}"

def main():
    log("=" * 50)
    log("🚀 Catwhite Configs Collector - АГРЕССИВНОЕ ОБНОВЛЕНИЕ")
    
    # ПОЛНОСТЬЮ УДАЛЯЕМ старый файл, если он есть
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        log(f"🗑️ Удалён старый {OUTPUT_FILE}")
    
    version = get_next_version()
    log(f"📦 Версия: {version}")
    
    # Скачиваем
    try:
        log(f"📡 Загрузка из источника...")
        response = requests.get(SOURCE_URL, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            log(f"❌ Ошибка загрузки: HTTP {response.status_code}")
            return
        
        lines = response.text.splitlines()
        log(f"✅ Загружено {len(lines)} строк из источника")
        
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return
    
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
    
    # Обрабатываем конфиги
    processed = []
    skipped = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if any(line.startswith(p) for p in ['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'ss://']):
            try:
                new_line = process_config_line(line)
                if new_line:
                    processed.append(new_line)
            except Exception as e:
                skipped += 1
        else:
            skipped += 1
    
    # СОЗДАЁМ НОВЫЙ ФАЙЛ С НУЛЯ
    log(f"\n📊 Статистика:")
    log(f"   • Новых конфигов: {len(processed)}")
    log(f"   • Пропущено: {skipped}")
    
    # Записываем новый файл
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header + processed))
    
    log(f"✅ Новый {OUTPUT_FILE} создан!")
    log(f"📁 Размер файла: {os.path.getsize(OUTPUT_FILE)} байт")
    
    # Показываем что получилось
    log("\n📝 Первые 3 строки нового файла:")
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10:  # Покажем 10 строк для наглядности
                break
            if line.strip():
                log(f"   {line[:100]}...")
    
    log("=" * 50)

if __name__ == "__main__":
    main()