from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class ModiamiStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "modiami.com" in url

    def scrape(self, page: Page, url: str) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Modiami: {url}")
        jobs: List[Dict[str, Any]] = []
        try:
            try:
                page.wait_for_selector("a[href]", timeout=8000)
            except:
                pass
            anchors = page.query_selector_all('article a[href], a[href*="modiami.com"]')
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            for a in anchors:
                try:
                    href = a.get_attribute("href") or ""
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = f"{base}{href}"
                    if "search/label" in href:
                        continue
                    title = a.inner_text().strip()
                    if not title or len(title) < 3:
                        continue
                    jobs.append({
                        "title": title[:120],
                        "company": "Modiami",
                        "location": "Unknown",
                        "link": href,
                        "platform": "Modiami"
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Modiami scrape error: {e}")
        return jobs[:100]
