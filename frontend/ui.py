import streamlit as st
import requests

API_URL = "http://api:8000"

st.set_page_config(page_title="Суммаризатор", layout="centered")
st.title("📝 Сервис суммаризации веб-страниц")
st.caption("Введите ссылку на статью → получите краткое содержание")

url = st.text_input("URL статьи", placeholder="https://habr.com/ru/articles/123456/")

if st.button("Суммаризировать", type="primary"):
    if not url.startswith("http"):
        st.error("Введите корректный URL, начинающийся с http:// или https://")
    else:
        with st.spinner("Загружаю статью и генерирую саммари..."):
            try:
                resp = requests.post("http://api:8000/summarize", json={"url": url}, timeout=300)
                data = resp.json()
                if resp.status_code == 200:
                    st.success("✅ Готово!")
                    st.subheader("Краткое содержание:")
                    st.write(data["summary"])
                else:
                    st.error(data.get("detail", "Ошибка сервера"))
            except Exception as e:
                st.error(f"Не удалось подключиться к API: {e}")