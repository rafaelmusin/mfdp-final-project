# app/routers/recommendations.py

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
import pandas as pd
import datetime

from app.database import get_db
from app.models import User, Item, Event
from app.schemas import RecommendationResponse
from app.recommend.utils import load_model

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Настроим логгер для этого модуля
logger = logging.getLogger("recommendations")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s [recommendations] %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# Попытка загрузить модель при старте приложения
try:
    MODEL = load_model()
    # Список признаков в том порядке, в котором обучалась модель
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
    logger.warning("Recommendation model не найдена, эндпоинты рекомендаций будут возвращать 503.")


@router.get("/{user_id}", response_model=List[RecommendationResponse])
def recommend_for_user(
        user_id: int,
        top_k: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        ):
    logger.info(f"Получен запрос /recommendations/{user_id}?top_k={top_k}")

    # 1) Проверяем, что пользователь существует
    user = db.query(User.id).filter(User.id == user_id).first()
    if user is None:
        logger.info(f"User {user_id} не найден.")
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Если модель не загружена — 503
    if MODEL is None:
        logger.warning("Вызван эндпоинт рекомендаций, но модель не готова.")
        raise HTTPException(status_code=503, detail="Recommendation model is not ready")

    # 3) Считаем, сколько событий (всех типов) у пользователя было вообще
    user_events_count = (
        db.query(func.count())
        .select_from(Event)
        .filter(Event.user_id == user_id)
        .scalar()
    )

    # Если у пользователя нет ни одного события — “холодный” старт: возвращаем топ-K самых популярных товаров
    if user_events_count == 0:
        logger.info(f"User {user_id} — холодный старт (нет событий). Возвращаем топ-{top_k} популярных items.")
        # Популярность: сортируем по количеству транзакций (или по количеству просмотров, как захотите)
        popular_items = (
            db.query(
                Event.item_id.label("item_id"),
                func.count().label("txn_count"),
                )
            .filter(Event.event == "transaction")
            .group_by(Event.item_id)
            .order_by(desc("txn_count"))
            .limit(top_k)
            .all()
        )
        recs: List[RecommendationResponse] = []
        for row in popular_items:
            recs.append(
                RecommendationResponse(
                    user_id=user_id,
                    item_id=int(row.item_id),
                    score=float(row.txn_count),  # в “холодном” старте score = число транзакций
                    )
                )
        return recs

    # 4) Составляем подзапрос: все item_id, которые видел(добавлял/покупал) пользователь
    seen_subq = db.query(Event.item_id).filter(Event.user_id == user_id).subquery()

    # 5) Получаем список кандидатов сразу из БД: все items, которых нет в seen_subq
    candidate_rows = db.query(Item.id).outerjoin(
        seen_subq, Item.id == seen_subq.c.item_id
        ).filter(seen_subq.c.item_id.is_(None))
    candidate_ids = [row[0] for row in candidate_rows.all()]

    if not candidate_ids:
        logger.info(f"User {user_id} видел все товары, нечего рекомендовать.")
        return []

    logger.info(f"User {user_id} — найдено {len(candidate_ids)} кандидатов для предсказания.")

    # ----------------------------------------------------------------------------------
    # 6) Собираем статистику по пользователю в целом
    #    (n_view, n_cart, n_buy, user_lifetime_days)
    # ----------------------------------------------------------------------------------

    user_agg = (
        db.query(
            func.sum(case((Event.event == "view", 1), else_=0)).label("n_view"),
            func.sum(case((Event.event == "addtocart", 1), else_=0)).label("n_cart"),
            func.sum(case((Event.event == "transaction", 1), else_=0)).label("n_buy"),
            func.min(Event.datetime).label("first_dt"),
            func.max(Event.datetime).label("last_dt"),
            )
        .filter(Event.user_id == user_id)
        .one()
    )

    # Если у пользователя вдруг нет ни одного события (маловероятно, потому что мы проверили count выше)
    if user_agg.first_dt is None or user_agg.last_dt is None:
        n_view = n_cart = n_buy = 0
        user_lifetime_days = 1
    else:
        n_view = int(user_agg.n_view or 0)
        n_cart = int(user_agg.n_cart or 0)
        n_buy = int(user_agg.n_buy or 0)
        delta = user_agg.last_dt - user_agg.first_dt
        user_lifetime_days = delta.days + 1

    # ----------------------------------------------------------------------------------
    # 7) Собираем статистику по товарам, но только для candidate_ids
    #    (item_n_view, item_n_cart, item_n_buy, item_n_unique_users)
    # ----------------------------------------------------------------------------------

    item_stats_query = (
        db.query(
            Event.item_id.label("item_id"),
            func.sum(case((Event.event == "view", 1), else_=0)).label("item_n_view"),
            func.sum(case((Event.event == "addtocart", 1), else_=0)).label("item_n_cart"),
            func.sum(case((Event.event == "transaction", 1), else_=0)).label("item_n_buy"),
            func.count(func.distinct(Event.user_id)).label("item_n_unique_users"),
            )
        .filter(Event.item_id.in_(candidate_ids))
        .group_by(Event.item_id)
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
    # Для товаров без событий по ним — все нули
    for iid in candidate_ids:
        if iid not in item_stats_map:
            item_stats_map[iid] = {
                "item_n_view": 0,
                "item_n_cart": 0,
                "item_n_buy": 0,
                "item_n_unique_users": 0,
                }

    # ----------------------------------------------------------------------------------
    # 8) Временные признаки “сейчас”
    # ----------------------------------------------------------------------------------

    now = datetime.datetime.utcnow()
    is_weekend = 1 if now.weekday() in (5, 6) else 0
    is_evening = 1 if 18 <= now.hour <= 23 else 0

    # ----------------------------------------------------------------------------------
    # 9) Формируем pandas.DataFrame для передачи в модель
    # ----------------------------------------------------------------------------------

    records = []
    for iid in candidate_ids:
        rec = {
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
            # Для формирования ответа:
            "item_id": iid,
            "user_id": user_id,
            }
        records.append(rec)

    df_pred = pd.DataFrame(records)
    X_pred = df_pred[FEATURE_COLS]

    # ----------------------------------------------------------------------------------
    # 10) Предсказание вероятностей (predict_proba[:,1])
    # ----------------------------------------------------------------------------------

    try:
        proba = MODEL.predict_proba(X_pred)[:, 1]
    except Exception as e:
        logger.error(f"Ошибка при MODEL.predict_proba: {e}")
        raise HTTPException(status_code=500, detail="Internal prediction error")

    df_pred["score"] = proba

    # ----------------------------------------------------------------------------------
    # 11) Берём топ-K по score
    # ----------------------------------------------------------------------------------

    df_top = df_pred.sort_values("score", ascending=False).head(top_k)
    recs: List[RecommendationResponse] = []
    for _, row in df_top.iterrows():
        recs.append(
            RecommendationResponse(
                user_id=int(row["user_id"]),
                item_id=int(row["item_id"]),
                score=float(row["score"]),
                )
            )

    logger.info(f"Для пользователя {user_id} сформировано {len(recs)} рекомендаций.")
    return recs