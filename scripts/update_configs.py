#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Catwhite Configs Collector v25 — конвертер vless:// в JSON
- Берём все конфиги из WHITE-CIDR-RU-all.txt
- Парсим каждый vless:// URL
- Генерируем полноценный JSON для клиентов
- Сохраняем массив объектов
- Автообновление раз в 5 часов
"""

import requests
import json
import time
import os
import re
import sys
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import unquote

# ================= НАСТРОЙКИ =================
VERSION_CORE = "25"
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

def parse_vless_url(url: str) -> Dict[str, Any]:
    """
    Парсит vless:// URL в словарь с параметрами
    Формат: vless://uuid@host:port?параметры#комментарий
    """
    result = {
        'protocol': 'vless',
        'uuid': None,
        'host': None,
        'port': 443,
        'params': {},
        'comment': ''
    }
    
    try:
        # Убираем vless://
        if not url.startswith('vless://'):
            return result
        
        without_proto = url[8:]
        
        # Разделяем на основную часть и комментарий
        if '#' in without_proto:
            main_part, comment = without_proto.split('#', 1)
            result['comment'] = '#' + comment
        else:
            main_part = without_proto
        
        # Разделяем на часть с хостом и параметры
        if '?' in main_part:
            host_part, query = main_part.split('?', 1)
            # Парсим параметры
            params = urllib.parse.parse_qs(query)
            # Преобразуем значения из списков в строки
            for key, value in params.items():
                if isinstance(value, list) and len(value) > 0:
                    result['params'][key] = value[0]
        else:
            host_part = main_part
        
        # Парсим host_part (uuid@host:port)
        if '@' in host_part:
            uuid, host_with_port = host_part.split('@', 1)
            result['uuid'] = uuid
            
            if ':' in host_with_port:
                host, port_str = host_with_port.split(':', 1)
                result['host'] = host
                try:
                    result['port'] = int(port_str)
                except:
                    pass
            else:
                result['host'] = host_with_port
    except Exception as e:
        log(f"⚠️ Ошибка парсинга {url[:50]}...: {e}")
    
    return result

def extract_flag_from_comment(comment: str) -> str:
    """Извлекает флаг из комментария"""
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

def vless_to_json_config(vless_url: str, index: int, total: int) -> Dict[str, Any]:
    """Конвертирует vless:// URL в JSON-конфиг для клиента"""
    parsed = parse_vless_url(vless_url)
    flag = extract_flag_from_comment(parsed['comment'])
    country = extract_country_from_comment(parsed['comment'])
    
    # Формируем remark
    num = f"{index+1:03d}"
    remark = f"{flag} {num} {country} | 💠 | от catler"
    
    # Базовая структура JSON (общая для всех)
    config = {
        "dns": {
            "queryStrategy": "UseIPv4",
            "servers": [
                "https+local://1.1.1.1/dns-query",
                "https+local://8.8.8.8/dns-query",
                "77.88.8.8"
            ]
        },
        "inbounds": [
            {
                "listen": "127.0.0.1",
                "port": 10808,
                "protocol": "socks",
                "settings": {"udp": True},
                "tag": "socks"
            },
            {
                "listen": "127.0.0.1",
                "port": 10809,
                "protocol": "http",
                "tag": "http"
            }
        ],
        "outbounds": [
            {
                "tag": f"s{index+1}",
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": parsed['host'],
                            "port": parsed['port'],
                            "users": [
                                {
                                    "id": parsed['uuid'],
                                    "flow": parsed['params'].get('flow', ''),
                                    "encryption": parsed['params'].get('encryption', 'none')
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": parsed['params'].get('type', 'tcp'),
                    "security": parsed['params'].get('security', 'none'),
                }
            },
            {
                "protocol": "freedom",
                "tag": "direct"
            },
            {
                "protocol": "blackhole",
                "tag": "block"
            }
        ],
        "remarks": remark,
        "routing": {
            "balancers": [
                {
                    "fallbackTag": f"s{index+1}",
                    "selector": [f"s{index+1}"],
                    "strategy": {
                        "settings": {
                            "baselines": ["2s"],
                            "expected": 1,
                            "maxRTT": "3s",
                            "tolerance": 0.3
                        },
                        "type": "leastLoad"
                    },
                    "tag": "auto_bal"
                }
            ],
            "domainStrategy": "IPIfNonMatch",
            "rules": [
                {
                    "outboundTag": "block",
                    "protocol": ["bittorrent"],
                    "type": "field"
                },
                {
                    "balancerTag": "auto_bal",
                    "inboundTag": ["socks", "http"],
                    "network": "tcp,udp",
                    "type": "field"
                }
            ]
        }
    }
    
    # Добавляем reality-специфичные настройки если есть
    if parsed['params'].get('security') == 'reality':
        config['outbounds'][0]['streamSettings']['realitySettings'] = {
            "publicKey": parsed['params'].get('pbk', ''),
            "shortId": parsed['params'].get('sid', ''),
            "spiderX": parsed['params'].get('spx', ''),
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome'),
            "show": False
        }
    
    # Добавляем TLS настройки если нужно
    if parsed['params'].get('security') == 'tls':
        config['outbounds'][0]['streamSettings']['tlsSettings'] = {
            "serverName": parsed['params'].get('sni', parsed['host']),
            "fingerprint": parsed['params'].get('fp', 'chrome')
        }
    
    return config

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

# ================= ОСНОВНАЯ ЛОГИКА =================

def main():
    log("🚀 Catwhite Configs Collector v25 — конвертер vless → JSON")
    version = get_next_version()
    log(f"📦 Версия: {version}")
    log(f"⏱️  Автообновление: каждые 5 часов")

    # Загружаем конфиги
    configs = fetch_configs()
    
    if not configs:
        log("❌ Нет конфигов, выход")
        sys.exit(1)

    log(f"\n📊 Всего конфигов: {len(configs)}")

    # Конвертируем каждый vless:// в JSON
    json_configs = []
    finnish_count = 0
    other_count = 0
    anycast_count = 0
    failed = 0

    for idx, line in enumerate(configs):
        # Пропускаем не-vless строки
        if not line.startswith('vless://'):
            failed += 1
            continue
            
        try:
            json_config = vless_to_json_config(line, idx, len(configs))
            json_configs.append(json_config)
            
            # Статистика по странам
            flag = extract_flag_from_comment(line)
            country = extract_country_from_comment(line)
            if country == 'Финляндия':
                finnish_count += 1
            elif country == 'Anycast':
                anycast_count += 1
            else:
                other_count += 1
                
        except Exception as e:
            log(f"⚠️ Ошибка конвертации строки {idx+1}: {e}")
            failed += 1

    log(f"\n📊 Статистика конвертации:")
    log(f"   • Успешно конвертировано: {len(json_configs)}")
    log(f"   • Не удалось: {failed}")
    log(f"   • 🇫🇮 Финских: {finnish_count}")
    log(f"   • 🌍 Других стран: {other_count}")
    log(f"   • 🌐 Anycast: {anycast_count}")

    # Сохраняем JSON
    json_file = "configs.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_configs, f, ensure_ascii=False, indent=2)
    
    log(f"✅ {json_file} сохранён, {len(json_configs)} конфигов")

    # Отладочная информация
    debug = {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'source': SOURCE,
        'total_original': len(configs),
        'converted': len(json_configs),
        'failed': failed,
        'finnish_count': finnish_count,
        'other_count': other_count,
        'anycast_count': anycast_count,
    }
    
    with open('debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug, f, indent=2)

    log(f"\n✨ Готово! Подписка (JSON) обновится через 5 часов")
    log(f"📁 Ссылка: https://twinkalex1470-crypto.github.io/CatwhiteAUTO/configs.json")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)