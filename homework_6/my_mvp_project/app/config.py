# app/config.py

import os

# 1) URL для подключения к базе
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "ERROR: переменная окружения DATABASE_URL не задана. "
        "В .env должно быть что-то вроде: DATABASE_URL=postgresql://user:pass@host:port/dbname"
    )

# 2) Путь к файлу модели рекомендаций (можно переопределить через ENV)
model_path = os.getenv("MODEL_PATH", "app/recommend/models/model.pkl")

# 3) Флаг режима разработки (True/False), читаем из ENV, по умолчанию True
_dev_mode = os.getenv("DEV_MODE", "true").lower()
dev_mode = _dev_mode in ("1", "true", "yes", "y")
