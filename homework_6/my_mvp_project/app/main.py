# app/main.py

import time
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError
from .database import engine, Base
from .routers import users, items, categories, item_properties, events, recommendations

app = FastAPI(
    title="RetailRocket MVP API",
    description="Минимально жизнеспособный сервис для хранения и доступа к данным RetailRocket",
    version="1.0.0",
    )

# Монтируем статику (index.html лежит в app/static)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def init_db():
    """
    1) Ждём, пока БД станет живой.
    2) Вызываем create_all(), оборачивая в try/except — игнорируем ошибку при создании already exists.
    """
    # 1. Ожидание запуска БД
    retries = 5
    while retries > 0:
        try:
            with engine.connect():
                pass
            break
        except OperationalError:
            retries -= 1
            time.sleep(1)

    # 2. Создаём таблицы и ENUM-тип через metadata.create_all()
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables (и ENUM) созданы (если не существовали).")
    except Exception as e:
        print("Error creating tables (init_db):", e)


@app.on_event("startup")
async def on_startup():
    init_db()


# Подключаем роутеры
app.include_router(users.router)
app.include_router(items.router)
app.include_router(categories.router)
app.include_router(item_properties.router)
app.include_router(events.router)
app.include_router(recommendations.router)


# Корневой маршрут отдаёт статический index.html
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("app/static/index.html")