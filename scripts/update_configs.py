#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import re
import sys
from datetime import datetime
from urllib.parse import unquote

# ========== НАСТРОЙКИ ==========
SOURCE_URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"
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
# Некоторые распространённые флаги в URL-кодировке
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
}

def log(msg):
    """Простое логирование с временем"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_version():
    """Получить следующую версию"""
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
    """Извлекает флаг из закодированного комментария"""
    # Сначала пробуем найти по URL-кодировкам
    for encoded, flag in FLAG_PATTERNS.items():
        if encoded in comment:
            return flag

    # Если не нашли, пробуем декодировать и искать эмодзи
    try:
        decoded = unquote(comment)
        # Ищем любой флаг из нашего словаря
        for flag in COUNTRIES.keys():
            if flag in decoded:
                return flag
    except:
        pass

    return '🌐'

def main():
    log("=" * 50)
    log("ЗАПУСК СКРИПТА")

    # Проверяем текущую директорию
    log(f"Текущая папка: {os.getcwd()}")

    # Версия
    version = get_version()
    log(f"Версия: {version}")

    # Скачиваем файл
    try:
        log(f"Скачиваю: {SOURCE_URL}")
        r = requests.get(SOURCE_URL, timeout=30)
        r.encoding = 'utf-8'

        if r.status_code != 200:
            log(f"ОШИБКА: HTTP {r.status_code}")
            return

        lines = r.text.strip().split('\n')
        log(f"Скачано строк: {len(lines)}")

        # Покажем первые несколько строк для отладки
        log("Первые 5 строк источника:")
        for i, line in enumerate(lines[:5]):
            if line.strip():
                log(f"  {i+1}: {line[:100]}...")

    except Exception as e:
        log(f"ОШИБКА скачивания: {e}")
        return

    # Заголовок для выходного файла
    header = [
        "#profile-title: 👾🌿CatwhiteVPN🌿👾",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]

    # Обрабатываем строки
    configs = []
    skipped = 0
    flag_stats = {}

    for i, line in enumerate(lines):
        line = line.strip()

        # Пропускаем пустые и комментарии
        if not line or line.startswith('#'):
            continue

        # Проверяем что это конфиг
        if line.startswith(('vless://', 'vmess://', 'trojan://', 'hysteria2://', 'ss://')):
            try:
                # Разделяем URL и комментарий
                if '#' in line:
                    url, comment = line.split('#', 1)
                else:
                    url, comment = line, ''

                # Извлекаем флаг из комментария
                flag = extract_flag_from_comment(comment)
                country = COUNTRIES.get(flag, 'Anycast')

                # Собираем статистику по флагам
                flag_stats[flag] = flag_stats.get(flag, 0) + 1

                # Собираем новую строку
                new_line = f"{url}#{flag} {country} |💠| от катлер"
                configs.append(new_line)

            except Exception as e:
                log(f"Ошибка в строке {i+1}: {e}")
                skipped += 1
        else:
            skipped += 1

    log(f"\nРЕЗУЛЬТАТ:")
    log(f"- Конфигов: {len(configs)}")
    log(f"- Пропущено: {skipped}")

    # Статистика по странам
    log("\nСтатистика по странам:")
    for flag, count in sorted(flag_stats.items(), key=lambda x: -x[1]):
        country = COUNTRIES.get(flag, 'Anycast')
        log(f"  {flag} {country}: {count}")

    if len(configs) == 0:
        log("ОШИБКА: Нет конфигов!")
        return

    # Сохраняем файл
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header + configs))

        log(f"\n✅ Файл сохранён: {OUTPUT_FILE}")
        log(f"Размер: {os.path.getsize(OUTPUT_FILE)} байт")

        # Показываем первые 3 строки для проверки
        log("\nПЕРВЫЕ 3 КОНФИГА:")
        for cfg in configs[:3]:
            if '#' in cfg:
                url_part = cfg.split('#')[0][:50] + "..."
                name_part = cfg.split('#')[1]
                log(f"  {url_part}#{name_part}")

    except Exception as e:
        log(f"ОШИБКА сохранения: {e}")

    log("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()