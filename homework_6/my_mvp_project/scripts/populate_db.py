# scripts/populate_db.py

import os
import csv
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import Category, ItemProperty, Item, User, Event

BATCH_SIZE = 10000  # размер пакета для bulk-вставок


def create_schema_with_retry(retries: int = 5, delay: int = 2):
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
            print("[populate_db] Схема базы готова.")
            return
        except OperationalError:
            print(f"[populate_db] DB не готова (попытка {attempt}/{retries}), через {delay} сек...")
            time.sleep(delay)
    raise Exception("[populate_db] Не удалось создать схему БД!")


def load_categories(session: Session, path_csv: str):
    """
    Загружаем категории по уровням:
    1) Сначала читаем все строки, разделяя на "roots" (parent_id пусто) и "children" (parent_id != пусто).
    2) Вставляем сразу все корневые (parent_id=None).
    3) Затем итеративно: каждый проход берем из оставшихся тех, у кого parent_id уже есть в БД,
       вставляем их (merge), фиксируем и добавляем в множество inserted_ids.
    4) Повторяем до тех пор, пока не вставим всех.
    """

    print(f"[populate_db] Загрузка категорий из: {path_csv}")
    roots = []
    children = []

    # Шаг 1: читаем CSV и разделяем корневые/дочерние
    with open(path_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat_id = int(row["categoryid"])
            parent = row.get("parentid")
            if parent is None or parent.strip() == "":
                roots.append(cat_id)
            else:
                children.append((int(row["categoryid"]), int(parent)))

    # Шаг 2: вставляем корневые (parent_id = None)
    for cid in roots:
        session.merge(Category(id=cid, parent_id=None))
    session.commit()
    print(f"[populate_db]  → Корневые категории вставлены (count={len(roots)})")

    # Шаг 3: итеративно вставляем уровень за уровнем
    inserted_ids = set(roots)
    remaining = children.copy()
    round_num = 1

    while remaining:
        inserted_this_round = []
        next_remaining = []

        for cid, pid in remaining:
            if pid in inserted_ids:
                # Родитель уже вставлен — можно вставлять эту категорию
                session.merge(Category(id=cid, parent_id=pid))
                inserted_this_round.append(cid)
            else:
                # Родитель еще не вставлен — отложим до следующего прохода
                next_remaining.append((cid, pid))

        if not inserted_this_round:
            # Если не удалось вставить ни одной категории за проход,
            # значит есть «висящие» связи (циклические или неверные parent_id)
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

    print("[populate_db] Категории загружены полностью.")


def load_items_and_users(session: Session, events_csv: str, item_props_csvs: list[str]):
    print("[populate_db] Сбор уникальных items и users …")

    unique_visitors = set()
    unique_items_from_events = set()

    # 1) Сканируем events.csv
    with open(events_csv, newline="", encoding="utf-8") as fe:
        reader = csv.DictReader(fe)
        for row in reader:
            vid = row.get("visitorid")
            iid = row.get("itemid")
            if vid and vid.strip():
                unique_visitors.add(int(vid))
            if iid and iid.strip():
                unique_items_from_events.add(int(iid))

    # 2) Сканируем item_properties CSVs
    unique_items_from_props = set()
    for path in item_props_csvs:
        with open(path, newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                iid = row.get("itemid")
                if iid and iid.strip():
                    unique_items_from_props.add(int(iid))

    unique_itemids = unique_items_from_events.union(unique_items_from_props)

    # Вставляем пользователей батчами
    users_to_insert = []
    count = 0
    for uid in unique_visitors:
        users_to_insert.append({"id": uid})
        count += 1
        if count % BATCH_SIZE == 0:
            session.bulk_insert_mappings(User, users_to_insert)
            session.commit()
            users_to_insert.clear()
    if users_to_insert:
        session.bulk_insert_mappings(User, users_to_insert)
        session.commit()
    print(f"[populate_db]  → Создано/обновлено пользователей: {len(unique_visitors)}")

    # Вставляем товары батчами
    items_to_insert = []
    count = 0
    for iid in unique_itemids:
        items_to_insert.append({"id": iid})
        count += 1
        if count % BATCH_SIZE == 0:
            session.bulk_insert_mappings(Item, items_to_insert)
            session.commit()
            items_to_insert.clear()
    if items_to_insert:
        session.bulk_insert_mappings(Item, items_to_insert)
        session.commit()
    print(f"[populate_db]  → Создано/обновлено товаров: {len(unique_itemids)}")


def load_item_properties(session: Session, paths: list[str]):
    print(f"[populate_db] Загрузка свойств товаров из: {paths}")
    total_inserted = 0

    for path in paths:
        batch = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = row.get("timestamp")
                iid = row.get("itemid")
                prop = row.get("property")
                val = row.get("value")
                if ts and iid and prop is not None and val is not None:
                    mapping = {
                        "timestamp": int(ts),
                        "item_id": int(iid),
                        "property": prop,
                        "value": val,
                        }
                    batch.append(mapping)

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


def load_events(session: Session, path_csv: str):
    print(f"[populate_db] Загрузка событий из: {path_csv}")
    batch = []
    total_events = 0

    with open(path_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row.get("timestamp")
            vid = row.get("visitorid")
            iid = row.get("itemid")
            ev = row.get("event")
            tx = row.get("transactionid")

            if ts and vid and iid and ev:
                mapping = {
                    "timestamp": int(ts),
                    "user_id": int(vid),
                    "item_id": int(iid),
                    "event": ev,
                    "transaction_id": tx.strip() if tx and tx.strip() else None,
                    }
                batch.append(mapping)

            if len(batch) >= BATCH_SIZE:
                session.bulk_insert_mappings(Event, batch)
                session.commit()
                total_events += len(batch)
                batch.clear()

    if batch:
        session.bulk_insert_mappings(Event, batch)
        session.commit()
        total_events += len(batch)
        batch.clear()

    print(f"[populate_db]  → Загружено {total_events} событий.")


def main():
    create_schema_with_retry()

    session = SessionLocal()
    try:
        load_categories(session, path_csv="data/category_tree.csv")

        load_items_and_users(
            session,
            events_csv="data/events.csv",
            item_props_csvs=["data/item_properties_part1.csv", "data/item_properties_part2.csv"],
            )

        load_item_properties(
            session,
            paths=["data/item_properties_part1.csv", "data/item_properties_part2.csv"],
            )

        load_events(session, path_csv="data/events.csv")

        print("[populate_db] === Все данные импортированы! ===")
    finally:
        session.close()


if __name__ == "__main__":
    print("[populate_db] === НАЧАЛО СКРИПТА ===")
    print("[populate_db] запускаю main()…")
    main()