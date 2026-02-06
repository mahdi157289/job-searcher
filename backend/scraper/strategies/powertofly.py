from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
import time
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class PowerToFlyStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "powertofly.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping PowerToFly: {url}")
        jobs = []
        scraped_links = set()
        
        # API Interception Storage
        api_jobs = []
        
        def handle_response(response):
            # logger.info(f"Response: {response.url}") # Too noisy
            if "search/jobs" in response.url and response.status == 200:
                logger.info(f"Intercepted API call: {response.url}")
                try:
                    data = response.json()
                    # logger.info(f"API Response Data Keys: {data.keys()}")
                    # Check for common job list structures
                    items = []
                    if isinstance(data, dict):
                        if "data" in data and isinstance(data["data"], list):
                            items = data["data"]
                        elif "jobs" in data and isinstance(data["jobs"], list):
                            items = data["jobs"]
                        elif "results" in data and isinstance(data["results"], list):
                            items = data["results"]
                    
                    if items:
                        logger.info(f"Intercepted API response from {response.url} with {len(items)} items")
                        for item in items:
                            # Normalize job data from API
                            job_data = self._parse_api_job(item)
                            if job_data and job_data["link"] not in scraped_links:
                                api_jobs.append(job_data)
                                scraped_links.add(job_data["link"])
                except:
                    pass

        # Attach listener
        page.on("response", handle_response)
        
        try:
            page.goto(url)
            
            # Allow some time for API responses to arrive
            time.sleep(5)
            
            # Stream API jobs if found
            if api_jobs:
                logger.info(f"Found {len(api_jobs)} jobs via API interception. Continuing to scroll/paginate for more.")
                jobs.extend(api_jobs)
                if on_jobs_found:
                    on_jobs_found(api_jobs)
                # Do NOT stop scrolling; we need to trigger more API calls via pagination
                # max_scrolls = 0 
            
            # Set a production-ready scroll limit
            max_scrolls = 50 
            
            # Initialize pagination variables
            last_height = 0
            no_change_count = 0
            self.stats["pages"] = 0
            
            logger.info("Starting pagination loop...")
            for scroll in range(max_scrolls):
                self.stats["pages"] = scroll + 1
                # Get current job cards
                job_cards = page.query_selector_all(".job.box")
                new_jobs_batch = []
                
                for card in job_cards:
                    try:
                        title = card.get_attribute("data-job-title")
                        job_id = card.get_attribute("data-job-id")
                        
                        # If attributes missing, try inner text
                        if not title:
                            title_el = card.query_selector(".title")
                            if title_el:
                                title = title_el.inner_text().strip()
                            else:
                                title = "Unknown"
                                
                        # Company
                        company_el = card.query_selector(".company")
                        company = company_el.inner_text().strip() if company_el else "Unknown"
                        
                        # Location
                        location_el = card.query_selector(".location .item")
                        location = location_el.inner_text().strip() if location_el else "Unknown"
                        
                        # Link
                        if job_id:
                            link = f"https://powertofly.com/jobs/detail/{job_id}"
                        else:
                            # Try to find an anchor tag
                            link_el = card.query_selector("a")
                            if link_el:
                                link = link_el.get_attribute("href")
                                if link and link.startswith("/"):
                                    link = f"https://powertofly.com{link}"
                            else:
                                link = url # Fallback
                        
                        if link and link not in scraped_links:
                            # Basic info
                            job_data = {
                                "title": title,
                                "company": company,
                                "location": location,
                                "link": link,
                                "platform": "PowerToFly",
                                "description": "Loading details..." 
                            }
                            new_jobs_batch.append(job_data)
                            jobs.append(job_data) # Add to main list
                            scraped_links.add(link)
                    except Exception as e:
                        logger.warning(f"Error extracting card: {e}")
                
                # Stream basic info immediately
                if new_jobs_batch:
                    logger.info(f"Found {len(new_jobs_batch)} new jobs (Total: {len(jobs)})")
                    if on_jobs_found:
                        on_jobs_found(new_jobs_batch, stats=self.stats)
                
                # Check for "Load More" button first
                clicked_load_more = False
                try:
                    # Common selectors for load more buttons
                    # Try specific known classes or text
                    load_more_selectors = [
                        "button.load-more", 
                        ".load-more-jobs button", 
                        ".pagination-next", 
                        "button[class*='loadMore']",
                        "a.load-more-link"
                    ]
                    
                    load_more = None
                    for sel in load_more_selectors:
                        load_more = page.query_selector(sel)
                        if load_more and load_more.is_visible():
                            break
                    
                    if not load_more:
                        # Try by text content using xpath - stricter search
                        # Look for "Load More" or "Show More" specifically
                        xpath_queries = [
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]"
                        ]
                        
                        for xpath in xpath_queries:
                            load_more = page.query_selector(f"xpath={xpath}")
                            if load_more and load_more.is_visible():
                                break

                    if load_more and load_more.is_visible():
                        logger.info(f"Clicking 'Load More' button: {load_more.inner_text()}")
                        load_more.click()
                        time.sleep(3) # Wait for load
                        clicked_load_more = True
                        no_change_count = 0
                except Exception as e:
                    logger.warning(f"Error checking load more: {e}")

                if clicked_load_more:
                    continue

                # If no button, try scrolling
                # Targeted scroll for PowerToFly's container
                # Incremental scroll to simulate user behavior
                scroll_info = page.evaluate("""async () => {
                    const scrollContainer = document.querySelector('.element-scroll');
                    
                    if (scrollContainer) {
                        const startHeight = scrollContainer.scrollHeight;
                        const startTop = scrollContainer.scrollTop;
                        const targetTop = scrollContainer.scrollHeight;
                        const step = 200;
                        
                        // Scroll down in steps
                        for (let i = startTop; i < targetTop; i += step) {
                            scrollContainer.scrollTop = i;
                            // Wait a tiny bit between steps
                            await new Promise(r => setTimeout(r, 50));
                        }
                        
                        // Ensure we hit the bottom
                        scrollContainer.scrollTop = targetTop;
                        scrollContainer.dispatchEvent(new Event('scroll'));
                        
                        return {
                            found: true,
                            startHeight: startHeight,
                            startTop: startTop,
                            endTop: scrollContainer.scrollTop
                        };
                    }
                    
                    // Fallback to window
                    const startHeight = document.body.scrollHeight;
                    window.scrollTo(0, document.body.scrollHeight);
                    return {
                        found: false,
                        startHeight: startHeight
                    };
                }""")
                
                logger.warning(f"Scroll action: {scroll_info}")
                time.sleep(5) # Wait for content load
                
                # Check for end
                new_height = page.evaluate("""() => {
                    const el = document.querySelector('.element-scroll') || document.body;
                    return el.scrollHeight;
                }""")
                
                logger.warning(f"Scroll height: {last_height} -> {new_height} (Jobs: {len(jobs)})")
                
                if new_height == last_height and not new_jobs_batch:
                    no_change_count += 1
                    if no_change_count >= 3:
                        logger.info("Reached end of list (no height change and no new jobs)")
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
            
            logger.info(f"Finished scrolling. Total jobs: {len(jobs)}. Now fetching details...")
            
            # Now fetch details for each job
            # Use requests for faster fetching since content is SSR
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Parallel fetching using ThreadPoolExecutor for speed
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def fetch_detail(job):
                link = job.get('link')
                if not link or link == url:
                    return None
                
                # Ensure absolute URL
                if link.startswith("/"):
                    link = f"https://powertofly.com{link}"
                
                try:
                    # Use Session with Retries for stability
                    with requests.Session() as session:
                        from requests.adapters import HTTPAdapter
                        from urllib3.util.retry import Retry
                        
                        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
                        adapter = HTTPAdapter(max_retries=retries)
                        session.mount('http://', adapter)
                        session.mount('https://', adapter)
                        
                        resp = session.get(link, headers=headers, timeout=15)
                        
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "html.parser")
                            desc_el = soup.select_one("#job-description, .job-description, .body, article")
                            if desc_el:
                                description = desc_el.get_text(separator="\n").strip()
                                job["description"] = description
                                return job
                            else:
                                logger.warning(f"No description element found for {link}")
                        else:
                            logger.warning(f"Requests failed for {link} (Status: {resp.status_code})")
                except Exception as req_err:
                    logger.warning(f"Requests exception for {link}: {req_err}")
                return None

            logger.info(f"Fetching details for {len(jobs)} jobs in parallel...")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {executor.submit(fetch_detail, job): job for job in jobs}
                count_updated = 0
                for future in as_completed(future_to_job):
                    updated_job = future.result()
                    if updated_job:
                        count_updated += 1
                        if on_jobs_found:
                            on_jobs_found([updated_job])
                logger.info(f"Updated details for {count_updated}/{len(jobs)} jobs")
            
            # Note: We rely on requests. If requests fails (e.g. 403), we might miss details.
            # But falling back to Playwright for 200+ jobs is too slow.
            # If significant failures occur, we might need a smarter fallback (e.g. check one, if fail, switch strategy).

                    
        except Exception as e:
            logger.error(f"PowerToFly scrape error: {e}")
            
        return jobs

    def _parse_api_job(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to parse raw API job data"""
        try:
            # Adjust these fields based on actual API response structure
            title = item.get("title") or item.get("job_title") or item.get("name")
            company_data = item.get("company") or {}
            company = "Unknown"
            if isinstance(company_data, dict):
                company = company_data.get("name") or company_data.get("title") or "Unknown"
            elif isinstance(company_data, str):
                company = company_data
            
            location = item.get("location") or "Remote"
            if isinstance(location, dict): 
                location = location.get("name") or str(location)

            job_id = item.get("id") or item.get("job_id")
            link = item.get("link") or item.get("url") or item.get("absolute_url")
            
            if not link and job_id:
                link = f"https://powertofly.com/jobs/detail/{job_id}"
                
            if title and link:
                return {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "platform": "PowerToFly",
                    "description": item.get("description") or item.get("body") or "Loading details..."
                }
        except Exception as e:
            logger.warning(f"Error parsing API job item: {e}")
        return None
