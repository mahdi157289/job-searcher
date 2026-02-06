from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Response
import logging
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class AshbyStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "ashbyhq.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Ashby: {url}")
        jobs = []
        scraped_links = set()
        self.stats["pages"] = 0
        
        # API Interception Storage
        api_jobs = []
        
        def handle_response(response: Response):
            try:
                # Intercept Job Board API (GraphQL)
                # URL often contains 'ApiJobBoardWithTeams' or just 'ApiJobBoard'
                if ("ApiJobBoard" in response.url or "graphql" in response.url) and response.status == 200:
                    try:
                        # Only try to parse if it looks like the right endpoint
                        # We can check the request post data usually, but response url query params help too
                        if "ApiJobBoard" in response.url:
                            data = response.json()
                            board = None
                            
                            # Navigate JSON structure
                            if "data" in data and "jobBoard" in data["data"]:
                                board = data["data"]["jobBoard"]
                            
                            if board:
                                postings = board.get("jobPostings", [])
                                logger.info(f"Intercepted Ashby API with {len(postings)} jobs")
                                
                                # Extract Company Name if available
                                # company_name = "Ashby Board" # Default
                                # if "teams" in board and len(board["teams"]) > 0:
                                #     pass 
                                
                                for post in postings:
                                    job_id = post.get("id")
                                    if not job_id: continue
                                    
                                    # Construct link
                                    # If url is https://jobs.ashbyhq.com/linear
                                    # Link is https://jobs.ashbyhq.com/linear/{id}
                                    base_url = url.split("?")[0].rstrip("/")
                                    # Handle case where base_url already ends with ID (unlikely for board)
                                    link = f"{base_url}/{job_id}"
                                    
                                    title = post.get("title", "Unknown")
                                    location = post.get("locationName", "Unknown")
                                    if post.get("secondaryLocations"):
                                        location += f" (+{len(post['secondaryLocations'])})"
                                    
                                    job = {
                                        "title": title,
                                        "company": "Ashby Board",
                                        "location": location,
                                        "link": link,
                                        "platform": "Ashby",
                                        "description": "" # To be filled
                                    }
                                    
                                    if link not in scraped_links:
                                        api_jobs.append(job)
                                        scraped_links.add(link)
                    except Exception as e:
                        # logger.warning(f"Error parsing Ashby API: {e}")
                        pass
            except:
                pass

        # Attach listener
        page.on("response", handle_response)
        
        # Navigate
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            self.stats["pages"] = 1
            
            # 1. Try to parse window.__appData from page content (Most reliable)
            try:
                content = page.content()
                match = re.search(r'window\.__appData\s*=\s*({.*?});', content)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    
                    # Check jobPostings directly
                    postings = data.get("jobPostings", [])
                    
                    # If not direct, check jobBoard
                    if not postings and "jobBoard" in data:
                         postings = data["jobBoard"].get("jobPostings", [])
                         
                    if postings:
                        logger.info(f"Found {len(postings)} jobs in window.__appData")
                        for post in postings:
                            job_id = post.get("id")
                            if not job_id: continue
                            
                            # Construct link
                            base_url = url.split("?")[0].rstrip("/")
                            # Handle if url ends with trailing slash or not
                            link = f"{base_url}/{job_id}"
                            
                            title = post.get("title", "Unknown")
                            location = post.get("locationName", "Unknown")
                            if post.get("secondaryLocations"):
                                location += f" (+{len(post['secondaryLocations'])})"
                            
                            job = {
                                "title": title,
                                "company": "Ashby",
                                "location": location,
                                "link": link,
                                "platform": "Ashby",
                                "description": ""
                            }
                            
                            if link not in scraped_links:
                                jobs.append(job)
                                scraped_links.add(link)
            except Exception as e:
                logger.warning(f"Error parsing window.__appData: {e}")

            # Wait a bit for API calls to fire (if needed)
            try:
                if not jobs:
                    page.wait_for_timeout(3000) 
                    # Scroll to bottom just in case
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Navigation error: {e}")

        # If API interception worked, use it (merge)
        if api_jobs:
            count_new = 0
            for job in api_jobs:
                if job['link'] not in scraped_links:
                    jobs.append(job)
                    scraped_links.add(job['link'])
                    count_new += 1
            if count_new > 0:
                logger.info(f"Added {count_new} jobs from API interception")
        else:
            # Fallback to DOM scraping
            if not jobs:
                logger.info("API interception and JSON parsing failed, falling back to DOM scraping")
                try:
                    anchors = page.query_selector_all("a")
                    for a in anchors:
                        href = a.get_attribute("href")
                        if href and re.search(r'/[0-9a-f-]{10,}', href):
                            text = a.inner_text().strip()
                            lines = [l.strip() for l in text.split('\n') if l.strip()]
                            title = lines[0] if lines else "Unknown"
                            
                            # Fix link
                            if href.startswith("/"):
                                parsed = urlparse(url)
                                full_link = f"{parsed.scheme}://{parsed.netloc}{href}"
                            else:
                                full_link = href
                                
                            job = {
                                "title": title,
                                "company": "Ashby Board",
                                "location": "Unknown",
                                "link": full_link,
                                "platform": "Ashby"
                            }
                            
                            if full_link not in scraped_links:
                                jobs.append(job)
                                scraped_links.add(full_link)
                except Exception as e:
                    logger.error(f"DOM fallback failed: {e}")

        # Update page stats based on volume if it's 1 (SPA logic)
        if self.stats["pages"] == 1 and len(jobs) > 20:
             import math
             # Heuristic: 20 jobs per "visual page"
             self.stats["pages"] = math.ceil(len(jobs) / 20)

        # Stream initial jobs (without details)
        if on_jobs_found and jobs:
             # Batch stream initially
             on_jobs_found(jobs, stats=self.stats)

        # Fetch Details
        logger.info(f"Fetching details for {len(jobs)} jobs...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for i, job in enumerate(jobs):
            if job.get("description"): continue # Already has description
            
            try:
                # Hybrid: Try requests first (Much Faster)
                resp = requests.get(job['link'], headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    # 1. Try meta description (often a summary)
                    meta_desc = soup.find("meta", attrs={"name": "description"})
                    desc_text = ""
                    if meta_desc:
                        desc_text = meta_desc.get("content", "").strip()
                    
                    # 2. Try to find the full description container
                    # Ashby structure usually has a main container
                    desc_el = soup.select_one("div[class*='JobDescription'], div[class*='description'], .job-description, main")
                    if desc_el:
                         full_text = desc_el.get_text(separator="\n").strip()
                         # Prefer full text if significantly longer
                         if len(full_text) > len(desc_text):
                             desc_text = full_text
                    
                    if desc_text:
                        job["description"] = desc_text
                        # Stream update
                        if on_jobs_found:
                            on_jobs_found([job], stats=self.stats)
                            
            except Exception as e:
                logger.warning(f"Failed to fetch details for {job['link']}: {e}")
                # Optional: Fallback to Playwright visit if requests fail repeatedly
                # but for Ashby, requests usually work fine.

        return jobs
