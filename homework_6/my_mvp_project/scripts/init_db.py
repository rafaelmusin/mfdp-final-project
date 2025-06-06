# scripts/init_db.py

import time
import os
from sqlalchemy.exc import OperationalError

# Чтобы импортировать Base и engine, путь должен быть доступным
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base


def init_db_with_retry(retries=10, delay=3):
    """
    Пробуем подключиться к базе и создать все таблицы.
    Если БД ещё не готова, ждём `delay` секунд и повторяем `retries` раз.
    """
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created (or already exist).")
            return
        except OperationalError:
            print(
                f"[Attempt {attempt}/{retries}] DB not ready, retrying in {delay} sec..."
            )
            time.sleep(delay)
    raise Exception("Could not initialize the database after multiple retries.")


if __name__ == "__main__":
    init_db_with_retry()
