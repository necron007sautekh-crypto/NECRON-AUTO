#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v18 — приоритет Финляндии и лимит 30 на страну
"""

import requests
import json
import time
import os
import re
import socket
import sys
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "18"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 300
MAX_PER_COUNTRY = 30  # максимум конфигов на одну страну (кроме Финляндии)
TIMEOUT = 5
WORKERS = 20

# ================= СПИСОК ИСТОЧНИКОВ =================
SOURCES = [
    # Основной (самый полный)
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    # Для мобилок (первые 150)
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    # Для мобилок (вторые 150)
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    # Ещё один источник от AvenCores
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt",
]

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

def extract_host(config_url: str) -> str:
    """Извлекает хост из URL"""
    m = re.search(r'@([^:]+)', config_url)
    if m:
        return m.group(1)
    m = re.search(r'(\d+\.\d+\.\d+\.\d+)', config_url)
    if m:
        return m.group(1)
    return None

def extract_flag_from_comment(comment: str) -> str:
    """Извлекает флаг из комментария (поддержка URL-кодировки и обычных флагов)"""
    try:
        # Декодируем URL-кодировку
        decoded = unquote(comment)
        # Ищем эмодзи флага (два символа подряд из диапазона флагов)
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
    }
    return country_map.get(flag, 'Anycast')

def is_allowed_flag(flag: str) -> bool:
    """Проверяет, что флаг в списке разрешённых (не Anycast)"""
    allowed_flags = {
        '🇫🇮', '🇩🇪', '🇳🇱', '🇷🇺', '🇺🇸', '🇬🇧', '🇫🇷', '🇸🇬', '🇸🇪', '🇵🇱',
        '🇪🇪', '🇪🇸', '🇹🇷', '🇭🇺', '🇮🇹', '🇳🇴', '🇱🇺', '🇨🇿', '🇦🇹', '🇨🇦',
        '🇯🇵', '🇦🇪', '🇮🇳', '🇧🇷', '🇿🇦', '🇦🇺', '🇪🇺'
    }
    return flag in allowed_flags

def check_config(config_line: str) -> Dict[str, Any]:
    """Проверяет работоспособность конфига"""
    parts = extract_config_parts(config_line)
    url = parts['url']
    host = extract_host(url)
    if not host:
        return None

    port_match = re.search(r':(\d+)', url)
    port = int(port_match.group(1)) if port_match else 443

    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            latency = (time.time() - start) * 1000
            flag = extract_flag_from_comment(parts['comment'])
            
            # Если флаг не разрешён – пропускаем
            if not is_allowed_flag(flag):
                return None
                
            return {
                'full_line': config_line,
                'url': url,
                'original_comment': parts['comment'],
                'flag': flag,
                'country': extract_country_from_comment(parts['comment']),
                'host': host,
                'port': port,
                'latency': round(latency, 2),
                'working': True
            }
    except:
        return None
    return None

def fetch_configs(source: str) -> List[str]:
    """Скачивает конфиги из источника"""
    try:
        resp = requests.get(source, timeout=15)
        if resp.status_code == 200:
            return resp.text.strip().split('\n')
    except:
        pass
    return []

def is_valid_config(line: str) -> bool:
    """Проверяет, что строка является конфигом"""
    line = line.strip()
    if not line or line.startswith('#'):
        return False
    # Пропускаем, если это не vless и не vmess
    if not (line.startswith('vless://') or line.startswith('vmess://')):
        return False
    return True

def generate_number(index: int) -> str:
    """Генерирует трёхзначный номер"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Старт сбора из нескольких источников")
    version = get_next_version()
    log(f"📦 Версия: {version}")

    # Собираем все конфиги из всех источников
    all_configs = []
    log(f"\n📡 Загрузка из {len(SOURCES)} источников:")
    
    for src in SOURCES:
        log(f"  {src[:80]}...")
        lines = fetch_configs(src)
        valid = [line.strip() for line in lines if is_valid_config(line)]
        all_configs.extend(valid)
        log(f"    ✅ Найдено {len(valid)} конфигов")

    if not all_configs:
        log("❌ Нет конфигов, выход")
        sys.exit(1)

    # Убираем дубликаты
    unique = list(set(all_configs))
    log(f"\n📊 Уникальных конфигов: {len(unique)}")

    # Проверка доступности
    log(f"\n🔄 Проверка {len(unique)} конфигов...")
    working = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_line = {executor.submit(check_config, line): line for line in unique}
        for future in as_completed(future_to_line):
            checked += 1
            result = future.result()
            if result:
                working.append(result)
            if checked % 50 == 0:
                log(f"   Проверено {checked}/{len(unique)}, найдено {len(working)} рабочих")

    log(f"\n✅ Найдено рабочих конфигов: {len(working)}")
    
    if not working:
        log("❌ Нет рабочих конфигов, выход")
        sys.exit(1)

    # Сортируем все рабочие по скорости
    working.sort(key=lambda x: x['latency'])

    # Отбираем финские первыми (все, сколько есть)
    finnish = [c for c in working if c['country'] == 'Финляндия']
    remaining = [c for c in working if c['country'] != 'Финляндия']
    
    log(f"\n🇫🇮 Найдено финских: {len(finnish)}")
    
    # Группируем остальные по странам
    countries = {}
    for cfg in remaining:
        country = cfg['country']
        if country not in countries:
            countries[country] = []
        countries[country].append(cfg)
    
    # Для каждой страны оставляем не больше MAX_PER_COUNTRY самых быстрых
    selected_others = []
    for country, cfgs in countries.items():
        # Берём первые MAX_PER_COUNTRY (они уже отсортированы по скорости)
        selected = cfgs[:MAX_PER_COUNTRY]
        selected_others.extend(selected)
        log(f"   {country}: выбрано {len(selected)} из {len(cfgs)}")
    
    # Сортируем остальные по стране и скорости
    selected_others.sort(key=lambda x: (x['country'], x['latency']))
    
    # Финальный список: сначала все финские, потом остальные
    final_list = finnish + selected_others
    
    # Если получилось больше MAX_CONFIGS, обрезаем (но финские останутся)
    if len(final_list) > MAX_CONFIGS:
        # Оставляем все финские + первые (MAX_CONFIGS - len(finnish)) из остальных
        final_list = finnish + selected_others[:MAX_CONFIGS - len(finnish)]
    
    log(f"\n📊 Итоговое количество: {len(final_list)} конфигов")
    log(f"   🇫🇮 Финских: {len(finnish)}")
    log(f"   🌍 Других стран: {len(final_list) - len(finnish)}")

    # Генерация файла
    log("\n📝 Формирование configs.txt ...")
    output = [
        "#profile-title: 👾🌿CatwhiteVPN🌿👾",
        "#profile-update-interval: 1",
        f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️",
        "#support-url: https://t.me/catlergememe/856",
        "#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/",
        "#hide-settings: 1",
        ""
    ]

    for idx, cfg in enumerate(final_list):
        num = generate_number(idx)
        # Извлекаем sni из комментария (если есть)
        sni_match = re.search(r'sni\s*=\s*([^|\s]+)', cfg['original_comment'])
        sni = sni_match.group(1) if sni_match else 'unknown'
        
        # Формируем строку
        line = f"{cfg['url']}#{cfg['flag']} {num} {cfg['country']} | 💠 | от catler"
        output.append(line)

    # Сохраняем основной файл
    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    log(f"✅ configs.txt сохранён, {len(final_list)} конфигов")

    # Отладочный JSON
    debug = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'total_checked': len(unique),
        'working_found': len(working),
        'best_selected': len(final_list),
        'finnish_count': len(finnish),
        'per_country': {c: len([x for x in final_list if x['country'] == c]) for c in set(x['country'] for x in final_list)},
        'avg_latency': round(sum(c['latency'] for c in final_list) / len(final_list), 1) if final_list else 0,
    }
    
    with open('configs_debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)
    log(f"📁 configs_debug.json сохранён")

    log(f"\n✨ Готово! Средний пинг отобранных: {debug['avg_latency']} ms")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)