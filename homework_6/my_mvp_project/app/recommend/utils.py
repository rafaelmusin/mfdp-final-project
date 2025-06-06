# app/recommend/utils.py

import pickle
from pathlib import Path

_MODEL_PATH = Path(__file__).parent / "model.pkl"


def load_model():
    """
    Пытаемся загрузить сериализованный CatBoost (или любую другую) модель.
    Если файла нет — кидаем FileNotFoundError, и роут отдаст 503.
    """
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(f"Модель не найдена по пути {_MODEL_PATH}")
    with open(_MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model
