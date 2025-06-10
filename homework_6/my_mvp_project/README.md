# 🛒 RetailRocket MVP - Intelligent Recommendation System

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)
![Docker](https://img.shields.io/badge/Docker-compose-blue.svg)
![Tests](https://img.shields.io/badge/tests-49%2F49%20passing-brightgreen.svg)
![ML](https://img.shields.io/badge/ML-CatBoost-orange.svg)

> **Современная рекомендательная система для e-commerce с машинным обучением**
> 
> Полнофункциональный MVP с современным веб-интерфейсом, REST API и персонализированными рекомендациями товаров.

---

## 📋 Содержание

- [✨ Возможности](#-возможности)
- [🎯 Демо](#-демо)
- [🏗️ Архитектура](#️-архитектура)
- [🚀 Быстрый старт](#-быстрый-старт)
- [📊 Данные и статистика](#-данные-и-статистика)
- [🔌 API](#-api)
- [🧪 Тестирование](#-тестирование)
- [⚙️ Конфигурация](#️-конфигурация)
- [🛠️ Разработка](#️-разработка)

## ✨ Возможности

### 🎨 **Современный веб-интерфейс**
- Адаптивный дизайн с анимациями
- Интерактивная аналитическая панель
- Каталог товаров с фильтрацией
- Получение персонализированных рекомендаций

### 🤖 **Машинное обучение**
- Модель CatBoost для предсказания предпочтений
- Обработка холодного старта для новых пользователей
- Персонализированные рекомендации на основе истории

### 📈 **Аналитика и мониторинг**
- Системная статистика в реальном времени
- Отслеживание популярных товаров
- Анализ активности пользователей
- Мониторинг производительности API

### 🔗 **REST API**
- Полное CRUD API для всех сущностей
- OpenAPI/Swagger документация
- Валидация данных с Pydantic
- Rate limiting и кэширование

## 🎯 Демо

### Статистика системы
```
👥 11,722 пользователя
🛍️ 7,571 товар
⚡ 39,739 событий (~3.4 на пользователя)
📁 1,669 категорий
🏷️ 542,849 свойств товаров
```

### Качество рекомендаций
- **Пользователи с историей**: Score 0.77-0.79
- **Холодный старт**: Score до 1.0
- **49/49 тестов** проходят успешно

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI App   │    │   PostgreSQL    │
│                 │◄──►│                 │◄──►│                 │
│ • Analytics     │    │ • REST API      │    │ • Users         │
│ • Catalog       │    │ • ML Model      │    │ • Items         │
│ • Recommendations│   │ • Business Logic│    │ • Events        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌─────────────────┐
                       │   CatBoost ML   │
                       │                 │
                       │ • User Features │
                       │ • Item Features │
                       │ • Predictions   │
                       └─────────────────┘
```

### Технологический стек

**Backend:**
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **Pydantic** - валидация данных
- **CatBoost** - модель машинного обучения

**Frontend:**
- **HTML5/CSS3** - семантическая верстка
- **JavaScript (ES6+)** - интерактивность
- **CSS Grid/Flexbox** - адаптивный дизайн

**Infrastructure:**
- **PostgreSQL 15** - основная база данных
- **Docker Compose** - контейнеризация
- **Pytest** - тестирование

## 🚀 Быстрый старт

### Предварительные требования

- **Docker** 20.10+ и **Docker Compose** v2+
- **4 GB RAM** свободной памяти
- **2 GB** свободного места на диске

### Установка и запуск

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd my_mvp_project
   ```

2. **Создание переменных окружения**
   ```bash
   # Создайте .env файл со следующими переменными:
   cat > .env << EOF
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=recommendation_db
   DATABASE_URL=postgresql://postgres:postgres@db:5432/recommendation_db
   DEV_MODE=true
   EOF
   ```

3. **Запуск системы**
   ```bash
   docker compose up --build
   ```

4. **Заполнение данными**
   ```bash
   # В новом терминале:
   docker compose exec app python -u scripts/populate_db.py
   ```

5. **Готово!** 🎉
   - **Веб-интерфейс**: http://localhost:8000
   - **API документация**: http://localhost:8000/docs
   - **Проверка здоровья**: http://localhost:8000/health

## 📊 Данные и статистика

### Источник данных
Проект использует данные **RetailRocket** - реальный dataset из e-commerce с событиями пользователей, товарами и их свойствами.

### Структура событий
- **view** - просмотры товаров (93,807 событий)
- **addtocart** - добавления в корзину (18,637 событий)  
- **transaction** - покупки (16,906 событий)

### Обработка данных
- **Демо-режим**: Загружены последние 5 событий каждого пользователя
- **Совместимость с ML**: Статистики близки к обучающим данным
- **Реалистичность**: ~3.4 события на пользователя

## 🔌 API

### Основные эндпоинты

#### Пользователи
```http
GET    /users/                 # Список пользователей
POST   /users/                 # Создать пользователя
GET    /users/{id}             # Получить пользователя
```

#### Товары
```http
GET    /items/                 # Список товаров
POST   /items/                 # Создать товар
GET    /items/{id}             # Получить товар
```

#### Рекомендации
```http
GET    /recommendations/{user_id}    # Персональные рекомендации
```

#### Аналитика
```http
GET    /analytics/stats              # Системная статистика
GET    /analytics/popular-items      # Популярные товары
GET    /analytics/active-users       # Активные пользователи
```

#### Каталог
```http
GET    /catalog/items               # Товары с фильтрацией
GET    /catalog/categories          # Категории товаров
```

### Примеры использования

**Получить рекомендации:**
```bash
curl "http://localhost:8000/recommendations/172?top_k=5"
```

**Системная статистика:**
```bash
curl "http://localhost:8000/analytics/stats"
```

**Создать событие:**
```bash
curl -X POST "http://localhost:8000/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "item_id": 456,
    "event_type": "view"
  }'
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты (49 штук)
docker compose exec app python -m pytest

# С подробным выводом
docker compose exec app python -m pytest -v

# Конкретный модуль
docker compose exec app python -m pytest app/tests/test_recommendations.py
```

### Покрытие тестами

- ✅ **CRUD операции** для всех моделей
- ✅ **Рекомендательная система** (холодный старт, персонализация)
- ✅ **Обработка ошибок** и валидация
- ✅ **API эндпоинты** и бизнес-логика
- ✅ **Граничные случаи** и производительность

### Результаты

```
===== 49 passed, 59 warnings in 1.09s =====
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql://...` |
| `DEV_MODE` | Режим разработки | `true` |
| `POSTGRES_USER` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `postgres` |
| `POSTGRES_DB` | Имя базы данных | `recommendation_db` |

### Настройки модели

В файле `app/routers/recommendations.py`:
- **FEATURE_COLS** - список признаков для ML
- **MAX_CANDIDATES** - максимум товаров для обработки (10,000)
- **Rate limiting** - 30 запросов в минуту

## 🛠️ Разработка

### Структура проекта

```
my_mvp_project/
├── app/                           # Основное приложение
│   ├── __init__.py               # Пакет приложения
│   ├── main.py                   # FastAPI приложение
│   ├── database.py               # Настройки БД
│   ├── models.py                 # SQLAlchemy модели
│   ├── schemas.py                # Pydantic схемы
│   ├── common_utils.py           # Общие утилиты
│   ├── limiter.py                # Rate limiting
│   ├── routers/                  # API эндпоинты
│   │   ├── __init__.py           # Пакет роутеров
│   │   ├── analytics.py          # Аналитика и метрики
│   │   ├── catalog.py            # Каталог товаров
│   │   ├── categories.py         # Управление категориями
│   │   ├── crud.py               # CRUD операции
│   │   ├── events.py             # События пользователей
│   │   ├── item_properties.py    # Свойства товаров
│   │   ├── items.py              # Управление товарами
│   │   ├── recommendations.py    # ML рекомендации
│   │   └── users.py              # Управление пользователями
│   ├── recommend/                # Рекомендательная система
│   │   ├── __init__.py           # Пакет рекомендаций
│   │   ├── utils.py              # ML утилиты
│   │   └── model.pkl             # Обученная CatBoost модель
│   ├── static/                   # Веб-интерфейс
│   │   ├── index.html            # Главная страница
│   │   ├── style.css             # CSS стили
│   │   └── script.js             # JavaScript логика
│   └── tests/                    # Автотесты
│       ├── __init__.py           # Пакет тестов
│       ├── conftest.py           # Pytest конфигурация
│       ├── test_api.py           # Тесты API
│       ├── test_categories.py    # Тесты категорий
│       ├── test_events.py        # Тесты событий
│       ├── test_item_properties.py # Тесты свойств
│       ├── test_items.py         # Тесты товаров
│       ├── test_recommendations.py # Тесты рекомендаций
│       └── test_users.py         # Тесты пользователей
├── scripts/                      # Утилиты и скрипты
│   └── populate_db.py            # Загрузка данных в БД
├── notebooks/                    # ML эксперименты
│   ├── model_training.ipynb      # Обучение модели
│   └── catboost_info/            # Логи CatBoost
├── data/                         # Исходные данные
│   ├── category_tree.csv         # Дерево категорий
│   ├── events.csv                # События пользователей
│   ├── item_properties_part1.csv # Свойства товаров (часть 1)
│   └── item_properties_part2.csv # Свойства товаров (часть 2)
├── .env.example                  # Шаблон .env
├── .gitignore                    # Git исключения
├── docker-compose.yml            # Docker композиция
├── Dockerfile                    # Docker образ
├── requirements.txt              # Python зависимости
└── README.md                     # Документация проекта
```

### Локальная разработка

1. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Запуск БД отдельно:**
   ```bash
   docker compose up db -d
   ```

3. **Запуск приложения:**
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/recommendation_db"
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Добавление новых функций

1. **API эндпоинты** → `app/routers/`
2. **Модели данных** → `app/models.py`
3. **Валидация** → `app/schemas.py`
4. **Тесты** → `app/tests/`
5. **UI компоненты** → `app/static/`

---