#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector — простая TXT-подписка
- Берём все конфиги из WHITE-CIDR-RU-all.txt
- Переименовываем их в нужный формат
- Добавляем шапку с названием и ссылками
- Сохраняем как configs.txt
"""

import requests
import os
import re
import sys
from datetime import datetime
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "1"
VERSION_FILE = "version.txt"
SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

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

def extract_country_from_flag(flag: str) -> str:
    """Возвращает название страны по флагу"""
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

def process_config_line(line: str, index: int) -> str:
    """Обрабатывает одну строку конфига, возвращает готовую строку для вывода"""
    # Разделяем на URL и комментарий
    if '#' in line:
        url_part, comment_part = line.split('#', 1)
        url_part = url_part.strip()
        comment = '#' + comment_part.strip()
    else:
        url_part = line.strip()
        comment = ''

    flag = extract_flag_from_comment(comment)
    country = extract_country_from_flag(flag)
    num = f"{index+1:03d}"

    return f"{url_part}#{flag} {num} {country} | 💠 | от catler"

def fetch_configs():
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
        log(f"❌ Ошибка: {e}")
    return []

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Catwhite Configs Collector — простая TXT-подписка")
    version = get_next_version()
    log(f"📦 Версия: {version}")

    configs = fetch_configs()
    if not configs:
        log("❌ Нет конфигов")
        sys.exit(1)

    log(f"\n📊 Всего конфигов: {len(configs)}")

    # Формируем выходной файл
    output_lines = [
        "#profile-title: 🌐🌿CatwhiteVPN🌿🌐",
        "#profile-update-interval: 5",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]

    processed = 0
    finnish_count = 0
    other_count = 0
    anycast_count = 0

    for idx, line in enumerate(configs):
        if not line.startswith('vless://'):
            continue
        try:
            new_line = process_config_line(line, idx)
            output_lines.append(new_line)
            processed += 1

            # Статистика
            if '🇫🇮' in new_line:
                finnish_count += 1
            elif '🌐' in new_line:
                anycast_count += 1
            else:
                other_count += 1
        except Exception as e:
            log(f"⚠️ Ошибка строки {idx+1}: {e}")

    # Сохраняем файл
    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    log(f"\n📊 Статистика:")
    log(f"   • Всего конфигов: {processed}")
    log(f"   • 🇫🇮 Финских: {finnish_count}")
    log(f"   • 🌍 Других стран: {other_count}")
    log(f"   • 🌐 Anycast: {anycast_count}")
    log(f"✅ configs.txt сохранён")

    log(f"\n✨ Готово! Ссылка:")
    log(f"https://twinkalex1470-crypto.github.io/CatwhiteAUTO/configs.txt")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)