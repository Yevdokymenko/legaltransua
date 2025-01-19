# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо системні залежності для PyMuPDF
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

# Вказуємо команду для запуску Streamlit-додатка
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.enableCORS=false"]
# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо локальні файли в контейнер
COPY . /app

# Встановлюємо необхідні пакети
RUN pip install --no-cache-dir -r requirements.txt

# Відкриваємо порт 8501
EXPOSE 8501

# Запускаємо Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
