"""Скрипт для заполнения базы данных данными из CSV файлов.

Загружает:
- Категории товаров
- Пользователей и товары
- Свойства товаров  
- События пользователей

Использование:
    python scripts/populate_db.py
"""

import csv
import os
import sys
import time
from pathlib import Path
import pandas as pd

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.models import Category, Event, Item, ItemProperty, User

BATCH_SIZE = 5000

# Пути к файлам данных
DATA_DIR = os.getenv("DATA_DIR", "data")
CATEGORY_FILE = os.getenv("CATEGORY_FILE", f"{DATA_DIR}/category_tree.csv")
EVENTS_FILE = os.getenv("EVENTS_FILE", f"{DATA_DIR}/events.csv")
ITEM_PROPS_FILE1 = os.getenv(
    "ITEM_PROPS_FILE1", f"{DATA_DIR}/item_properties_part1.csv"
)
ITEM_PROPS_FILE2 = os.getenv(
    "ITEM_PROPS_FILE2", f"{DATA_DIR}/item_properties_part2.csv"
)


def create_schema_with_retry(retries: int = 5, delay: int = 2):
    """Создание схемы базы данных с повторными попытками."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
            print("[populate_db] Схема базы данных готова.")
            return
        except OperationalError:
            print(
                f"[populate_db] База данных не готова (попытка {attempt}/{retries}), повтор через {delay} сек..."
            )
            time.sleep(delay)
    raise Exception("[populate_db] Не удалось создать схему базы данных!")


def load_categories(session: Session, path_csv: str, use_test_split: bool = True):
    """Загрузка категорий из CSV файла."""
    if session.query(Category).first() is not None:
        print("[populate_db] Таблица 'categories' уже заполнена, пропуск.")
        return

    print(f"[populate_db] Загрузка категорий из: {path_csv}")
    roots = []
    children = []

    # Читаем CSV файл
    all_categories = []
    with open(path_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat_id = int(row["categoryid"])
            parent = row.get("parentid")
            parent_id = int(parent) if parent and parent.strip() else None
            all_categories.append((cat_id, parent_id))
    
    if use_test_split:
        # Полноценный режим - загружаем все категории
        print(f"[populate_db] Полноценная загрузка всех {len(all_categories)} категорий...")
        selected_categories = set()
        
        # Добавляем все категории
        for cat_id, parent_id in all_categories:
            selected_categories.add(cat_id)
    else:
        # Демо-режим - ограничиваем количество категорий для тестирования
        roots_from_all = [cat_id for cat_id, parent_id in all_categories if parent_id is None]
        limited_roots = roots_from_all[:5]  # Берем 5 корневых категорий
        
        # Добавляем дочерние категории
        selected_categories = set(limited_roots)
        children_level1 = [(cat_id, parent_id) for cat_id, parent_id in all_categories 
                           if parent_id in limited_roots]
        
        for cat_id, parent_id in children_level1[:5]:  # Ограничиваем дочерние
            selected_categories.add(cat_id)
    
    # Формируем списки для загрузки
    for cat_id, parent_id in all_categories:
        if cat_id in selected_categories:
            if parent_id is None:
                roots.append(cat_id)
            elif parent_id in selected_categories:
                children.append((cat_id, parent_id))

    # Загружаем корневые категории
    for cid in roots:
        session.merge(Category(id=cid, parent_id=None, name=f"Category {cid}"))
    session.commit()
    print(f"[populate_db]  → Корневые категории вставлены (count={len(roots)})")

    # Загружаем дочерние категории
    inserted_ids = set(roots)
    remaining = children.copy()
    round_num = 1

    while remaining:
        inserted_this_round = []
        next_remaining = []

        for cid, pid in remaining:
            if pid in inserted_ids:
                session.merge(Category(id=cid, parent_id=pid, name=f"Category {cid}"))
                inserted_this_round.append(cid)
            else:
                next_remaining.append((cid, pid))

        if not inserted_this_round:
            raise RuntimeError(
                "[populate_db] Ошибка при загрузке категорий: обнаружены категории с отсутствующими родителями."
            )

        session.commit()
        inserted_ids.update(inserted_this_round)
        remaining = next_remaining
        print(
            f"[populate_db]  → Рунд {round_num}: вставлено = {len(inserted_this_round)}, "
            f"осталось = {len(remaining)}"
        )
        round_num += 1

    print(f"[populate_db] Категории загружены полностью. Всего: {len(inserted_ids)}")


def check_files_exist(files: list[str]):
    """Проверка наличия файлов данных."""
    missing_files = []
    for file_path in files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        raise FileNotFoundError(f"Отсутствуют файлы: {', '.join(missing_files)}")


def load_items_and_users(session: Session, unique_visitors: set, unique_items: set, use_test_split: bool = True):
    """Загружает пользователей и товары в базу данных."""
    if session.query(User).first() is not None:
        print("[populate_db] Таблица 'users' уже заполнена, пропуск.")
    else:
        if use_test_split:
            # Загружаем всех пользователей из тестового набора
            limited_visitors = list(unique_visitors)
        else:
            # Ограничиваем до 10 пользователей для демо
            limited_visitors = list(unique_visitors)[:10]
        
        print(f"[populate_db] Загрузка {len(limited_visitors)} пользователей...")
        user_batch = []
        for vid in limited_visitors:
            user_batch.append({"id": vid})
            if len(user_batch) >= BATCH_SIZE:
                session.bulk_insert_mappings(User, user_batch)
                session.commit()
                user_batch.clear()
        if user_batch:
            session.bulk_insert_mappings(User, user_batch)
            session.commit()
        print("[populate_db]  → Пользователи загружены.")

    if session.query(Item).first() is not None:
        print("[populate_db] Таблица 'items' уже заполнена, пропуск.")
    else:
        if use_test_split:
            # Загружаем все товары из тестового набора
            limited_items = list(unique_items)
        else:
            # Ограничиваем до 10 товаров для демо
            limited_items = list(unique_items)[:10]
        
        print(f"[populate_db] Загрузка {len(limited_items)} товаров...")
        
        item_batch = []
        for iid in limited_items:
            item_batch.append({"id": iid})
            if len(item_batch) >= BATCH_SIZE:
                session.bulk_insert_mappings(Item, item_batch)
                session.commit()
                item_batch.clear()
        if item_batch:
            session.bulk_insert_mappings(Item, item_batch)
            session.commit()
        print("[populate_db]  → Товары загружены.")


def collect_unique_ids(events_csv: str, item_props_csvs: list[str], use_test_split: bool = True) -> tuple[set, set]:
    """Собирает уникальные ID пользователей и товаров из CSV файлов."""
    print(f"[populate_db] Сбор уникальных товаров и пользователей из CSV файлов (test_split={use_test_split})...")

    if use_test_split:
        # Загружаем события и применяем разделение
        print("[populate_db] Загрузка событий для разделения на train/test...")
        events_df = pd.read_csv(events_csv)
        
        # Применяем разделение как при обучении модели
        train_events, test_events = train_test_split_events(events_df, test_size=1)
        
        print(f"[populate_db] train_events: {train_events.shape}")
        print(f"[populate_db] test_events: {test_events.shape}")
        print(f"[populate_db] уникальных пользователей в test: {test_events['visitorid'].nunique()}")
        
        # Берем всех пользователей и товары из тестового набора
        # Конвертируем numpy.int64 в обычные int для совместимости с PostgreSQL
        unique_visitors = set(int(x) for x in test_events['visitorid'].unique())
        unique_items = set(int(x) for x in test_events['itemid'].unique())
        
        print(f"[populate_db] Из test набора: {len(unique_visitors)} пользователей, {len(unique_items)} товаров")
        
    else:
        # Старая логика - берем первые 10 
        unique_visitors = []
        unique_items = []

        with open(events_csv, newline="", encoding="utf-8") as fe:
            reader = csv.DictReader(fe)
            visitors_seen = set()
            items_seen = set()
            
            for row in reader:
                vid = row.get("visitorid")
                iid = row.get("itemid")
                
                if vid and vid.strip() and int(vid) not in visitors_seen and len(unique_visitors) < 10:
                    unique_visitors.append(int(vid))
                    visitors_seen.add(int(vid))
                    
                if iid and iid.strip() and int(iid) not in items_seen and len(unique_items) < 10:
                    unique_items.append(int(iid))
                    items_seen.add(int(iid))
                    
                if len(unique_visitors) >= 10 and len(unique_items) >= 10:
                    break

        unique_visitors = set(unique_visitors)
        unique_items = set(unique_items)

    return unique_visitors, unique_items


def load_item_properties(session: Session, paths: list[str]):
    """Загружает свойства товаров из CSV файлов."""
    if session.query(ItemProperty).first() is not None:
        print("[populate_db] Таблица 'item_properties' уже заполнена, пропуск.")
        return

    # Получаем ID всех товаров, которые уже есть в базе
    existing_item_ids = set(row[0] for row in session.query(Item.id).all())
    print(f"[populate_db] Найдено {len(existing_item_ids)} товаров в базе для загрузки свойств")

    print(f"[populate_db] Загрузка свойств товаров из файлов: {paths}")
    total_inserted = 0

    count = 0
    for path in paths:
        batch = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Убираем ограничение - ищем свойства по всему файлу
                ts = row.get("timestamp")
                iid = row.get("itemid")
                prop = row.get("property")
                val = row.get("value")
                
                if ts and iid and prop is not None and val is not None:
                    item_id = int(iid)
                    # Загружаем только если товар существует в базе
                    if item_id in existing_item_ids:
                        mapping = {
                            "timestamp": int(ts),
                            "item_id": item_id,
                            "property": prop,
                            "value": val,
                        }
                        batch.append(mapping)
                count += 1

                if len(batch) >= BATCH_SIZE:
                    session.bulk_insert_mappings(ItemProperty, batch)
                    session.commit()
                    total_inserted += len(batch)
                    batch.clear()

        if batch:
            session.bulk_insert_mappings(ItemProperty, batch)
            session.commit()
            total_inserted += len(batch)
            batch.clear()

    print(f"[populate_db]  → Загружено {total_inserted} строк item_properties.")


def load_events(session: Session, path_csv: str, use_test_split: bool = True):
    """Загружает события из CSV файла."""
    if session.query(Event).first() is not None:
        print("[populate_db] Таблица 'events' уже заполнена, пропуск.")
        return

    # Получаем ID всех пользователей и товаров, которые уже есть в базе
    existing_user_ids = set(row[0] for row in session.query(User.id).all())
    existing_item_ids = set(row[0] for row in session.query(Item.id).all())
    print(f"[populate_db] Найдено {len(existing_user_ids)} пользователей и {len(existing_item_ids)} товаров в базе для загрузки событий")

    if use_test_split:
        # Загружаем ограниченное количество событий каждого пользователя из тестового набора
        print("[populate_db] Загрузка последних 5 событий каждого пользователя из тестового набора...")
        events_df = pd.read_csv(path_csv)
        
        # Получаем пользователей из тестового набора (которые уже загружены в базу)
        test_user_ids = existing_user_ids
        
        # Фильтруем события: берем события пользователей, которые есть в базе
        user_events = events_df[events_df['visitorid'].isin(test_user_ids)]
        
        # Сортируем по времени и берем последние 5 событий каждого пользователя
        user_events = user_events.sort_values('timestamp').groupby('visitorid').tail(5).reset_index(drop=True)
        
        print(f"[populate_db] Найдено {len(user_events)} событий для {len(test_user_ids)} пользователей (по 5 событий на пользователя)")
        
        # Загружаем события
        total_inserted = 0
        batch = []
        
        for _, row in user_events.iterrows():
            user_id = int(row['visitorid'])
            item_id = int(row['itemid'])
            
            # Загружаем только если пользователь и товар существуют в базе
            if user_id in existing_user_ids and item_id in existing_item_ids:
                mapping = {
                    "timestamp": int(row['timestamp']),
                    "user_id": user_id,
                    "item_id": item_id,
                    "event_type": row['event'],
                    "transaction_id": row['transactionid'] if pd.notna(row['transactionid']) and str(row['transactionid']).strip() else None,
                }
                batch.append(mapping)

                if len(batch) >= BATCH_SIZE:
                    session.bulk_insert_mappings(Event, batch)
                    session.commit()
                    total_inserted += len(batch)
                    print(f"[populate_db]  → Загружено {total_inserted} событий...")
                    batch.clear()

        if batch:
            session.bulk_insert_mappings(Event, batch)
            session.commit()
            total_inserted += len(batch)
            batch.clear()
            
    else:
        # Старая логика - загрузка всех событий с лимитом
        print(f"[populate_db] Загрузка событий из: {path_csv}")
        total_inserted = 0
        batch = []

        with open(path_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if count >= 10000:
                    break
                ts = row.get("timestamp")
                vid = row.get("visitorid")
                iid = row.get("itemid")
                ev = row.get("event")
                tx = row.get("transactionid")

                if ts and vid and iid and ev:
                    user_id = int(vid)
                    item_id = int(iid)
                    if user_id in existing_user_ids and item_id in existing_item_ids:
                        mapping = {
                            "timestamp": int(ts),
                            "user_id": user_id,
                            "item_id": item_id,
                            "event_type": ev,
                            "transaction_id": tx.strip() if tx and tx.strip() else None,
                        }
                        batch.append(mapping)
                count += 1

                if len(batch) >= BATCH_SIZE:
                    session.bulk_insert_mappings(Event, batch)
                    session.commit()
                    total_inserted += len(batch)
                    print(f"[populate_db]  → Загружено {total_inserted} строк...")
                    batch.clear()

        if batch:
            session.bulk_insert_mappings(Event, batch)
            session.commit()
            total_inserted += len(batch)
            batch.clear()

    print(f"[populate_db]  → Загружено {total_inserted} событий.")


def update_sequences(session: Session):
    """Обновляет последовательности в базе данных."""
    print("[populate_db] Обновление sequence для таблиц...")
    tables = ["users", "items", "categories"]
    for table in tables:
        try:
            # Находим максимальный ID в таблице
            max_id = session.execute(text(f"SELECT MAX(id) FROM {table}")).scalar()
            if max_id is not None:
                # Устанавливаем sequence в значение > max_id
                query = text(f"SELECT setval('{table}_id_seq', {max_id}, true)")
                session.execute(query)
                print(
                    f"[populate_db]  → Sequence для таблицы '{table}' обновлен до {max_id}."
                )
        except Exception as e:
            # Может возникнуть ошибка, если таблица пуста или sequence не существует
            print(f"[populate_db]  → Не удалось обновить sequence для '{table}': {e}")
    session.commit()
    print("[populate_db] Обновление sequence завершено.")


def train_test_split_events(events, test_size=1):
    """Разделяет данные на train и test по последней покупке каждого пользователя."""
    test_indices = events[events['event'] == 'transaction'].groupby('visitorid').tail(test_size).index
    test_events = events.loc[test_indices]
    train_events = events.drop(test_indices)
    return train_events, test_events


def main():
    """Основная функция скрипта загрузки данных."""
    # Проверка наличия файлов данных
    item_prop_files = [ITEM_PROPS_FILE1, ITEM_PROPS_FILE2]
    check_files_exist([CATEGORY_FILE, EVENTS_FILE] + item_prop_files)

    # Используем тестовый набор для честной оценки модели
    use_test_split = True
    print(f"[populate_db] Начало загрузки данных (test_split={use_test_split})...")
    session = SessionLocal()
    try:
        create_schema_with_retry()
        load_categories(session, CATEGORY_FILE, use_test_split=use_test_split)

        # Сначала собираем все ID из тестового набора
        unique_visitors, unique_items = collect_unique_ids(EVENTS_FILE, item_prop_files, use_test_split=use_test_split)

        # Загружаем пользователей и товары
        load_items_and_users(session, unique_visitors, unique_items, use_test_split=use_test_split)

        # Загружаем остальные данные
        load_item_properties(session, item_prop_files)
        load_events(session, EVENTS_FILE, use_test_split=use_test_split)

        # Обновляем последовательности
        update_sequences(session)

        print("[populate_db] === Все данные из тестового набора успешно импортированы! ===")
    except Exception as e:
        print(f"[populate_db] Ошибка: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
