# app/limiter.py
"""Модуль для ограничения количества запросов к API.

Этот модуль предоставляет механизм rate limiting для защиты API от перегрузки.
Используется библиотека slowapi для реализации ограничений на количество запросов.

Основные особенности:
- Ограничения применяются на основе IP-адреса клиента
- Настраиваются индивидуально для каждого эндпоинта
- Поддерживают различные временные интервалы (минуты, часы, дни)
- Имеют гибкую конфигурацию лимитов

Пример использования:
    @router.get("/endpoint")
    @limiter.limit("100/minute")
    def endpoint():
        return {"message": "Hello World"}
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Создаем единый экземпляр Limiter для всего приложения
limiter = Limiter(key_func=get_remote_address)
