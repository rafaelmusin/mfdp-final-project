import pickle
from pathlib import Path
from functools import lru_cache
import threading

_MODEL_PATH = Path(__file__).parent / "model.pkl"
_model_lock = threading.Lock()
_loaded_model = None


@lru_cache(maxsize=1)
def load_model():
    """
    Загрузка ML модели с кэшированием
    """
    global _loaded_model
    
    if _loaded_model is not None:
        return _loaded_model
    
    with _model_lock:
        # Повторная проверка после получения блокировки
        if _loaded_model is not None:
            return _loaded_model
            
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Модель не найдена по пути {_MODEL_PATH}")
        
        with open(_MODEL_PATH, "rb") as f:
            _loaded_model = pickle.load(f)
        
        return _loaded_model 