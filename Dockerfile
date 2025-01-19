# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо системні залежності для PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential gcc libmupdf-dev mupdf-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо всі файли проєкту до контейнера
COPY . /app

# Оновлюємо pip та встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Вказуємо команду для запуску додатку
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
