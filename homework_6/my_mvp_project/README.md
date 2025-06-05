# RetailRocket MVP (FastAPI + PostgreSQL + Docker)

**Описание:**  
Минимально жизнеспособный продукт (MVP) для хранения и доступа к данным RetailRocket (Users, Items, Categories, ItemProperties, Events).  
Реализован на FastAPI, SQLAlchemy, PostgreSQL, Docker.

---

## Структура проекта
```
my_mvp_project/
│
├── app/
│   ├── init.py
│   ├── database.py        # Настройка SQLAlchemy engine, Base, SessionLocal
│   ├── models.py          # SQLAlchemy ORM-модели: User, Item, Category, ItemProperty, Event
│   ├── schemas.py         # Pydantic-схемы для валидации (Create/Read)
│   ├── routers/
│   │   ├── init.py
│   │   ├── users.py       # CRUD для Users
│   │   ├── items.py       # CRUD для Items
│   │   ├── categories.py  # CRUD для Categories
│   │   ├── item_properties.py  # CRUD для ItemProperties
│   │   └── events.py      # CRUD для Events
│   ├── main.py            # Точка входа: запуск FastAPI, подключение роутеров, init_db
│   └── static/
│       └── index.html     # Минимальный UI (HTML+JS)
│
├── scripts/
│   └── init_db.py         # Скрипт для инициализации базы с retry
│
├── notebooks/
│   └── model_training.ipynb  # Jupyter Notebook с моделью рекомендаций (например, LightFM/CatBoost)
│
├── docker-compose.yml     # Описание сервисов (Postgres + FastAPI)
├── Dockerfile             # Dockerfile для сборки образа FastAPI-приложения
├── requirements.txt       # Зависимости Python
├── README.md              # Этот файл
└── pytest.ini             # (опционально) конфигурация pytest, если нужна
```

---

## Запуск через Docker

1. Убедитесь, что установлен Docker и Docker Compose.
2. Выполните в корне проекта:

   ```bash
   docker-compose up --build
   ```
    Это создаст два контейнера:
    •	db — PostgreSQL (порт 5432).
    •	app — FastAPI-приложение (порт 8000).

3.	В первые секунды сервис app будет ждать готовности БД, а затем автоматически выполнит Base.metadata.create_all(...), создав все таблицы.



