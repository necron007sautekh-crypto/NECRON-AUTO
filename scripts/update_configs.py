[21.03.2026 23:02] Ghost: #!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import socket
from datetime import datetime
from urllib.parse import unquote, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== НАСТРОЙКИ ==========
SOURCES_IGARECK = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/Delta-Kronecker/V2ray-Config/refs/heads/main/config/protocols/vless.txt",
]

SOURCES_CHECKED = [
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/main/out/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/main/out/default/all-secure.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/main/out/split-by-protocols/vless-secure.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/main/githubmirror/ru-sni/vless_ru.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/main/githubmirror/clean/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/main/checked/RU_Best/ru_white.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/main/checked/My_Euro/my_euro.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/light.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/vless.txt",
]

OUTPUT_FILE = "configs.txt"
MAX_FILE = "max.txt"
VERSION_FILE = "version.txt"
CHECK_TIMEOUT = 3

# ========== СЛОВАРЬ СТРАН ==========
COUNTRIES = {
    '🇦🇹': 'Австрия', '🇦🇺': 'Австралия', '🇧🇪': 'Бельгия', '🇧🇷': 'Бразилия',
    '🇬🇧': 'Великобритания', '🇭🇺': 'Венгрия', '🇩🇪': 'Германия', '🇮🇱': 'Израиль',
    '🇮🇳': 'Индия', '🇪🇸': 'Испания', '🇮🇹': 'Италия', '🇨🇦': 'Канада',
    '🇱🇻': 'Латвия', '🇱🇹': 'Литва', '🇱🇺': 'Люксембург', '🇳🇱': 'Нидерланды',
    '🇳🇴': 'Норвегия', '🇦🇪': 'ОАЭ', '🇵🇱': 'Польша', '🇷🇺': 'Россия',
    '🇺🇸': 'США', '🇹🇷': 'Турция', '🇫🇮': 'Финляндия', '🇫🇷': 'Франция',
    '🇨🇿': 'Чехия', '🇸🇪': 'Швеция', '🇪🇪': 'Эстония', '🇯🇵': 'Япония',
    '🇧🇾': 'Беларусь', '🇰🇿': 'Казахстан', '🇺🇦': 'Украина',
    '🇪🇺': 'Европа', '🌐': 'Anycast'
}

