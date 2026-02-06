from typing import List, Dict, Any
from playwright.sync_api import Page, Response
import logging
import json
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

print("!!!!!!!!!!!!!!!! SNAPHUNT MODULE LOADED !!!!!!!!!!!!!!!!")

class SnaphuntStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "snaphunt.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        print(f"DEBUG: EXECUTION ENTERED SCRAPE METHOD for {url}", flush=True)
        try:
            with open("snaphunt_debug.log", "a") as f:
                f.write(f"DEBUG: Entering SnaphuntStrategy.scrape (MODIFIED) for {url}\n")
        except Exception as e:
            print(f"DEBUG: Failed to write to log file: {e}", flush=True)

        logger.info(f"DEBUG: Entering SnaphuntStrategy.scrape (MODIFIED) for {url}")
        logger.info(f"Scraping Snaphunt: {url}")
        jobs = []
        self.stats["pages"] = 0
        self.total_jobs_from_api = 0
        self.seen_ids = set()
        
        # API Interception
        def handle_response(response: Response):
            if "api.snaphunt.com" in response.url:
                 logger.info(f"Snaphunt API call: {response.url} ({response.status})")
            
            # Match generic jobs endpoint or company jobs
            if ("api.snaphunt.com" in response.url and "jobs" in response.url) or ("api.snaphunt.com/companies" in response.url):
                # We check content type to avoid image/css
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    return

                try:
                    # Some endpoints might be 302 or 204
                    if response.status != 200:
                        return

                    data = response.json()
                    
                    # Handle Lambda-like wrapper
                    if "body" in data and "statusCode" in data:
                        import json as json_lib
                        body = data["body"]
                        if isinstance(body, str):
                            data = json_lib.loads(body)
                        else:
                            data = body
                            
                    # logger.info(f"Snaphunt API response keys: {data.keys() if isinstance(data, dict) else 'List'}")
                    if isinstance(data, dict):
                         total_count = data.get("total") or data.get("count")
                         if total_count and isinstance(total_count, int):
                             self.total_jobs_from_api = total_count
                             logger.info(f"API Total Count: {total_count}")
                    
                    job_list = []
                    if isinstance(data, list):
                        job_list = data
                    elif isinstance(data, dict):
                        # Try various keys where jobs might be hidden
                        job_list = data.get("jobs", data.get("data", data.get("list", [])))
                    
                    if not job_list:
                        return

                    logger.info(f"Parsed {len(job_list)} jobs from API")

                    if job_list:
                        # logger.info(f"Intercepted Snaphunt API with {len(job_list)} jobs")
                            
                        for post in job_list:
                            # Map fields
                            title = post.get("title") or post.get("jobTitle", "Unknown")
                            job_id = post.get("id") or post.get("_id")
                            ref_id = post.get("refId") or post.get("jobReferenceId")

                            # Unique ID check
                            unique_key = job_id or ref_id or title
                            
                            # Check if we already have this job
                            existing_job = None
                            for j in jobs:
                                if j.get("_id") == unique_key:
                                    existing_job = j
                                    break
                            
                            if unique_key in self.seen_ids and not existing_job:
                                continue

                            # Description extraction logic (reused)
                            description = post.get("description")
                            if not description:
                                description = post.get("jobDescription")
                            if not description:
                                description = post.get("roleDescription")
                            if not description:
                                description = post.get("details")
                            if not description:
                                description = post.get("body")
                            if not description:
                                description = ""
                            
                            # Clean up
                            try:
                                if description and isinstance(description, str):
                                    if description.startswith("undefined"):
                                        description = description.replace("undefined", "", 1)
                                    if description.endswith("undefined"):
                                         description = description[:-9]
                                    description = description.replace("undefined<", "<")
                            except Exception as e:
                                logger.warning(f"Error cleaning description: {e}")

                            if existing_job:
                                # If existing job has no description but we found one now, update it
                                current_desc = existing_job.get("description", "")
                                if (not current_desc or len(current_desc) < 50) and description and len(description) > 50:
                                    existing_job["description"] = description
                                    logger.info(f"Updated description for job: {title}")
                                continue

                            if unique_key in self.seen_ids:
                                continue

                            self.seen_ids.add(unique_key)
                            
                            # Use refId (short code) for URL construction, or careerJobLink if absolute
                            career_link = post.get("careerJobLink")
                            
                            if career_link:
                                link = career_link
                            elif ref_id:
                                # Snaphunt links: https://odixcity.snaphunt.com/job/{refId}
                                base_domain = url.split("?")[0].rstrip("/")
                                if "snaphunt.com" not in base_domain:
                                    base_domain = "https://snaphunt.com"
                                link = f"{base_domain}/job/{ref_id}"
                            else:
                                # Fallback to ID (might redirect to home, but better than nothing)
                                link = f"https://snaphunt.com/job/{job_id}"
                            
                            # Location
                            location = "Unknown"
                            if post.get("country"):
                                location = post.get("country")
                            if post.get("city"):
                                location = f"{post.get('city')}, {location}"
                            
                            job = {
                                "title": title,
                                "company": "Snaphunt Board",
                                "location": location,
                                "link": link,
                                "platform": "Snaphunt",
                                "description": description,
                                "_id": unique_key # Store for update matching
                            }
                            jobs.append(job)
                            
                        # Update stats
                        import math
                        self.stats["pages"] = math.ceil(len(jobs) / 20)
                        
                        if on_jobs_found:
                            on_jobs_found(jobs, stats=self.stats)
                            
                except Exception as e:
                    logger.error(f"Error parsing Snaphunt API: {e}")

        page.on("response", handle_response)
        
        print(f"DEBUG: Snaphunt navigating to {url}")
        logger.info(f"Navigating to {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Scroll loop
            last_height = 0
            retries = 0
            scroll_cycles = 0
            # Increase max cycles to handle more pages (e.g., 50 * 20 jobs = 1000 jobs)
            max_cycles = 50 
            
            while True:
                # Scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000)
                page.wait_for_load_state("networkidle")
                
                current_count = len(jobs)
                # Log job count
                print(f"DEBUG: Snaphunt scroll loop. Jobs: {current_count}/{self.total_jobs_from_api}")
                
                # If we reached the total count from API, stop scrolling
                if self.total_jobs_from_api > 0 and current_count >= self.total_jobs_from_api:
                    logger.info("Reached total job count from API. Stopping scroll.")
                    break

                # Try clicking load more if visible
                more_btn = page.query_selector("button:has-text('Load more'), button:has-text('Show more')")
                if more_btn and more_btn.is_visible():
                    try:
                        more_btn.click()
                        page.wait_for_timeout(2000)
                        page.wait_for_load_state("networkidle")
                    except Exception:
                        pass

                # Check if height changed
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    retries += 1
                    if retries >= 8:
                        # Before giving up, look for load more one last time
                        more_btn = page.query_selector("button:has-text('Show more'), button:has-text('Load more')")
                        if more_btn and more_btn.is_visible():
                            try:
                                more_btn.click()
                                page.wait_for_timeout(3000)
                                retries = 0
                                continue
                            except Exception:
                                pass
                        
                        logger.info("Scroll stuck and no more buttons. Exiting loop.")
                        break
                else:
                    retries = 0
                    last_height = new_height
                    scroll_cycles += 1
                    if scroll_cycles >= max_cycles:
                        logger.info("Reached max scroll cycles. Stopping.")
                        break
                
        except Exception as e:
            logger.error(f"Snaphunt scrape error: {e}")

        # Post-processing: Fetch details for jobs with missing descriptions
        if jobs:
            logger.info(f"Collected {len(jobs)} jobs. Checking for missing descriptions...")
            print(f"DEBUG: Starting detail scraping for {len(jobs)} jobs...", flush=True)
            
            for i, job in enumerate(jobs):
                # If description is too short (likely just a summary) or empty
                if len(job.get("description", "")) < 100:
                    link = job.get("link")
                    if link and "snaphunt.com" in link:
                        try:
                            logger.info(f"Fetching details for job {i+1}/{len(jobs)}: {link}")
                            print(f"DEBUG: Fetching details for job {i+1}: {link}", flush=True)
                            
                            page.goto(link, wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(2000) # Wait for React to render
                            
                            # Selectors to try
                            selectors = [
                                ".job-description", 
                                "[data-testid='job-description']", 
                                "div[class*='JobDescription']", 
                                "div[class*='jobDescription']",
                                "div[class*='Description']",
                                "article"
                            ]
                            
                            full_desc = ""
                            for sel in selectors:
                                try:
                                    el = page.query_selector(sel)
                                    if el and el.is_visible():
                                        text = el.inner_html() # Use HTML to preserve formatting if possible, or inner_text
                                        # If text is substantial
                                        if len(text) > 100:
                                            full_desc = text
                                            logger.info(f"Found description with selector: {sel}")
                                            break
                                except:
                                    continue
                            
                            if full_desc:
                                job["description"] = full_desc
                            else:
                                logger.warning(f"Could not find description for {link}")
                                
                        except Exception as e:
                            logger.error(f"Failed to fetch details for {link}: {e}")
                            print(f"DEBUG: Error fetching details: {e}", flush=True)
                            
        return jobs
