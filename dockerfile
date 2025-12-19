# Используем легкий образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости для работы с Postgres и сборки пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Указываем рабочую папку внутри контейнера
WORKDIR /app

# Копируем список библиотек
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . .

# Команда для запуска нашего приложения
CMD ["python", "app.py"]