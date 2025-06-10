# Docker образ для приложения рекомендаций

# Установка зависимостей
FROM python:3.11-slim AS builder

# Рабочая папка
WORKDIR /app

# Установка библиотек
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Копирование библиотек
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копирование кода
COPY app/ ./app/
COPY scripts/ ./scripts/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]