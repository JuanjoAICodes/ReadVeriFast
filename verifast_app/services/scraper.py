"""Simple article scraper using newspaper3k to retrieve full content from a URL."""
from typing import Tuple, Optional

from newspaper import Article as NPArticle  # type: ignore


def fetch_full_article(url: str, timeout: int = 20, language: Optional[str] = None) -> Tuple[bool, str]:
    """
    Fetch and parse the full article text from a URL using newspaper3k.

    Returns (success, text). On failure, returns (False, "").
    """
    try:
        art = NPArticle(url=url, language=language)
        art.download()
        art.parse()
        # article.nlp()  # Not required for text extraction; avoid extra time
        text = (art.text or "").strip()
        if not text:
            return False, ""
        # Heuristic rejection for likely video pages
        lower = text.lower()
        if any(marker in lower for marker in [
            'watch the video', 'ver el video', 'ver video', 'play video',
            'subscribe to our channel', 'suscríbete a nuestro canal'
        ]):
            return False, ""
        return True, text
    except Exception:
        return False, ""
