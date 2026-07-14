# Прокси-проверялка для Telegram

Проверяет прокси-серверы на работоспособность, используя Telegram Bot API.

## Зависимости

- Python 3.7+
- httpx
- python-dotenv

## Установка

1. Клонировать репозиторий
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

## Настройка

Установка кода как библиотеки:

```bash
python -m build
pip install .
```

## Использование

```bash
proxy-checker PROXY_LIST_URL BOT_TOKEN
```

Скрипт:
- Загружает список прокси по указанному URL
- Проверяет каждый прокси, делая запрос к Telegram API
- Выводит прогресс в консоль
- Сохраняет рабочие прокси в файл `working_proxies.txt`

**Примечание:** Замените `BOT_TOKEN` на токен вашего Telegram-бота (получить у @BotFather), а `PROXY_LIST_URL` — на прямую ссылку на файл со списком прокси (по одному в строке, формат `ip:port` или `http://ip:port`).

## Вывод

Рабочие прокси сохраняются в `working_proxies.txt` в формате:
```
http://ip:port
```
