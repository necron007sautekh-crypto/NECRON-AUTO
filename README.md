# 🐱 Catwhite Configs — Автоматический сборщик VPN-конфигов

[![Update Configs](https://github.com/твой-ник/catwhite-configs/actions/workflows/update.yml/badge.svg)](https://github.com/твой-ник/catwhite-configs/actions/workflows/update.yml)

Автоматический сбор и проверка VPN-конфигов (VLESS, VMess, Trojan, Shadowsocks) для проектов **CatwhiteVPN** и **GlashaVPN**.

## 🔥 Возможности

- ✅ Сбор конфигов из множества источников
- ✅ Автоматическое удаление дубликатов
- ✅ Добавление флагов стран (🇫🇮, 🇳🇱, 🇩🇪, 🇺🇸 и др.)
- ✅ Генерация JSON с метаданными
- ✅ Обновление **каждый час** через GitHub Actions
- ✅ Публикация через GitHub Pages

## 📥 Ссылки для подписки

| Формат | Ссылка |
|--------|--------|
| 📄 **TXT (для Happ)** | `https://твой-ник.github.io/catwhite-configs/configs.txt` |
| 📦 **JSON (с метаданными)** | `https://твой-ник.github.io/catwhite-configs/configs.json` |

## 🛠️ Технологии

- Python 3.10
- GitHub Actions
- GitHub Pages
- Requests

## 📅 Обновление

Конфиги обновляются автоматически **каждый час**. Последнее обновление: всегда свежее в файлах.

## 🔒 Защита

Для дополнительной защиты рекомендуется использовать Cloudflare Worker с проверкой User-Agent (только для Happ, v2ray и т.д.).

## 📝 Лицензия

MIT
