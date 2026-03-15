#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v8
- Проверка доступности
- Измерение скорости
- Только рабочие, максимум 1000
- Сохраняем оригинальные флаги из конфигов
- Переименовываем только формат
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
VERSION_CORE = "5"
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

def extract_original_flag(config_line: str) -> str:
    """
    Извлекает флаг из оригинального конфига
    Формат: vless://... #🇫🇮 Финляндия 001 | sni = ... | от catler
    """
    # Ищем # с флагом (эмодзи)
    flag_match = re.search(r'#([🇦-🇿]{2})', config_line)
    if flag_match:
        return flag_match.group(1)
    return '🌐'

def extract_original_country(config_line: str) -> str:
    """Извлекает название страны после флага"""
    # Ищем #🇫🇮 Финляндия
    country_match = re.search(r'#[🇦-🇿]{2}\s+([^|\d]+)', config_line)
    if country_match:
        return country_match.group(1).strip()
    return 'Anycast'

def extract_sni(config_url: str) -> str:
    """Извлекает sni из ссылки"""
    sni_match = re.search(r'sni=([^&]+)', config_url)
    if sni_match:
        return sni_match.group(1)
    return 'unknown'

def extract_host(config_url: str) -> str:
    """Извлекает хост из vless:// ссылки"""
    match = re.search(r'@([^:]+)', config_url)
    if match:
        return match.group(1)
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', config_url)
    if match:
        return match.group(1)
    return None

def check_config(config_line: str) -> Dict[str, Any]:
    """
    Проверяет работоспособность конфига
    Возвращает словарь с результатами или None если не работает
    """
    # Извлекаем чистую ссылку (до #)
    clean_url = config_line.split('#')[0].strip()
    
    host = extract_host(clean_url)
    if not host:
        return None
    
    try:
        # Определяем порт
        port_match = re.search(r':(\d+)', clean_url)
        port = int(port_match.group(1)) if port_match else 443
        
        # Пробуем TCP-соединение
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            latency = (time.time() - start) * 1000
            
            return {
                'original_line': config_line,
                'clean_url': clean_url,
                'host': host,
                'port': port,
                'latency': round(latency, 2),
                'flag': extract_original_flag(config_line),
                'country': extract_original_country(config_line),
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
    # Должен содержать vless:// и #
    if 'vless://' not in line or '#' not in line:
        return False
    return True

def generate_number(index: int) -> str:
    """Генерирует трёхзначный номер"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    print("=" * 70)
    print("🐱 Catwhite Configs Collector v8 — сохраняем оригинальные флаги")
    print("=" * 70)
    
    version = get_next_version()
    print(f"📦 Версия: {version}")
    
    # ШАГ 1: Собираем все конфиги из источников
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
        print("❌ Нет конфигов! Проверь источники.")
        return
    
    # ШАГ 2: Проверяем работоспособность (параллельно)
    print(f"\n🔄 Проверка работоспособности (макс {WORKERS} одновременно)...")
    
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
    
    print(f"\n✅ Найдено рабочих конфигов: {len(working_configs)}")
    
    if not working_configs:
        print("❌ Нет рабочих конфигов!")
        return
    
    # ШАГ 3: Сортируем по скорости
    working_configs.sort(key=lambda x: x['latency'])
    
    # ШАГ 4: Берём только самые быстрые
    best_configs = working_configs[:MAX_CONFIGS]
    print(f"📊 Отобрано лучших (до {MAX_CONFIGS}): {len(best_configs)}")
    
    # ШАГ 5: Сортируем по стране (по оригинальному названию)
    best_configs.sort(key=lambda x: (x['country'], x['clean_url']))
    
    # ШАГ 6: Генерируем итоговый файл
    output_lines = []
    
    # Шапка
    output_lines.append("#profile-title: 🌐🌿CatwhiteVPN🌿🌐")
    output_lines.append("#profile-update-interval: 1")
    output_lines.append(f"#announce: ⚡️Тгк @catlergememe версия: {version}⚡️")
    output_lines.append("#support-url: https://t.me/catlergememe/856")
    output_lines.append("#profile-web-page-url: https://twinkalex1470-crypto.github.io/Catsite/")
    output_lines.append("#hide-settings: 1")
    output_lines.append("")
    
    # Добавляем конфиги
    for idx, cfg in enumerate(best_configs):
        number = generate_number(idx)
        # Формат: vless://... #🇫🇮 001 Финляндия | sni = ... | от catler
        line = f"{cfg['clean_url']} #{cfg['flag']} {number} {cfg['country']} | sni = {cfg['sni']} | от catler"
        output_lines.append(line)
    
    # Сохраняем
    output_file = "configs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    # Сохраняем JSON с информацией
    json_file = "configs_debug.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'total_checked': len(unique_lines),
            'working_found': len(working_configs),
            'best_selected': len(best_configs),
            'avg_latency': sum(c['latency'] for c in best_configs)/len(best_configs) if best_configs else 0,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Готово! Сохранено {len(best_configs)} конфигов")
    print(f"📁 configs.txt — для подписки")
    print(f"📁 configs_debug.json — отладочная информация")
    print(f"⚡ Средний пинг: {sum(c['latency'] for c in best_configs)/len(best_configs):.1f}ms")
    print("=" * 70)

if __name__ == "__main__":
    main()