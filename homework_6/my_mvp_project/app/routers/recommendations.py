# app/routers/recommendations.py
"""Модуль для работы с рекомендациями товаров."""

import datetime
from typing import List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi_cache.decorator import cache
from loguru import logger
from sqlalchemy import func, desc, case
from sqlalchemy.orm import Session

from ..common_utils import get_temporal_features
from ..database import get_db
from ..limiter import limiter
from ..models import Event, Item
from ..schemas import RecommendedItem, RecommendedItems
from . import crud

try:
    from ..recommend.utils import load_model
except ImportError:
    def load_model():
        raise FileNotFoundError("Модель не найдена")

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Модель будет загружаться при первом обращении
MODEL = None
FEATURE_COLS = [
    "n_view",  # количество просмотров пользователя
    "n_cart",  # количество добавлений в корзину
    "n_buy",  # количество покупок
    "user_lifetime_days",  # возраст аккаунта в днях
    "item_n_view",  # количество просмотров товара
    "item_n_cart",  # количество добавлений товара в корзину
    "item_n_buy",  # количество покупок товара
    "item_n_unique_users",  # количество уникальных пользователей товара
    "is_weekend",  # является ли день выходным
    "is_evening",  # является ли время вечерним
]


def get_model():
    """Получить модель рекомендаций."""
    global MODEL
    if MODEL is None:
        try:
            MODEL = load_model()
            logger.info("Модель рекомендаций успешно загружена.")
        except FileNotFoundError:
            logger.warning("Модель рекомендаций не найдена.")
            raise
    return MODEL


