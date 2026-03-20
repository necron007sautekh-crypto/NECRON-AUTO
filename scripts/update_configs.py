def fetch_and_process_source(url, source_name):
    log(f"📡 Загрузка из {source_name}...")
    
    try:
        r = requests.get(url, timeout=30)
        r.encoding = 'utf-8'
        
        if r.status_code != 200:
            log(f"❌ Ошибка {source_name}: HTTP {r.status_code}")
            return [], 0
        
        lines = r.text.strip().split('\n')
        log(f"✅ {source_name}: всего {len(lines)} строк")
        
        # Собираем все конфиги
        configs = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Проверяем все возможные протоколы
            if (line.startswith('vless://') or 
                line.startswith('vmess://') or 
                line.startswith('trojan://') or 
                line.startswith('hysteria2://') or 
                line.startswith('ss://')):
                
                try:
                    if '#' in line:
                        url_part, comment = line.split('#', 1)
                    else:
                        url_part, comment = line, ''
                    
                    flag = extract_flag_from_comment(comment)
                    country = COUNTRIES.get(flag, 'Anycast')
                    
                    # ← Вот здесь меняем подпись
                    new_line = f"{url_part}#{flag} {country} | NECRON-AUTO"   # или любой вариант выше
                    
                    configs.append(new_line)
                    
                except Exception as e:
                    log(f"   ⚠️ Ошибка обработки строки: {e}")
        
        log(f"   Найдено конфигов: {len(configs)}")
        return configs, 0
        
    except Exception as e:
        log(f"❌ Ошибка скачивания {source_name}: {e}")
        return [], 0
