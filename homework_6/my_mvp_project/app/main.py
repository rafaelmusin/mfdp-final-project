# app/main.py

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .routers import users, items, categories, item_properties, events, recommendations

app = FastAPI(
    title="RetailRocket MVP API",
    description="Минимально жизнеспособный сервис для хранения и доступа к данным RetailRocket",
    version="1.0.0",
)

# Монтируем статику (index.html лежит в app/static)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def on_startup():
    """
    1) При старте приложения ждём готовности БД и создаём таблицы.
    """
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
    """
    1) Возвращает наш index.html, чтобы SPA или другой фронтенд загрузился.
    2) Не появляется в Swagger (include_in_schema=False).
    """
    return FileResponse("app/static/index.html")
