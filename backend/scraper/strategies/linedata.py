from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class LinedataStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "linedata.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Linedata: {url}")
        jobs: List[Dict[str, Any]] = []
        self.stats["pages"] = 0
        
        try:
            while True:
                self.stats["pages"] += 1
                page_jobs: List[Dict[str, Any]] = []
                
                # Try parsing articles first (new design)
                try:
                    page.wait_for_selector("article", timeout=5000)
                except:
                    pass
                    
                articles = page.query_selector_all("article")
                if articles:
                    for article in articles:
                        try:
                            title_el = article.query_selector("h3, .field--name-title")
                            title = title_el.inner_text().strip() if title_el else "Unknown"
                            
                            link_el = article.query_selector("a")
                            href = link_el.get_attribute("href") if link_el else ""
                            
                            if href and not href.startswith("http"):
                                parsed = urlparse(url)
                                href = f"{parsed.scheme}://{parsed.netloc}{href}"
                            
                            # Location
                            location = "Unknown"
                            # Try specific block selector
                            loc_el = article.query_selector(".block-field-blocknodejob-offerfield-location")
                            if loc_el:
                                location = loc_el.inner_text().strip()
                            else:
                                # Fallback
                                loc_el = article.query_selector(".field--name-field-location .field__item")
                                if loc_el:
                                    location = loc_el.inner_text().strip()
                            
                            if title != "Unknown" and href:
                                job = {
                                    "title": title,
                                    "company": "Linedata",
                                    "location": location,
                                    "link": href,
                                    "platform": "Linedata"
                                }
                                page_jobs.append(job)
                                jobs.append(job)
                        except Exception:
                            continue
                
                if on_jobs_found and page_jobs:
                    on_jobs_found(page_jobs, stats=self.stats)
                
                # Check pagination
                next_el = page.query_selector(".pager__item--next a")
                if next_el and self.stats["pages"] < 100: # Increased safety limit to 100 pages
                    try:
                        next_url = next_el.get_attribute("href")
                        logger.info(f"Navigating to next page: {next_url}")
                        next_el.click()
                        page.wait_for_load_state("domcontentloaded")
                        page.wait_for_timeout(2000)
                    except Exception as e:
                        logger.error(f"Pagination error: {e}")
                        break
                else:
                    break
            
            # If no jobs found via articles (and only 1 page), try legacy/fallback
            if not jobs and self.stats["pages"] == 1:
                anchors = page.query_selector_all('a[href*="/job-offers/"], a[href*="/job-offers"]')
                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                if not anchors:
                    anchors = page.query_selector_all("article a[href]")
                for a in anchors:
                    try:
                        href = a.get_attribute("href") or ""
                        if not href:
                            continue
                        if href.startswith("/"):
                            href = f"{base}{href}"
                        title = a.inner_text().strip()
                        if not title or len(title) < 3 or "Explore our job" in title:
                            continue
                        job = {
                            "title": title[:120],
                            "company": "Linedata",
                            "location": "Unknown",
                            "link": href,
                            "platform": "Linedata"
                        }
                        jobs.append(job)
                    except Exception:
                        continue
                if on_jobs_found and jobs:
                    on_jobs_found(jobs, stats=self.stats)
        except Exception as e:
            logger.error(f"Linedata scrape error: {e}")
            
        # Fetch Details for jobs that don't have descriptions
        # Linedata links redirect to Ceipal (SPA), so we must use Playwright
        if jobs:
            logger.info(f"Fetching details for {len(jobs)} jobs (Ceipal)...")
            for i, job in enumerate(jobs):
                try:
                    # Stream update every 5 jobs or so to keep UI alive
                    if i % 5 == 0 and on_jobs_found:
                         on_jobs_found([], stats=self.stats)
                         
                    url = job["link"]
                    logger.info(f"Visiting {url}")
                    
                    try:
                        # Use the existing page to navigate
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        
                        # Wait for the card content
                        try:
                            page.wait_for_selector(".p-card-content", timeout=5000)
                        except:
                            pass
                        
                        # Handle "Show More" button if present
                        # Look for button with text "Show More" or class .showmore-link
                        try:
                            show_more = page.query_selector("button:has-text('Show More'), .showmore-link button")
                            if show_more and show_more.is_visible():
                                logger.info("Clicking 'Show More' button...")
                                show_more.click()
                                page.wait_for_timeout(1000) # Wait for expansion
                        except Exception as e:
                            logger.warning(f"Error handling Show More button: {e}")

                        # Extract description
                        # Ceipal uses PrimeNG cards. The description is usually in one of them.
                        # We'll grab all text from p-card-content
                        cards = page.query_selector_all(".p-card-content")
                        full_desc = []
                        for card in cards:
                            text = card.inner_text().strip()
                            if text:
                                full_desc.append(text)
                        
                        if full_desc:
                            job["description"] = "\n\n".join(full_desc)
                        else:
                            # Fallback to body text if no cards found
                            job["description"] = page.inner_text()
                            
                        # Update the job in the stream
                        if on_jobs_found:
                            on_jobs_found([job], stats=self.stats)
                            
                    except Exception as nav_err:
                        logger.error(f"Failed to load job page {url}: {nav_err}")
                        
                except Exception as e:
                    logger.error(f"Error fetching details for {job['link']}: {e}")
                    
        return jobs
