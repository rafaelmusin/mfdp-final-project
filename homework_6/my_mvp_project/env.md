# Environment variables

Пример файла `.env` для проекта:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=retail
DATABASE_URL=postgresql://postgres:postgres@db:5432/retail
DEV_MODE=true
MODEL_PATH=app/recommend/model.pkl
```

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — параметры базы данных в контейнере `db`.
- `DATABASE_URL` — строка подключения приложения к БД.
- `DEV_MODE` — включает режим разработки (автоперезагрузка FastAPI).
- `MODEL_PATH` — путь к файлу модели рекомендаций (опционально).

