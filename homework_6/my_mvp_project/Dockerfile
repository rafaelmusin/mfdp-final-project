# Dockerfile
FROM python:3.11-slim

# Настройки Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Копируем только зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Создаём непривилегированного пользователя и назначаем ему приложение
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Стандартная команда запуска (2 воркера)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]