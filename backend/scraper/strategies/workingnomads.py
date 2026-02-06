from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
import re
from datetime import datetime
import requests
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class WorkingNomadsStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "workingnomads.com" in url

    def scrape(self, page: Page, url: str) -> List[Dict[str, Any]]:
        logger.info(f"Scraping WorkingNomads: {url}")
        jobs: List[Dict[str, Any]] = []
        try:
            api_url = "https://www.workingnomads.com/api/exposed_jobs/"
            try:
                resp = requests.get(api_url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("jobs") or data
                    if isinstance(items, list):
                        for j in items:
                            try:
                                title = j.get("title") or ""
                                company = j.get("company_name") or "Unknown"
                                link = j.get("url") or ""
                                location = j.get("location") or "Unknown"
                                posted_at = None
                                pd = j.get("pub_date") or j.get("published_at") or j.get("date")
                                if isinstance(pd, str) and pd:
                                    ds = pd.strip().replace("Z", "+00:00")
                                    try:
                                        if re.match(r'^\\d{4}-\\d{2}-\\d{2}', ds):
                                            posted_at = datetime.fromisoformat(ds[:10])
                                    except Exception:
                                        posted_at = None
                                if title and (company or link):
                                    item = {
                                        "title": title[:120],
                                        "company": company,
                                        "location": location,
                                        "link": link or url,
                                        "platform": "WorkingNomads"
                                    }
                                    if posted_at:
                                        item["posted_at"] = posted_at
                                    jobs.append(item)
                            except Exception:
                                continue
            except Exception as e:
                logger.warning(f"WorkingNomads API error: {e}")
        except Exception as e:
            logger.error(f"WorkingNomads scrape error: {e}")
        return jobs[:200]
