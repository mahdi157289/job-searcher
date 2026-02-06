from typing import List, Dict, Any
from playwright.sync_api import Page
import logging

logger = logging.getLogger(__name__)

class BaseStrategy:
    def __init__(self):
        self.stats = {"pages": 1}

    def can_handle(self, url: str) -> bool:
        return False

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        raise NotImplementedError
