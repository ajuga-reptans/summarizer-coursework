import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def fetch_article_text(url: str) -> str:
    """
    Надежный парсер на requests + BeautifulSoup.
    Избегает конфликтов с сигналами в async-окружении (Uvicorn/FastAPI).
    """
    logger.info(f"[SCRAPER] Start parsing: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        content = (
            soup.find("article") or
            soup.find("main") or
            soup.find("div", class_=["content", "article", "post", "entry", "text", "article-body", "post-content"]) or
            soup.find("section", class_=["content", "article"]) or
            soup.body
        )

        if content:
            text = content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        text = " ".join(text.split())

        if len(text) < 150:
            logger.warning(f"[SCRAPER] Extracted text too short: {len(text)} chars")
            return ""

        logger.info(f"[SCRAPER] SUCCESS: extracted {len(text)} characters")
        return text

    except Exception as e:
        logger.error(f"[SCRAPER] Error: {type(e).__name__} - {str(e)}")
        return ""