# crypto-listing-bot

Telegram-бот, который присылает в личные сообщения текстовые объявления о предстоящих листингах с Binance, OKX, Bybit, Bitget, Gate и MEXC.

## Как устроено

- `listing_bot` (Python 3.11, aiogram 3): Telegram-бот и HTTP API.
  - `POST /api/collect` — забирает ленты объявлений о листингах со всех бирж, отбрасывает уже известные, для новых загружает текст объявления и вытаскивает тикеры и время листинга. Возвращает только новые объявления.
  - `POST /api/broadcast` — рассылает одно объявление всем подписчикам бота.
  - `GET /api/latest` — последние сохранённые объявления.
  - Все `/api/*` требуют заголовок `X-Api-Token`.
- `n8n` — расписание и оркестрация: раз в 5 минут вызывает `/api/collect`, разбивает результат на отдельные объявления и для каждого вызывает `/api/broadcast`. Workflow лежит в `n8n/workflows/listings.json`, импортируется и включается автоматически при старте контейнера.
- SQLite (`data/listings.db`) хранит подписчиков и уже отправленные объявления.

При первом опросе каждой биржи текущие объявления только сохраняются, без рассылки. Дальше приходят лишь новые.

Источники:

| Биржа | Источник |
|---|---|
| Binance | CMS API, раздел New Cryptocurrency Listing |
| OKX | `/api/v5/support/announcements`, тип `announcements-new-listings` |
| Bybit | `/v5/announcements/index`, тип `new_crypto` |
| Bitget | `/api/v2/public/annoucements`, тип `coin_listings` |
| Gate | HTML-страница `gate.com/en/announcements/newlisted` |
| MEXC | HTML-страница `mexc.com/announcements/new-listings` |

Запросы к биржам идут через `curl_cffi` с отпечатком Chrome, иначе Gate и MEXC отвечают 403.

## Команды бота

- `/start` — подписаться
- `/stop` — отписаться
- `/latest` — 5 последних объявлений
- `/status` — статус подписки

## Запуск через Docker

1. Создать бота у [@BotFather](https://t.me/BotFather) и получить токен.
2. Скопировать конфиг и заполнить `BOT_TOKEN` и `API_TOKEN`:
   ```bash
   cp .env.example .env
   ```
3. Запустить:
   ```bash
   docker compose up -d --build
   ```
4. Написать боту `/start`.

Интерфейс n8n: http://localhost:5678 (при первом входе нужно создать владельца). Интервал опроса меняется в узле `Every 5 minutes`.

## Запуск без Docker

Нужны Python 3.11 и Node.js 18+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m listing_bot
```

В другом терминале:

```bash
export APP_URL=http://127.0.0.1:8080 API_TOKEN=<тот же, что в .env> N8N_BLOCK_ENV_ACCESS_IN_NODE=false
npx n8n@1.64.0 import:workflow --input=n8n/workflows/listings.json
npx n8n@1.64.0 update:workflow --id=cryptoListings01 --active=true
npx n8n@1.64.0 start
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | токен Telegram-бота |
| `API_TOKEN` | секрет для запросов n8n к API бота |
| `ALLOWED_USER_IDS` | Telegram ID через запятую, кому разрешена подписка; пусто — всем |
| `API_HOST`, `API_PORT` | адрес HTTP API |
| `DB_PATH` | путь к SQLite |
| `REQUEST_TIMEOUT` | таймаут запросов к биржам, сек |
| `HTTP_PROXY_URL` | прокси для запросов к биржам, если они недоступны из вашего региона |
