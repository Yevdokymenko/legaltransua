# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    libmupdf-dev mupdf-tools \
    && apt-get clean

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо всі файли проєкту до контейнера
COPY . /app

# Оновлюємо pip та встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Команда для запуску Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.enableCORS=false"]