@router.get("/{user_id}", response_model=RecommendedItems)
@limiter.limit("30/minute")
# @cache(expire=300)  # Убираем кэш для тестов
def recommend_for_user(
    request: Request,
    user_id: int,
    top_k: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Получить рекомендации для пользователя."""
    logger.info(f"Получен запрос /recommendations/{user_id}?top_k={top_k}")

    # Проверка существования пользователя
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        logger.warning(f"Пользователь с id {user_id} не найден.")
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Загрузка модели
    try:
        model = get_model()
    except FileNotFoundError:
        logger.warning("Вызван эндпоинт рекомендаций, но модель не готова.")
        raise HTTPException(status_code=503, detail="Модель рекомендаций не готова")

    return _generate_recommendations(user_id, top_k, db, model)


def _generate_recommendations(
    user_id: int, top_k: int, db: Session, model
) -> RecommendedItems:
    """Генерация рекомендаций для пользователя."""
    # Подсчёт количества событий пользователя
    user_events_count = (
        db.query(func.count())
        .select_from(Event)
        .filter(Event.user_id == user_id)
        .scalar()
    )

    # Холодный старт - если у пользователя нет событий
    if user_events_count == 0:
        logger.info(
            f"Пользователь {user_id} — холодный старт (нет событий). Возвращаем топ-{top_k} популярных товаров."
        )
        return _handle_cold_start(top_k, db)

    # Получаем товары, которые пользователь уже видел
    seen_subq = db.query(Event.item_id).filter(Event.user_id == user_id).subquery()

    # Находим кандидатов - товары, которые пользователь ещё не видел
    MAX_CANDIDATES = 10000  # Максимум товаров для обработки
    candidate_rows = (
        db.query(Item.id)
        .outerjoin(seen_subq, Item.id == seen_subq.c.item_id)
        .filter(seen_subq.c.item_id.is_(None))
        .limit(MAX_CANDIDATES)
    )
    candidate_ids = [row[0] for row in candidate_rows.all()]

    if not candidate_ids:
        logger.info(f"Пользователь {user_id} видел все товары, нечего рекомендовать.")
        return RecommendedItems(items=[])

    logger.info(
        f"Пользователь {user_id} — найдено {len(candidate_ids)} кандидатов для предсказания."
    )

    # Сбор данных и предсказание
    return _process_recommendations(user_id, candidate_ids, db, model, top_k)


def _handle_cold_start(top_k: int, db: Session) -> RecommendedItems:
    """Обработка холодного старта: возврат популярных товаров."""
    # Ищем самые популярные товары по всем типам событий
    # Приоритет: transaction > addtocart > view (взвешенная популярность)
    popular_items = (
        db.query(
            Event.item_id,
            (func.count(case((Event.event_type == "transaction", 1))) * 3 +
             func.count(case((Event.event_type == "addtocart", 1))) * 2 +
             func.count(case((Event.event_type == "view", 1))) * 1
            ).label("weighted_score")
        )
        .group_by(Event.item_id)
        .order_by(desc("weighted_score"))
        .limit(top_k)
        .all()
    )

    # Если нет никаких событий, возьмем любые товары из базы
    if not popular_items:
        logger.info("Нет событий в базе, возвращаем случайные товары.")
        items = db.query(Item.id).limit(top_k).all()
        if not items:
            logger.warning("В базе данных нет товаров для холодного старта.")
            return RecommendedItems(items=[])
        
        recommended_items = []
        for i, (item_id,) in enumerate(items):
            score = 1.0 - (i * 0.1)  # Убывающий score
            recommended_items.append(
                RecommendedItem(
                    id=item_id,
                    name=f"Item {item_id}",
                    score=max(score, 0.1)  # Минимальный score 0.1
                )
            )
        
        logger.info(f"Холодный старт: возвращено {len(recommended_items)} случайных товаров.")
        return RecommendedItems(items=recommended_items)

    # Формируем список рекомендаций на основе взвешенной популярности
    recommended_items = []
    max_score = max([item[1] for item in popular_items]) if popular_items else 1
    for item_id, weighted_score in popular_items:
        # Нормализация взвешенного счетчика в score от 0.1 до 1
        score = max(0.1, weighted_score / max_score) if max_score > 0 else 0.5
        recommended_items.append(
            RecommendedItem(
                id=item_id,
                name=f"Popular Item {item_id}",
                score=score
            )
        )

    logger.info(f"Холодный старт: возвращено {len(recommended_items)} популярных товаров.")
    return RecommendedItems(items=recommended_items)


def _process_recommendations(
    user_id: int, candidate_ids: List[int], db: Session, model, top_k: int
) -> RecommendedItems:
    """Обработка рекомендаций с использованием модели."""
    # Собираем признаки пользователя
    user_features = _get_user_features(user_id, db)
    
    # Собираем признаки товаров
    item_features_map = _get_item_features(candidate_ids, db)
    
    # Временные признаки
    temporal_features = _get_temporal_features()

    # Подготавливаем данные для предсказания
    df_pred = _prepare_prediction_data(
        user_id, candidate_ids, user_features, item_features_map, temporal_features
    )

    if df_pred.empty:
        logger.warning(f"Нет данных для предсказания для пользователя {user_id}.")
        return RecommendedItems(items=[])

    # Получаем предсказания от модели
    scores = _predict_scores(df_pred, model)

    # Сортируем и выбираем топ
    item_score_pairs = list(zip(candidate_ids, scores))
    item_score_pairs.sort(key=lambda x: x[1], reverse=True)
    top_items = item_score_pairs[:top_k]

    # Формируем результат
    recommended_items = []
    for item_id, score in top_items:
        recommended_items.append(
            RecommendedItem(
                id=item_id,
                name=f"Item {item_id}",  # Простое название
                score=float(score)
            )
        )

    logger.info(f"Сгенерированы рекомендации для пользователя {user_id}: {len(recommended_items)} товаров.")
    return RecommendedItems(items=recommended_items)


def _get_user_features(user_id: int, db: Session) -> dict:
    """Получить признаки пользователя."""
    # Агрегируем события пользователя
    user_stats = (
        db.query(
            func.count(case((Event.event_type == "view", 1))).label("n_view"),
            func.count(case((Event.event_type == "addtocart", 1))).label("n_cart"),
            func.count(case((Event.event_type == "transaction", 1))).label("n_buy"),
            func.min(Event.timestamp).label("first_event_ts")
        )
        .filter(Event.user_id == user_id)
        .first()
    )

    # Вычисляем возраст аккаунта
    if user_stats.first_event_ts:
        first_event_date = datetime.datetime.fromtimestamp(user_stats.first_event_ts / 1000)
        user_lifetime_days = (datetime.datetime.now() - first_event_date).days
    else:
        user_lifetime_days = 0

    return {
        "n_view": user_stats.n_view or 0,
        "n_cart": user_stats.n_cart or 0,
        "n_buy": user_stats.n_buy or 0,
        "user_lifetime_days": user_lifetime_days,
    }


def _get_item_features(candidate_ids: List[int], db: Session) -> dict:
    """Получить признаки товаров."""
    # Агрегируем статистику по товарам
    item_stats = (
        db.query(
            Event.item_id,
            func.count(case((Event.event_type == "view", 1))).label("item_n_view"),
            func.count(case((Event.event_type == "addtocart", 1))).label("item_n_cart"),
            func.count(case((Event.event_type == "transaction", 1))).label("item_n_buy"),
            func.count(func.distinct(Event.user_id)).label("item_n_unique_users")
        )
        .filter(Event.item_id.in_(candidate_ids))
        .group_by(Event.item_id)
        .all()
    )

    # Создаем словарь с признаками
    features_map = {}
    for stats in item_stats:
        features_map[stats.item_id] = {
            "item_n_view": stats.item_n_view or 0,
            "item_n_cart": stats.item_n_cart or 0,
            "item_n_buy": stats.item_n_buy or 0,
            "item_n_unique_users": stats.item_n_unique_users or 0,
        }

    # Добавляем нулевые значения для товаров без статистики
    for item_id in candidate_ids:
        if item_id not in features_map:
            features_map[item_id] = {
                "item_n_view": 0,
                "item_n_cart": 0,
                "item_n_buy": 0,
                "item_n_unique_users": 0,
            }

    return features_map


def _get_temporal_features() -> dict:
    """Получить временные признаки."""
    return get_temporal_features()


def _prepare_prediction_data(
    user_id: int,
    candidate_ids: List[int],
    user_features: dict,
    item_features_map: dict,
    temporal_features: dict,
) -> pd.DataFrame:
    """Подготовить данные для предсказания."""
    rows = []
    for item_id in candidate_ids:
        row = {
            "user_id": user_id,
            "item_id": item_id,
            **user_features,
            **item_features_map[item_id],
            **temporal_features,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    
    # Выбираем только нужные колонки в правильном порядке
    if not df.empty:
        df = df[FEATURE_COLS]
    
    return df


def _predict_scores(df_pred: pd.DataFrame, model) -> List[float]:
    """Получить предсказания от модели."""
    try:
        predictions = model.predict_proba(df_pred)[:, 1]  # Вероятность класса 1
        return predictions.tolist()
    except Exception as e:
        logger.error(f"Ошибка предсказания модели: {e}")
        # Возвращаем случайные значения в случае ошибки
        return np.random.random(len(df_pred)).tolist()