FLAG_PATTERNS = {
    '%F0%9F%87%A6%F0%9F%87%B9': '🇦🇹', '%F0%9F%87%A7%F0%9F%87%AA': '🇧🇪',
    '%F0%9F%87%A7%F0%9F%87%BE': '🇧🇾', '%F0%9F%87%A8%F0%9F%87%BF': '🇨🇿',
    '%F0%9F%87%A9%F0%9F%87%AA': '🇩🇪', '%F0%9F%87%AA%F0%9F%87%AA': '🇪🇪',
    '%F0%9F%87%AB%F0%9F%87%AE': '🇫🇮', '%F0%9F%87%AB%F0%9F%87%B7': '🇫🇷',
    '%F0%9F%87%AC%F0%9F%87%A7': '🇬🇧', '%F0%9F%87%B0%F0%9F%87%BF': '🇰🇿',
    '%F0%9F%87%B1%F0%9F%87%BB': '🇱🇻', '%F0%9F%87%B1%F0%9F%87%B9': '🇱🇹',
    '%F0%9F%87%B3%F0%9F%87%B1': '🇳🇱', '%F0%9F%87%B3%F0%9F%87%B4': '🇳🇴',
    '%F0%9F%87%B5%F0%9F%87%B1': '🇵🇱', '%F0%9F%87%B7%F0%9F%87%BA': '🇷🇺',
    '%F0%9F%87%BA%F0%9F%87%B8': '🇺🇸',
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_max_limit():
    try:
        if os.path.exists(MAX_FILE):
            with open(MAX_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 500

def get_version():
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

def extract_flag(comment):
    for encoded, flag in FLAG_PATTERNS.items():
        if encoded in comment:
            return flag
    try:
        decoded = unquote(comment)
        for flag in COUNTRIES.keys():
            if flag in decoded:
                return flag
    except:
        pass
    return '🌐'
[21.03.2026 23:02] Ghost: def parse_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    if not (line.startswith('vless://') or line.startswith('vmess://') or 
            line.startswith('trojan://') or line.startswith('hysteria2://')):
        return None
    try:
        if '#' in line:
            url, comment = line.split('#', 1)
        else:
            url, comment = line, ''
        flag = extract_flag(comment)
        country = COUNTRIES.get(flag, 'Anycast')
        return (url, flag, country)
    except:
        return None

def fetch_source(url, name):
    log(f"📡 {name}...")
    try:
        r = requests.get(url, timeout=30)
        r.encoding = 'utf-8'
        if r.status_code != 200:
            log(f"   ❌ HTTP {r.status_code}")
            return []
        configs = []
        for line in r.text.split('\n'):
            parsed = parse_line(line)
            if parsed:
                configs.append(parsed)
        log(f"   +{len(configs)} конфигов")
        return configs
    except Exception as e:
        log(f"   ❌ Ошибка: {e}")
        return []

def check_config(config):
    url, flag, country = config
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CHECK_TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        return (url, flag, country, result == 0)
    except:
        return (url, flag, country, False)

def main():
    log("=" * 60)
    log("NECRON-AUTO - Сбор и проверка конфигов")
    
    max_limit = get_max_limit()
    log(f"Лимит из max.txt: {max_limit}")
    
    version = get_version()
    log(f"Версия: {version}")
    
    # ЭТАП 1: igareck (без проверки — белые списки)
    log("\nЭТАП 1: igareck (байпас)")
    igareck_configs = []
    for url in SOURCES_IGARECK:
        igareck_configs.extend(fetch_source(url, "igareck"))
    log(f"Итого из igareck: {len(igareck_configs)}")
    
    # ЭТАП 2: проверка остальных источников
    log("\nЭТАП 2: скачивание остальных источников")
    raw_configs = []
    for url in SOURCES_CHECKED:
        name = url.split('/')[-1][:30]
        raw_configs.extend(fetch_source(url, name))
    log(f"Всего скачано: {len(raw_configs)}")
    
    log(f"\nПроверка {len(raw_configs)} конфигов (30 потоков)...")
    working_configs = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_config, cfg) for cfg in raw_configs]
        for future in as_completed(futures):
            url, flag, country, ok = future.result()
            if ok:
                working_configs.append((url, flag, country))
    log(f"Живых: {len(working_configs)}/{len(raw_configs)}")
    
    # ЭТАП 3: объединение + дедуп
    log("\nЭТАП 3: объединение и удаление дублей")
    all_configs = igareck_configs + working_configs
    unique = []
    seen = set()
    for url, flag, country in all_configs:
        if url not in seen:
            seen.add(url)
            unique.append((url, flag, country))
    log(f"Уникальных: {len(unique)}")
    
    if len(unique) > max_limit:
        unique = unique[:max_limit]
        log(f"Обрезано до лимита {max_limit}")
    
    # ЭТАП 4: сохранение
    log("\nЭТАП 4: сохранение")
    header = [
        "#profile-title: NECRON-AUTO",
        "#profile-update-interval: 1",
        f"#announce: NECRON-AUTO версия: {version}",
        "#hide-settings: 1",
        ""
    ]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header))
        for url, flag, country in unique:
            f.write(f"{url}#{flag} {country} | NECRON\n")
    
    log(f"\n✅ Сохранено {len(unique)} живых конфигов в {OUTPUT_FILE}")
[21.03.2026 23:02] Ghost: # Статистика
    stats = {}
    for _, flag, _ in unique:
        stats[flag] = stats.get(flag, 0) + 1
    log("\nТоп-10 стран:")
    for flag, count in sorted(stats.items(), key=lambda x: -x[1])[:10]:
        country = COUNTRIES.get(flag, 'Anycast')
        log(f"   {flag} {country}: {count}")
    
    log("\n" + "=" * 60)
    log("NECRON-AUTO готов к бою! 🚀")

if name == "main":
    try:
        main()
    except Exception as e:
        log(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
