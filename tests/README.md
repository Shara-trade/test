# Тестирование

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py           # Фикстуры pytest
├── test_mining.py        # Тесты механики добычи
├── test_modules.py       # Тесты системы модулей
├── test_containers.py    # Тесты контейнеров
├── test_drones.py        # Тесты дронов
├── test_database.py      # Тесты БД
└── test_validators.py    # Тесты валидаторов
```

## Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=. --cov-report=html

# Конкретный файл
pytest tests/test_mining.py

# С выводом
pytest -v
```

## Требования

```bash
pip install pytest pytest-asyncio pytest-cov
```
