# Стартовый набор для создания тг-ботов
## Установка и настройка

### 1. Клонирование репозитория

Сначала склонируйте репозиторий на локальную машину:

```bash
git clone https://github.com/mrInsaf/TgBotsStarterPack.git
```

### 2. Создание и активация виртуального окружения (опционально):

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
.\venv\Scripts\activate   # Для Windows
```

### 3. Настройка базы данных MySQL:

Измените параметры подключения в файле db.py (переменная config) на ваши
```python
config = {
    'user': 'your_user',
    'password': 'your_password',
    'host': 'your_host',
    'database': 'your_database',
}
```

### 4. Получение токенов Telegram:

Получите токен для вашего бота через [BotFather](https://t.me/BotFather) и обновите переменные TEST_TOKEN и MAIN_TOKEN в файле main.py.

### 5. Запуск бота:

Для запуска бота используйте команду:

```bash
python main.py <token>
```
Где <token> — это либо 'test' для тестового режима, либо 'main' для основного режима.
