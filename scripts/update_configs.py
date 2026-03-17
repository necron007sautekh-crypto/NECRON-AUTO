#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import re
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

# ================= ФУНКЦИИ =================
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_next_version() -> str:
    """Возвращает следующую версию на основе version.txt"""
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
    return str(next_ver)

def extract_flag_and_country(comment: str) -> tuple:
    """
    Извлекает флаг из закодированного комментария и возвращает (флаг, название_страны)
    """
    try:
        # Декодируем URL-кодировку (проценты)
        decoded = unquote(comment)
        
        # Ищем эмодзи-флаг (два символа из диапазона флагов)
        flag_match = re.search(r'([🇦-🇿]{2})', decoded)
        if flag_match:
            flag = flag_match.group(1)
            # Получаем название страны из карты, если есть, иначе "Неизвестно"
            country = COUNTRY_MAP.get(flag, 'Неизвестно')
            return flag, country
    except Exception as e:
        log(f"⚠️ Ошибка извлечения флага: {e}")
    
    # Если флаг не найден или ошибка
    return '🌐', 'Anycast'

def process_config_line(line: str) -> str:
    """
    Обрабатывает одну строку конфига:
    - Оставляет часть ДО # без изменений
    - Генерирует новую часть ПОСЛЕ # по шаблону
    """
    line = line.strip()
    if not line:
        return ""
    
    # Разделяем на URL и старый комментарий
    if '#' in line:
        url_part, old_comment = line.split('#', 1)
        url_part = url_part.strip()
    else:
        # Если нет комментария (такого не должно быть, но на всякий случай)
        return line
    
    # Извлекаем флаг и страну из старого комментария
    flag, country = extract_flag_and_country(old_comment)
    
    # Формируем новое название
    new_name = f"{flag} {country} |💠| от катлер"
    
    # Собираем строку обратно
    return f"{url_part}#{new_name}"

def main():
    log("🚀 Запуск сборщика конфигов Catwhite")
    
    # Получаем следующую версию
    version = get_next_version()
    log(f"📦 Версия сборки: {version}")
    
    # Скачиваем исходный файл
    try:
        log(f"📡 Загрузка из {SOURCE_URL}")
        response = requests.get(SOURCE_URL, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            log(f"❌ Ошибка загрузки: HTTP {response.status_code}")
            return
        
        lines = response.text.splitlines()
        log(f"✅ Загружено {len(lines)} строк")
        
    except Exception as e:
        log(f"❌ Ошибка при загрузке: {e}")
        return
    
    # Подготавливаем заголовок для выходного файла
    header = [
        "#profile-title: 👾🌿CatwhiteVPN🌿👾",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        ""  # пустая строка для разделения
    ]
    
    # Обрабатываем каждую строку
    processed_configs = []
    skipped = 0
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Пропускаем пустые строки и комментарии источника
        if not line or line.startswith('#'):
            continue
        
        # Проверяем, что это похоже на конфиг (начинается с протокола)
        if line.startswith(('vless://', 'vmess://', 'trojan://', 'hysteria2://', 'ss://')):
            try:
                new_line = process_config_line(line)
                processed_configs.append(new_line)
            except Exception as e:
                log(f"⚠️ Ошибка обработки строки {i}: {e}")
                skipped += 1
        else:
            # Если строка не похожа на конфиг, пропускаем
            skipped += 1
    
    # Формируем полный вывод
    output_lines = header + processed_configs
    
    # Сохраняем в файл
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        log(f"\n📊 Статистика:")
        log(f"   • Обработано конфигов: {len(processed_configs)}")
        log(f"   • Пропущено строк: {skipped}")
        log(f"   • Версия: {version}")
        log(f"\n✅ Файл {OUTPUT_FILE} успешно сохранён")
        
        # Показываем первые 3 конфига для примера
        if processed_configs:
            log("\n📝 Пример первых 3 конфигов:")
            for sample in processed_configs[:3]:
                # Обрезаем длинные строки для читаемости
                short = sample[:80] + "..." if len(sample) > 80 else sample
                log(f"   • {short}")
                
    except Exception as e:
        log(f"❌ Ошибка сохранения файла: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()