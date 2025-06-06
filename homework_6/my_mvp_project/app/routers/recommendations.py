# app/routers/recommendations.py

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.recommendations import compute_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Логгер для рекомендаций (можно настроить при желании)
logger = logging.getLogger("recommendations_router")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s [recommendations] %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


@router.get("/{user_id}", response_model=List[schemas.RecommendationResponse])
def recommend_for_user(
    user_id: int,
    top_k: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    1) Вызывает сервис compute_recommendations.
    2) Если пользователя нет — возвращает 404.
    3) Если модель не готова — возвращает 503.
    4) Если внутри сервиса упала ошибка предсказания — возвращает 500.
    """
    logger.info(f"Получен запрос /recommendations/{user_id}?top_k={top_k}")
    try:
        return compute_recommendations(db, user_id, top_k)
    except ValueError as e:
        # Сервис бросает ValueError("User not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        msg = str(e)
        if "not ready" in msg:
            # Сервис бросает RuntimeError("Recommendation model is not ready")
            logger.warning(f"Модель не готова: {msg}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg
            )
        else:
            # Внутренняя ошибка предсказания
            logger.error(f"Ошибка предсказания: {msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
            )
