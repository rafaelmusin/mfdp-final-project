# app/services/recommendations.py

import logging
import datetime
from typing import List

import pandas as pd
from sqlalchemy import func, case, desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.recommend.utils import load_model

# 1) Настройка логгера (аналогично тому, что было в роутере)
logger = logging.getLogger("recommendations_service")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s [recommendations] %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 2) Попытка загрузить модель при импорте сервиса
try:
    MODEL = load_model()
    FEATURE_COLS = [
        "n_view",
        "n_cart",
        "n_buy",
        "user_lifetime_days",
        "item_n_view",
        "item_n_cart",
        "item_n_buy",
        "item_n_unique_users",
        "is_weekend",
        "is_evening",
    ]
    logger.info("Recommendation model успешно загружена.")
except FileNotFoundError:
    MODEL = None
    FEATURE_COLS = []
    logger.warning("Recommendation model не найдена, сервис выдаёт 503.")


def compute_recommendations(
    db: Session, user_id: int, top_k: int
) -> List[schemas.RecommendationResponse]:
    # 1) Проверяем, что пользователь существует
    user = db.query(models.User.id).filter(models.User.id == user_id).first()
    if user is None:
        logger.info(f"User {user_id} не найден.")
        raise ValueError("User not found")

    # 2) Если модель не загружена — бросаем ошибку, чтобы роутер вернул 503
    if MODEL is None:
        logger.warning("Вызван сервис рекомендаций, но модель не готова.")
        raise RuntimeError("Recommendation model is not ready")

    # 3) Считаем общее число событий пользователя
    user_events_count = (
        db.query(func.count())
        .select_from(models.Event)
        .filter(models.Event.user_id == user_id)
        .scalar()
    )

    # 3.1) Холодный старт: если нет ни одного события, возвращаем топ-K по популярности
    if user_events_count == 0:
        logger.info(f"User {user_id} — холодный старт.")
        popular_items = (
            db.query(
                models.Event.item_id.label("item_id"),
                func.count().label("txn_count"),
            )
            .filter(models.Event.event == models.EventTypeEnum.transaction)
            .group_by(models.Event.item_id)
            .order_by(desc("txn_count"))
            .limit(top_k)
            .all()
        )
        recs: List[schemas.RecommendationResponse] = []
        for row in popular_items:
            recs.append(
                schemas.RecommendationResponse(
                    user_id=user_id,
                    item_id=int(row.item_id),
                    score=float(row.txn_count),
                )
            )
        return recs

    # 4) Подзапрос: все item_id, которые видел пользователь
    seen_subq = (
        db.query(models.Event.item_id)
        .filter(models.Event.user_id == user_id)
        .subquery()
    )

    # 5) Кандидаты: все items, которых нет в seen_subq
    candidate_rows = (
        db.query(models.Item.id)
        .outerjoin(seen_subq, models.Item.id == seen_subq.c.item_id)
        .filter(seen_subq.c.item_id.is_(None))
    )
    candidate_ids = [row[0] for row in candidate_rows.all()]

    if not candidate_ids:
        logger.info(f"User {user_id} видел всё, нечего рекомендовать.")
        return []

    logger.info(f"User {user_id} — найдено {len(candidate_ids)} кандидатов.")

    # 6) Статистика по пользователю:
    user_agg = (
        db.query(
            func.sum(case((models.Event.event == "view", 1), else_=0)).label("n_view"),
            func.sum(case((models.Event.event == "addtocart", 1), else_=0)).label(
                "n_cart"
            ),
            func.sum(case((models.Event.event == "transaction", 1), else_=0)).label(
                "n_buy"
            ),
            func.min(models.Event.datetime).label("first_dt"),
            func.max(models.Event.datetime).label("last_dt"),
        )
        .filter(models.Event.user_id == user_id)
        .one()
    )

    if user_agg.first_dt is None or user_agg.last_dt is None:
        n_view = n_cart = n_buy = 0
        user_lifetime_days = 1
    else:
        n_view = int(user_agg.n_view or 0)
        n_cart = int(user_agg.n_cart or 0)
        n_buy = int(user_agg.n_buy or 0)
        delta = user_agg.last_dt - user_agg.first_dt
        user_lifetime_days = delta.days + 1

    # 7) Статистика по товарам-кандидатам:
    item_stats_query = (
        db.query(
            models.Event.item_id.label("item_id"),
            func.sum(case((models.Event.event == "view", 1), else_=0)).label(
                "item_n_view"
            ),
            func.sum(case((models.Event.event == "addtocart", 1), else_=0)).label(
                "item_n_cart"
            ),
            func.sum(case((models.Event.event == "transaction", 1), else_=0)).label(
                "item_n_buy"
            ),
            func.count(func.distinct(models.Event.user_id)).label(
                "item_n_unique_users"
            ),
        )
        .filter(models.Event.item_id.in_(candidate_ids))
        .group_by(models.Event.item_id)
        .all()
    )

    item_stats_map = {
        row.item_id: {
            "item_n_view": int(row.item_n_view or 0),
            "item_n_cart": int(row.item_n_cart or 0),
            "item_n_buy": int(row.item_n_buy or 0),
            "item_n_unique_users": int(row.item_n_unique_users or 0),
        }
        for row in item_stats_query
    }
    for iid in candidate_ids:
        if iid not in item_stats_map:
            item_stats_map[iid] = {
                "item_n_view": 0,
                "item_n_cart": 0,
                "item_n_buy": 0,
                "item_n_unique_users": 0,
            }

    # 8) Временные признаки:
    now = datetime.datetime.utcnow()
    is_weekend = 1 if now.weekday() in (5, 6) else 0
    is_evening = 1 if 18 <= now.hour <= 23 else 0

    # 9) Формируем DataFrame для модели
    records = []
    for iid in candidate_ids:
        records.append(
            {
                "n_view": n_view,
                "n_cart": n_cart,
                "n_buy": n_buy,
                "user_lifetime_days": user_lifetime_days,
                "item_n_view": item_stats_map[iid]["item_n_view"],
                "item_n_cart": item_stats_map[iid]["item_n_cart"],
                "item_n_buy": item_stats_map[iid]["item_n_buy"],
                "item_n_unique_users": item_stats_map[iid]["item_n_unique_users"],
                "is_weekend": is_weekend,
                "is_evening": is_evening,
                "item_id": iid,
                "user_id": user_id,
            }
        )
    df_pred = pd.DataFrame(records)
    X_pred = df_pred[FEATURE_COLS]

    # 10) Предсказание
    try:
        proba = MODEL.predict_proba(X_pred)[:, 1]
    except Exception as e:
        logger.error(f"Ошибка при MODEL.predict_proba: {e}")
        raise RuntimeError("Internal prediction error")

    df_pred["score"] = proba

    # 11) Топ-K
    df_top = df_pred.sort_values("score", ascending=False).head(top_k)
    recs: List[schemas.RecommendationResponse] = []
    for _, row in df_top.iterrows():
        recs.append(
            schemas.RecommendationResponse(
                user_id=int(row["user_id"]),
                item_id=int(row["item_id"]),
                score=float(row["score"]),
            )
        )

    logger.info(f"Сформировано {len(recs)} рекомендаций для user {user_id}.")
    return recs
