# Telegram Shop Mini App

Маркетплейс-витрина: любой пользователь создаёт магазин в боте, размещает товары (название + фото), а публичный каталог всех магазинов открывается в Telegram Mini App / браузере.

## Стек

| Слой | Технология |
|------|------------|
| Bot | aiogram 3.x |
| Business logic | Temporal workflows |
| API | FastAPI |
| DB | PostgreSQL |
| S3 | MinIO |
| Mini App | Next.js (App Router) |

## Архитектура бизнес-логики (Temporal)

```
CreateShopWorkflow
  └─ ensure_user_and_create_shop  → PostgreSQL (users + shops)

CreateProductWorkflow
  ├─ fetch_and_store_product_image → Telegram file → MinIO S3
  └─ save_product                  → PostgreSQL (products)
```

Публичная лента: `GET /api/products` — товары всех магазинов.

## Быстрый старт

### 1. Токен бота

1. Создай бота у [@BotFather](https://t.me/BotFather)
2. Скопируй `.env.example` → `.env`, вставь `BOT_TOKEN`
3. Для Mini App нужен **HTTPS**. Локально подними туннель:

```bash
# пример
ngrok http 3000
```

В `.env` укажи:

```env
WEBAPP_URL=https://xxxx.ngrok-free.app
```

В BotFather: `/newapp` → выбери бота → URL = тот же `WEBAPP_URL`.

### 2. Запуск

```bash
cp .env.example .env
# отредактируй BOT_TOKEN и WEBAPP_URL

docker compose up --build
```

Сервисы:

- Frontend (каталог): http://localhost:3000  
- API / docs: http://localhost:8000/docs  
- MinIO console: http://localhost:9001 (`minioadmin` / `minioadmin`)  
- Temporal UI: http://localhost:8080  

### 3. Сценарий в Telegram

1. `/start` — бот пишет «У меня есть товар» и даёт кнопку Mini App  
2. «Создать магазин» → название  
3. «Создать товар» → **одно сообщение**: фото + название в caption  
4. «Открыть каталог» — публичная лента всех магазинов в TMA  

## Локальная разработка без Docker (опционально)

Нужны поднятые Postgres, MinIO и Temporal (можно только их из compose).

```bash
# infra
docker compose up postgres minio minio-init temporal temporal-ui -d

# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # терминал 1
python -m app.temporal.worker          # терминал 2
python -m bot.main                     # терминал 3

# frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API

- `GET /api/products` — публичный каталог (лента)  
- `GET /api/shops` — список магазинов  
- `POST /api/shops` — создать магазин (через Temporal)  
- `GET /api/shops/{id}/products` — товары магазина  
- `GET /health` — healthcheck  

## Структура

```
backend/
  app/           # FastAPI + models + Temporal
  bot/           # aiogram handlers
frontend/        # Next.js каталог (TMA-ready)
docker-compose.yml
```
