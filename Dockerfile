# Базовий образ Python
FROM python:3.10-slim

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
