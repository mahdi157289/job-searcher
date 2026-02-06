from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class BambooHRStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "bamboohr.com" in url

    def scrape(self, page: Page, url: str) -> List[Dict[str, Any]]:
        logger.info(f"Scraping BambooHR: {url}")
        jobs: List[Dict[str, Any]] = []
        try:
            try:
                page.wait_for_selector("a[href]", timeout=8000)
            except:
                pass
            anchors = page.query_selector_all('a[href*="jobs/view"], a[href*="jobs/view.php"], a[href*="/jobs/"]')
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            for a in anchors:
                try:
                    href = a.get_attribute("href") or ""
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = f"{base}{href}"
                    title = a.inner_text().strip()
                    if not title or len(title) < 3:
                        continue
                    jobs.append({
                        "title": title[:120],
                        "company": "BambooHR Board",
                        "location": "Unknown",
                        "link": href,
                        "platform": "BambooHR"
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"BambooHR scrape error: {e}")
        return jobs[:100]
