import os
import streamlit as st
from translate_script import (
    extract_text, translate_text_google, translate_text_marian, translate_text_openai,
    setup_document_orientation, add_title, create_translation_table, extract_text_from_url
)
from transformers import MarianMTModel, MarianTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed
import docx
import logging
import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ініціалізація MarianMT
model_name = "Helsinki-NLP/opus-mt-en-uk"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Перевірка та створення папки temp
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Налаштування сторінки
st.set_page_config(page_title="LegalTransUA", layout="wide")

# Фон і стилі тексту
st.markdown(
    """
    <style>
    /* Фон для всієї сторінки */
    body {
        background-color: #f8f4e7; /* Світло-бежевий фон */
    }

    /* Контейнер Streamlit */
    [data-testid="stAppViewContainer"] {
        background-color: #f8f4e7;
        color: black; /* Чорний текст */
    }

    /* Заголовки */
    h1, h2, h3, h4, h5, h6 {
        color: black; /* Чорний колір заголовків */
    }

    /* Текст для описів і параграфів */
    p {
        color: black; /* Чорний текст для параграфів */
    }

    /* Стиль елементів вибору */
    label {
        color: black; /* Чорний текст для міток */
    }

    /* Кнопки */
    button {
        color: white !important; /* Білий текст */
        background-color: #007bff; /* Синій фон */
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }

    button:hover {
        background-color: #0056b3; /* Темніший синій при наведенні */
    }

    /* Текст у боковому меню */
    .css-1aumxhk, .css-qbe2hs {
        color: white !important; /* Білий текст у боковій панелі */
    }

    /* Лінки */
    a {
        color: #0056b3; /* Темно-синій для посилань */
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.image("https://i.imgur.com/JmLIg6y.jpeg", use_container_width=True)

# Навігаційні кнопки
st.sidebar.title("Меню навігації")
section = st.sidebar.radio(
    "Перейдіть до розділу:",
    ["Головна сторінка", "Про додаток", "Корисні посилання", "Допомога Україні", "Контакти"]
)

if section == "Головна сторінка":
    st.title("LegalTransUA")
    st.header("Перекладач документів")
    st.write("Завантажте файл (DOCX або PDF) або введіть URL для перекладу.")

    # Вибір джерела
    type_of_source = st.radio("Оберіть тип джерела:", ["Файл", "URL"])

    # Функція для збереження файлу
    def save_uploaded_file(uploaded_file):
        file_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path

    if type_of_source == "Файл":
        uploaded_file = st.file_uploader("Завантажте файл (DOCX або PDF):", type=["docx", "pdf"])
        if uploaded_file:
            file_path = save_uploaded_file(uploaded_file)
            st.success(f"Файл '{uploaded_file.name}' успішно завантажено.")

            if st.button("Розпочати переклад"):
                paragraphs = extract_text(file_path)
                st.info(f"Знайдено {len(paragraphs)} абзаців для перекладу.")

                # Прогрес-бари
                google_progress = st.progress(0, text="Google Translate: 0%")
                marian_progress = st.progress(0, text="MarianMT: 0%")
                openai_progress = st.progress(0, text="OpenAI GPT: 0%")

                # Переклад
                google_translations = ["" for _ in paragraphs]
                marian_translations = ["" for _ in paragraphs]
                openai_translations = ["" for _ in paragraphs]

                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Google Translate
                    google_futures = {executor.submit(translate_text_google, para): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(google_futures)):
                        idx = google_futures[future]
                        google_translations[idx] = future.result()
                        google_progress.progress((i + 1) / len(paragraphs), text=f"Google Translate: {int((i + 1) / len(paragraphs) * 100)}%")

                    # MarianMT
                    marian_futures = {executor.submit(translate_text_marian, para, tokenizer, model): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(marian_futures)):
                        idx = marian_futures[future]
                        marian_translations[idx] = future.result()
                        marian_progress.progress((i + 1) / len(paragraphs), text=f"MarianMT: {int((i + 1) / len(paragraphs) * 100)}%")

                    # OpenAI GPT
                    openai_futures = {executor.submit(translate_text_openai, para): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(openai_futures)):
                        idx = openai_futures[future]
                        openai_translations[idx] = future.result()
                        openai_progress.progress((i + 1) / len(paragraphs), text=f"OpenAI GPT: {int((i + 1) / len(paragraphs) * 100)}%")

                # Збереження результатів у файл
                base_name = os.path.splitext(uploaded_file.name)[0]
                output_file = os.path.join(TEMP_DIR, f"{base_name}.docx")
                doc = docx.Document()

                # Налаштування документа
                setup_document_orientation(doc)
                add_title(doc)
                create_translation_table(doc, paragraphs, google_translations, marian_translations, openai_translations)

                doc.save(output_file)

                st.success("Переклад завершено!")
                st.download_button(
                label="Завантажити таблицю DOCX",
                data=open(output_file, "rb").read(),
                file_name=f"Переклад_{os.path.splitext(uploaded_file.name)[0]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

    elif type_of_source == "URL":
        url = st.text_input("Введіть URL:")
        if url and st.button("Розпочати переклад"):
            st.info(f"Завантаження тексту з {url}...")
            paragraphs = extract_text_from_url(url)

            if not paragraphs:
                st.warning("Не вдалося знайти текст на сторінці.")
            else:
                st.success(f"Знайдено {len(paragraphs)} абзаців для перекладу.")

                # Прогрес-бари
                google_progress = st.progress(0, text="Google Translate: 0%")
                marian_progress = st.progress(0, text="MarianMT: 0%")
                openai_progress = st.progress(0, text="OpenAI GPT: 0%")

                # Переклад
                google_translations = ["" for _ in paragraphs]
                marian_translations = ["" for _ in paragraphs]
                openai_translations = ["" for _ in paragraphs]

                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Google Translate
                    google_futures = {executor.submit(translate_text_google, para): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(google_futures)):
                        idx = google_futures[future]
                        google_translations[idx] = future.result()
                        google_progress.progress((i + 1) / len(paragraphs), text=f"Google Translate: {int((i + 1) / len(paragraphs) * 100)}%")

                    # MarianMT
                    marian_futures = {executor.submit(translate_text_marian, para, tokenizer, model): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(marian_futures)):
                        idx = marian_futures[future]
                        marian_translations[idx] = future.result()
                        marian_progress.progress((i + 1) / len(paragraphs), text=f"MarianMT: {int((i + 1) / len(paragraphs) * 100)}%")

                    # OpenAI GPT
                    openai_futures = {executor.submit(translate_text_openai, para): idx for idx, para in enumerate(paragraphs)}
                    for i, future in enumerate(as_completed(openai_futures)):
                        idx = openai_futures[future]
                        openai_translations[idx] = future.result()
                        openai_progress.progress((i + 1) / len(paragraphs), text=f"OpenAI GPT: {int((i + 1) / len(paragraphs) * 100)}%")

                # Збереження результатів у таблицю
                output_file = os.path.join(TEMP_DIR, "Translated_from_URL.docx")
                doc = docx.Document()
                setup_document_orientation(doc)
                add_title(doc)
                create_translation_table(doc, paragraphs, google_translations, marian_translations, openai_translations)
                doc.save(output_file)

                st.success("Переклад завершено!")
                st.download_button(
                    label="Завантажити таблицю DOCX",
                    data=open(output_file, "rb").read(),
                    file_name="Переклад_URL.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

elif section == "Про додаток":
    st.title("Про LegalTransUA")
    st.write("""
    **LegalTransUA** — це інноваційний додаток для автоматизації перекладу юридичних документів.
    Основні можливості:
    - Переклад з англійської на українську мову;
    - Робота з файлами у форматах DOCX та PDF;
    - Максимальна точність перекладу з урахуванням юридичної термінології.
    """)

elif section == "Корисні посилання":
    st.title("Корисні посилання")
    st.markdown("""
    - [Європейське законодавство](https://eur-lex.europa.eu/)
    - [Законодавство України](https://zakon.rada.gov.ua/)
    - [Переклади документів ЄС](https://euractiv.com/)
    """)

elif section == "Допомога Україні":
    st.title("Допомога Україні")
    st.write("""
    Росія розпочала агресію проти України, порушивши всі міжнародні закони та норми. Україна прагне стати частиною європейської спільноти та бореться за свою незалежність.
    Ви можете підтримати Україну, зробивши внесок у фонд [Повернись живим](https://savelife.in.ua/).
    """)

elif section == "Контакти":
    st.title("Контакти")
    st.write("""
    Якщо у вас є питання чи пропозиції, зв'яжіться зі мною:
    - **Email:** yevdokymenkodn@gmail.com
    - **Телефон:** +380 66 556 0001
    - **LinkedIn:** [Профіль](https://www.linkedin.com/in/yevdokymenko/)
    """)