# Використовуємо Python образ
FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && apt-get clean

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо проєкт до контейнера
COPY . /app

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Запускаємо додаток
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
