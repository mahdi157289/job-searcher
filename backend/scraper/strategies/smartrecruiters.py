from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class SmartRecruitersStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "smartrecruiters.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping SmartRecruiters: {url}")
        jobs: List[Dict[str, Any]] = []
        scraped_links = set()
        
        try:
            # Wait for content
            try:
                page.wait_for_selector("a", timeout=8000)
            except:
                pass
            
            # SmartRecruiters often lists jobs in a table or list
            # Links usually look like: https://jobs.smartrecruiters.com/{company}/{id}
            
            anchors = page.query_selector_all('a[href*="smartrecruiters.com"], a[href*="/jobs/"], a[href*="/positions/"]')
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            for a in anchors:
                try:
                    href = a.get_attribute("href") or ""
                    if not href:
                        continue
                    
                    # Filter out non-job links (e.g. privacy policy, login)
                    if "privacy" in href or "login" in href or "legal" in href or "help." in href:
                        continue
                        
                    # Filter out oneclick-ui (usually general application forms)
                    if "oneclick-ui" in href:
                        continue

                    if href.startswith("/"):
                        href = f"{base}{href}"
                    
                    # Deduplicate
                    if href in scraped_links:
                        continue

                    text = a.inner_text().strip()
                    if not text or len(text) < 3:
                        continue
                        
                    if text.lower() in ["here", "get in touch", "read more", "view all", "click here"]:
                        continue
                    
                    # Heuristic: Job links usually have longer text or specific structure
                    # But for now, we take all potential job links
                    
                    job = {
                        "title": text[:120],
                        "company": "SmartRecruiters Board",
                        "location": "Unknown",
                        "link": href,
                        "platform": "SmartRecruiters",
                        "description": ""
                    }
                    
                    jobs.append(job)
                    scraped_links.add(href)
                    
                except Exception:
                    continue
            
            # Stream initial list
            if on_jobs_found and jobs:
                on_jobs_found(jobs)

            # Fetch Details
            logger.info(f"Fetching details for {len(jobs)} jobs...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            for job in jobs:
                try:
                    resp = requests.get(job['link'], headers=headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # SmartRecruiters details usually in .job-sections or #job-details
                        desc_el = soup.select_one(".job-sections, #job-details, main, article")
                        if desc_el:
                            job["description"] = desc_el.get_text(separator="\n").strip()
                            if on_jobs_found:
                                on_jobs_found([job])
                except Exception as e:
                    logger.warning(f"Failed to fetch details for {job['link']}: {e}")

        except Exception as e:
            logger.error(f"SmartRecruiters scrape error: {e}")
            
        return jobs
