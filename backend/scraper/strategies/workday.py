from typing import List, Dict, Any
from playwright.sync_api import Page, Response
import logging
from urllib.parse import urlparse
import time
import requests
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class WorkdayStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "myworkdayjobs.com" in url

    def scrape(self, page: Page, url: str) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Workday: {url}")
        jobs: List[Dict[str, Any]] = []
        self.api_jobs_total = 0
        self.base_api_url = None
        self.seen_urls = set()

        def handle_response(response: Response):
            try:
                if "myworkdayjobs.com" in response.url and "/jobs" in response.url:
                    if "json" in response.headers.get("content-type", ""):
                        data = response.json()
                        if "total" in data:
                            self.api_jobs_total = data["total"]
                            logger.info(f"Workday API Total: {self.api_jobs_total}")
                        
                        # Extract base API URL if not set
                        # URL is like .../wday/cxs/tenant/site/jobs
                        if not self.base_api_url:
                            self.base_api_url = response.url.split("/jobs")[0]
                            logger.info(f"Base API URL: {self.base_api_url}")

            except Exception as e:
                pass

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Pagination loop (Next button)
            page_num = 1
            max_pages = 4 # As requested: "jobs in the first 4 pages"
            collected_job_data = []
            
            while page_num <= max_pages:
                logger.info(f"Scraping page {page_num}")
                
                # Collect current page jobs
                anchors = page.query_selector_all('a[href*="/job/"]')
                parsed_base = urlparse(url)
                domain_base = f"{parsed_base.scheme}://{parsed_base.netloc}"
                
                new_jobs_count = 0
                for a in anchors:
                    try:
                        href = a.get_attribute("href") or ""
                        if not href:
                            continue
                        if href.startswith("/"):
                            href = f"{domain_base}{href}"
                        
                        if href in self.seen_urls:
                            continue
                        self.seen_urls.add(href)

                        title = a.inner_text().strip()
                        if "\n" in title:
                            title = title.split("\n")[0]

                        collected_job_data.append({
                            "title": title,
                            "link": href,
                            "location": "Unknown",
                            "company": "Workday Board",
                            "platform": "Workday"
                        })
                        new_jobs_count += 1
                    except Exception:
                        continue
                
                logger.info(f"Page {page_num}: Found {new_jobs_count} new jobs (Total collected: {len(collected_job_data)})")
                
                if page_num >= max_pages:
                    break
                    
                # Click Next
                try:
                    # Try multiple selectors for Next button
                    next_btn = page.query_selector("button[aria-label='next']")
                    if not next_btn:
                        next_btn = page.query_selector("[data-automation-id='nextPageButton']")
                    if not next_btn:
                        next_btn = page.query_selector("button:has-text('Next')")
                        
                    if next_btn and not next_btn.is_disabled():
                        logger.info("Clicking Next button...")
                        next_btn.click()
                        page.wait_for_timeout(3000)
                        page.wait_for_load_state("networkidle")
                        page_num += 1
                    else:
                        logger.info("No Next button or disabled. Stopping.")
                        break
                except Exception as e:
                    logger.error(f"Pagination error: {e}")
                    break
            
            logger.info(f"Collected {len(collected_job_data)} job links. Fetching details...")
            
            # Fallback: Construct Base API URL if not intercepted
            if not self.base_api_url:
                try:
                    parsed = urlparse(url)
                    # Host: tenant.wdX.myworkdayjobs.com
                    parts = parsed.netloc.split(".")
                    tenant = parts[0]
                    
                    # Path: /en-US/site or /site
                    path_parts = [p for p in parsed.path.split("/") if p]
                    site = ""
                    if path_parts:
                        # Skip locale if present
                        if len(path_parts[0]) == 5 and "-" in path_parts[0]:
                            if len(path_parts) > 1:
                                site = path_parts[1]
                        else:
                            site = path_parts[0]
                    
                    if site:
                        self.base_api_url = f"https://{parsed.netloc}/wday/cxs/{tenant}/{site}"
                        logger.info(f"Constructed Base API URL fallback: {self.base_api_url}")
                except Exception as e:
                    logger.warning(f"Failed to construct fallback API URL: {e}")
            
            # Fetch details
            for job in collected_job_data:
                description = ""
                location = "Unknown"
                
                if self.base_api_url:
                    # Construct detail API URL
                    # Link: .../job/Douala/Senior-Audit-IT--F-H-_R-7763
                    # API: .../job/Senior-Audit-IT--F-H-_R-7763
                    try:
                        slug = job["link"].split("/")[-1]
                        detail_url = f"{self.base_api_url}/job/{slug}"
                        
                        # We use requests here for speed, assuming public API
                        # Headers might be needed? Usually Accept: application/json is enough
                        headers = {
                            "Accept": "application/json",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        }
                        
                        resp = requests.get(detail_url, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            if "jobPostingInfo" in data:
                                info = data["jobPostingInfo"]
                                description = info.get("jobDescription", "")
                                location = info.get("location", location)
                                # Additional location info
                                if info.get("additionalLocations"):
                                    location += f", {', '.join(info.get('additionalLocations'))}"
                    except Exception as e:
                        logger.error(f"Failed to fetch details for {job['link']}: {e}")
                
                job["description"] = description
                job["location"] = location
                jobs.append(job)

        except Exception as e:
            logger.error(f"Workday scrape error: {e}")
            
        return jobs
