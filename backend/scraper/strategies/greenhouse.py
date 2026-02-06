from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class GreenhouseStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "greenhouse.io" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Greenhouse: {url}")
        jobs = []
        scraped_links = set()
        
        # Check if it's the login page
        if "my.greenhouse.io" in url:
            logger.warning(f"Skipping Greenhouse Login Page: {url}")
            return []

        # Wait for the main content
        try:
            page.wait_for_selector("#main, .main, #jobs, .jobs, section.level-0", timeout=5000)
        except:
            pass
            
        # Scroll to bottom to ensure lazy-loaded jobs are loaded
        try:
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except:
            pass
        
        # Strategy 1: Look for .opening (Classic Greenhouse)
        job_elements = page.query_selector_all(".opening")
        
        # Strategy 2: If no openings, look for any link that contains '/jobs/'
        if not job_elements:
             links = page.query_selector_all("a[href*='/jobs/']")
             if links:
                 job_elements = links

        for element in job_elements:
            try:
                # Determine if element is just a link or a container
                tag_name = element.evaluate("el => el.tagName")
                
                title = "Unknown"
                link = None
                location = "Unknown"

                if tag_name == 'A':
                     raw_text = element.inner_text().strip()
                     if '\n' in raw_text:
                         parts = [p.strip() for p in raw_text.split('\n') if p.strip()]
                         if len(parts) >= 2:
                             title = parts[0]
                             location = parts[-1]
                         else:
                             title = raw_text
                     else:
                         title = raw_text
                     link = element.get_attribute("href")
                else:
                    # Classic .opening structure
                    title_el = element.query_selector("a")
                    location_el = element.query_selector(".location")
                    
                    if title_el:
                        title = title_el.inner_text().strip()
                        link = title_el.get_attribute("href")
                        location = location_el.inner_text().strip() if location_el else "Unknown"
                    else:
                        continue

                if link:
                    if not link.startswith("http"):
                         if link.startswith("/"):
                             parsed = urlparse(url)
                             link = f"{parsed.scheme}://{parsed.netloc}{link}"
                    
                    job = {
                        "title": title,
                        "company": "Greenhouse Board",
                        "location": location,
                        "link": link,
                        "platform": "Greenhouse",
                        "description": ""
                    }
                    
                    if link not in scraped_links:
                        jobs.append(job)
                        scraped_links.add(link)
            except Exception as e:
                pass 
        
        # Stream initial list
        if on_jobs_found and jobs:
            on_jobs_found(jobs)

        # Fetch details
        logger.info(f"Fetching details for {len(jobs)} jobs...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for job in jobs:
            if job.get("description"): continue
            
            try:
                # Use Playwright for details if available, otherwise requests
                # But here we are inside scrape, so we have 'page' available.
                # However, navigating 'page' might be slow if we have many jobs.
                # Let's stick to requests for speed, but handle timeouts better.
                
                resp = requests.get(job['link'], headers=headers, timeout=30, verify=False)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Try common content containers
                    desc_el = soup.select_one("#content, #main, .content, .main, .job-description, [itemprop='description']")
                    if desc_el:
                        job["description"] = desc_el.get_text(separator="\n").strip()
                        if on_jobs_found:
                            on_jobs_found([job])
            except Exception as e:
                logger.warning(f"Failed to fetch details for {job['link']}: {e}")
                
        return jobs
