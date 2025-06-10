"""FastAPI приложение для рекомендаций товаров."""

import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, IntegrityError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .database import Base, engine, init_db as db_init_db
from .limiter import limiter
from .routers import analytics, catalog, categories, events, item_properties, items, recommendations, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация приложения."""
    logger.info("Запуск приложения...")
    await db_init_db()
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    logger.info("Сервис успешно запущен.")
    yield
    logger.info("Остановка приложения...")


app = FastAPI(
    title="RetailRocket MVP API",
    description="API для рекомендательной системы",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS настройки
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Логирование запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование HTTP запросов."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.2f}s"
    )
    
    return response

# Обработка ошибок
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Обработка ошибок валидации."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Обработка ошибок БД."""
    logger.error(f"Database integrity error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Database integrity error",
            "message": str(exc)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработка HTTP ошибок."""
    logger.warning(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка всех остальных ошибок."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc)
        }
    )

# Статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Подключение роутеров
app.include_router(users.router)
app.include_router(items.router)
app.include_router(categories.router)
app.include_router(item_properties.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)
app.include_router(catalog.router)


async def init_db():
    """Инициализация базы данных при запуске."""
    retries = 5
    logger.info("Попытка подключения к базе данных...")
    while retries > 0:
        try:
            with engine.connect():
                logger.info("Соединение с базой данных установлено.")
                break
        except OperationalError:
            retries -= 1
            logger.warning(f"Не удалось подключиться к БД. Попыток осталось: {retries}")
            await asyncio.sleep(1)

    if retries == 0:
        logger.error("Не удалось подключиться к базе данных после нескольких попыток.")
        return

    # Создание таблиц
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Таблицы базы данных успешно проверены/созданы.")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}", exc_info=True)
        raise


@app.get("/", include_in_schema=False)
@limiter.limit("100/minute")
async def root(request: Request):
    """Главная страница."""
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["System"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Проверка работоспособности сервиса."""
    try:
        # Проверяем БД
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected",
                "version": app.version,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )


@app.get("/version", tags=["System"])
@limiter.limit("100/minute")
async def get_version(request: Request):
    """Версия API."""
    return {"version": app.version, "title": app.title}


# Приложение создано выше
