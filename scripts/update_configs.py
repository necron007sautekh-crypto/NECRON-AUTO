#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v10 — приоритет на лучшие конфиги
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
VERSION_CORE = "10"
VERSION_FILE = "version.txt"
MAX_CONFIGS = 1000
TIMEOUT = 5
WORKERS = 20

# ГЛАВНЫЙ источник (лучшие конфиги)
MAIN_SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt"

# Дополнительные источники (если не хватит)
EXTRA_SOURCES = [
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

def extract_config_parts(config_line: str) -> Dict[str, str]:
    """
    Извлекает чистый URL и оригинальный комментарий из строки конфига
    Формат: vless://... #🇫🇮 Финляндия 001 | sni = ... | от catler
    """
    if '#' in config_line:
        url_part, comment_part = config_line.split('#', 1)
        return {
            'url': url_part.strip(),
            'comment': '#' + comment_part.strip()
        }
    else:
        return {
            'url': config_line.strip(),
            'comment': ''
        }

def extract_host(config_url: str) -> str:
    """Извлекает хост из ссылки"""
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
    parts = extract_config_parts(config_line)
    clean_url = parts['url']
    
    host = extract_host(clean_url)
    if not host:
        return None
    
    try:
        # Определяем порт
        port_match = re.search(r':(\d+)', clean_url)
        port = int(port_match.group(1)) if port_match else 443
        
        # Проверяем соединение
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            latency = (time.time() - start) * 1000
            
            return {
                'full_line': config_line,
                'url': clean_url,
                'original_comment': parts['comment'],
                'host': host,
                'port': port,
                'latency': round(latency, 2),
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
    if 'vless://' not in line:
        return False
    return True

def generate_number(index: int) -> str:
    """Генерирует трёхзначный номер"""
    return f"{index+1:03d}"

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    print("=" * 70)
    print("🐱 Catwhite Configs Collector v10 — приоритет на лучшие конфиги")
    print("=" * 70)
    
    version = get_next_version()
    print(f"📦 Версия: {version}")
    print(f"🎯 Максимум конфигов: {MAX_CONFIGS}")
    
    # ШАГ 1: Загружаем конфиги из главного источника
    print(f"\n📡 Загрузка из ГЛАВНОГО источника:")
    print(f"  {MAIN_SOURCE[:80]}...")
    main_lines = fetch_configs(MAIN_SOURCE)
    main_valid = [line.strip() for line in main_lines if is_valid_config(line)]
    print(f" 