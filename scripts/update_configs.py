#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import sys
from datetime import datetime

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
    '🌐': 'Anycast'
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

def find_flag(text):
    """Найти флаг в тексте"""
    flags = list(COUNTRIES.keys())
    for flag in flags:
        if flag in text:
            return flag
    return '🌐'

def main():
    log("=" * 50)
    log("ЗАПУСК СКРИПТА")
    
    # Проверяем текущую директорию
    log(f"Текущая папка: {os.getcwd()}")
    log(f"Файлы здесь: {os.listdir('.')}")
    
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
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Пропускаем пустые и комментарии
        if not line or line.startswith('#'):
            continue
        
        # Проверяем что это конфиг
        if line.startswith(('vless://', 'vmess://', 'trojan://', 'hysteria://', 'ss://')):
            try:
                # Разделяем URL и комментарий
                if '#' in line:
                    url, comment = line.split('#', 1)
                else:
                    url, comment = line, ''
                
                # Ищем флаг в комментарии
                flag = find_flag(comment)
                country = COUNTRIES.get(flag, 'Anycast')
                
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
    
    if len(configs) == 0:
        log("ОШИБКА: Нет конфигов!")
        return
    
    # Сохраняем файл
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header + configs))
        
        log(f"✅ Файл сохранён: {OUTPUT_FILE}")
        log(f"Размер: {os.path.getsize(OUTPUT_FILE)} байт")
        
        # Показываем первые 3 строки для проверки
        log("\nПЕРВЫЕ 3 КОНФИГА:")
        for cfg in configs[:3]:
            short = cfg[:100] + "..." if len(cfg) > 100 else cfg
            log(f"  {short}")
            
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