from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class InforStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "careers.infor.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Infor: {url}")
        jobs = []
        scraped_links = set()
        self.stats["pages"] = 0
        cookies_handled = False
        max_pages = 4  # Limit to 4 pages as requested by user
        show_more_attempts = 0
        
        try:
            # Add anti-detection headers and stealth args
            # This is handled by Playwright usually, but sometimes extra help is needed
            # We are already in a loop, but let's make sure we wait enough
            
            while True:
                self.stats["pages"] += 1
                
                # Force wait for network idle to ensure content is loaded
                try:
                    # Infor might be blocking headless requests or requires specific headers
                    # Try waiting for a specific XHR request if possible, or just generous timeout
                    page.wait_for_timeout(5000)
                except:
                    pass
                
                # Check if empty body (sometimes happens with strict headless)
                content = page.content()
                if len(content) < 200:
                    logger.warning(f"Empty/Blocked page detected (len={len(content)})! Retrying reload...")
                    # Try going to the page again explicitly
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(8000)

                page.wait_for_timeout(2000) # Give it time to render
                
                # Handle cookie banner if present (improves pagination visibility)
                if not cookies_handled:
                    try:
                        # Wait for cookie banner specifically
                        page.wait_for_selector("#onetrust-accept-btn-handler, button:has-text('Accept All'), button:has-text('Accept all')", timeout=5000)
                        consent_btn = page.query_selector("#onetrust-accept-btn-handler, button:has-text('Accept All'), button:has-text('Accept all'), [aria-label='Accept all cookies']")
                        if consent_btn and consent_btn.is_visible():
                            logger.info("Clicking cookie consent...")
                            consent_btn.click()
                            page.wait_for_timeout(2000)
                            cookies_handled = True
                    except:
                        logger.info("No cookie banner found or timed out")
                        pass
                
                # Wait for job list or share buttons
                try:
                    # Wait for specific job title link pattern
                    page.wait_for_selector('a[href*="/JobDetail/"]', timeout=15000)
                except:
                    logger.warning("Timeout waiting for Infor selectors")
                
                # Debug: Dump counts
                count_share = len(page.query_selector_all(".shareButton"))
                count_list = len(page.query_selector_all(".list__item"))
                count_jobname = len(page.query_selector_all("[data-jobname]"))
                logger.info(f"Debug Infor: Share={count_share}, List={count_list}, JobName={count_jobname}")
                
                # If zero items, take a snapshot to see what's happening
                if count_list == 0 and count_share == 0:
                     # Log HTML structure
                     html_content = page.content()
                     logger.info(f"Page content length: {len(html_content)}")
                     if "Access Denied" in html_content or "Cloudflare" in html_content:
                         logger.error("BLOCKED BY CLOUDFLARE/WAF!")
                     elif "No jobs found" in html_content:
                         logger.info("Page says 'No jobs found'")
                     else:
                         # Log the first 500 chars of body
                         logger.info(f"Body start: {html_content[:500]}")
                
                # If zero list items found, try wait one more time with a very generic selector
                if count_list == 0 and count_share == 0:
                     logger.info("No items found yet, waiting for ANY 'li' or 'div' with class containing 'list'...")
                     try:
                         page.wait_for_selector("li.list__item, div.article--result, li[class*='list__item']", timeout=5000)
                         # Refresh counts
                         count_list = len(page.query_selector_all(".list__item"))
                         logger.info(f"Refreshed count: {count_list}")
                     except:
                         pass

                # Find all job links via Share buttons or direct links
                # Strategy: Look for elements with data-jobname (Share buttons often have this)
                share_btns = page.query_selector_all("[data-jobname]")
                
                page_jobs = []
                # Use a specific list of selectors for Infor job links to avoid missing any
                # Strategy 1: data-jobname attributes
                for btn in share_btns:
                    try:
                        title = btn.get_attribute("data-jobname")
                        href_attr = btn.get_attribute("href")
                        
                        # Extract link from mailto or other share links
                        full_link = None
                        if href_attr and "body=" in href_attr:
                            # Parse URL from body param
                            import urllib.parse
                            # mailto:...?body=URL
                            try:
                                query = urllib.parse.urlparse(href_attr).query
                                params = urllib.parse.parse_qs(query)
                                if "body" in params:
                                    full_link = params["body"][0]
                            except:
                                pass
                        
                        if not full_link and href_attr and href_attr.startswith("http"):
                             full_link = href_attr
                             
                        if not full_link:
                             # Try to find a sibling anchor that looks like a job link
                             # Traverse up to list item
                             li = btn.evaluate_handle("el => el.closest('li.list__item')") # This is the share item
                             # The job item is likely the parent of the ul containing this li, or a sibling
                             # Let's try to find the job title link in the vicinity
                             pass

                        if title and full_link:
                            # Clean up link
                            full_link = full_link.split("?")[0]
                            
                            if full_link in scraped_links:
                                continue
                                
                            job = {
                                "title": title,
                                "company": "Infor",
                                "location": "Unknown", # We'll try to fetch this later
                                "link": full_link,
                                "platform": "Infor"
                            }
                            
                            page_jobs.append(job)
                            jobs.append(job)
                            scraped_links.add(full_link)
                            
                    except Exception as e:
                        continue
                
                # Strategy 2: Direct job links (h3/h4/div > a)
                # This catches jobs that might not have share buttons formatted as expected
                # Or where the previous strategy failed
                if True: # Always run this as backup/augmentation
                    anchors = page.query_selector_all('a[href*="/JobDetail/"]')
                    # Also look for generic anchors inside result items
                    if not anchors:
                        anchors = page.query_selector_all(".article--result a, .list__item a")
                        
                    for a in anchors:
                        try:
                            href = a.get_attribute("href")
                            if not href or "/JobDetail/" not in href:
                                continue
                                
                            title = a.inner_text().strip()
                            
                            if not title or len(title) < 3 or "Share" in title:
                                # Try to get title from child element if text is empty?
                                if not title:
                                     # Sometimes the link wraps a div with the title
                                     title_el = a.query_selector("h3, h4, div.title, span.title")
                                     if title_el:
                                         title = title_el.inner_text().strip()
                                
                            if not title or len(title) < 3 or "Share" in title:
                                # Fallback: if we found a valid job link but no title text
                                # Try to find title in parent container
                                try:
                                    parent_title = a.evaluate("el => el.closest('.list__item').querySelector('h3, h4').innerText")
                                    if parent_title:
                                        title = parent_title.strip()
                                except:
                                    pass
                            
                            if not title or "Share" in title:
                                continue

                            if href.startswith("/"):
                                parsed = urlparse(url)
                                full_link = f"{parsed.scheme}://{parsed.netloc}{href}"
                            else:
                                full_link = href
                                
                            if full_link in scraped_links:
                                continue
                                
                            job = {
                                "title": title,
                                "company": "Infor",
                                "location": "Unknown",
                                "link": full_link,
                                "platform": "Infor"
                            }
                            
                            page_jobs.append(job)
                            jobs.append(job)
                            scraped_links.add(full_link)
                        except Exception:
                            continue
                
                # Strategy 3: List items traversal (most robust for this layout)
                # If we still have few jobs, iterate over .list__item
                if len(page_jobs) < 3:
                     items = page.query_selector_all(".list__item")
                     for item in items:
                         try:
                             # Try to find the link inside
                             link_el = item.query_selector("a[href*='/JobDetail/']")
                             if link_el:
                                 href = link_el.get_attribute("href")
                                 title = link_el.inner_text().strip()
                                 
                                 if not title:
                                     continue
                                     
                                 if href.startswith("/"):
                                     parsed = urlparse(url)
                                     full_link = f"{parsed.scheme}://{parsed.netloc}{href}"
                                 else:
                                     full_link = href
                                     
                                 if full_link in scraped_links:
                                     continue
                                     
                                 job = {
                                    "title": title,
                                    "company": "Infor",
                                    "location": "Unknown",
                                    "link": full_link,
                                    "platform": "Infor"
                                 }
                                 page_jobs.append(job)
                                 jobs.append(job)
                                 scraped_links.add(full_link)
                         except:
                             pass

                
                # Strategy 4: Fallback to searching for ANY link with job-like URL pattern
                if len(page_jobs) == 0:
                     logger.info("Strategy 4: Aggressive fallback for any job links...")
                     # Try to find any link containing 'JobDetail'
                     all_links = page.query_selector_all("a")
                     for a in all_links:
                         try:
                             href = a.get_attribute("href")
                             if href and "/JobDetail/" in href:
                                 # We found a job link!
                                 title = a.inner_text().strip()
                                 if not title:
                                     # Try to find title in parent
                                     try:
                                        title = a.evaluate("el => el.closest('div').innerText").split('\n')[0].strip()
                                     except:
                                        title = "Unknown Job Title"
                                 
                                 if href.startswith("/"):
                                     parsed = urlparse(url)
                                     full_link = f"{parsed.scheme}://{parsed.netloc}{href}"
                                 else:
                                     full_link = href

                                 if full_link in scraped_links:
                                     continue

                                 job = {
                                     "title": title,
                                     "company": "Infor",
                                     "location": "Unknown",
                                     "link": full_link,
                                     "platform": "Infor"
                                 }
                                 page_jobs.append(job)
                                 jobs.append(job)
                                 scraped_links.add(full_link)
                         except:
                             pass
                
                if on_jobs_found and page_jobs:
                    on_jobs_found(page_jobs, stats=self.stats)
                
                # Check page limit
                if self.stats["pages"] >= max_pages:
                    logger.info(f"Reached max pages limit ({max_pages}). Stopping pagination.")
                    break

                # Pagination
                # Inspecting Infor pagination...
                # The "Show More" or "Next" button might be dynamically loaded or named differently
                # Updated: found 'next >>' link in debug, ensure we pick the visible one
                # Selector update based on debug: .paginationNextLink
                next_btn = page.query_selector("a.paginationNextLink:visible, a[aria-label^='Go to Next Page']:visible, a:has-text('Next >>'):visible")
                
                # Fallback: Check for page numbers if Next button not found or not visible
                if not next_btn:
                     # Look for current page and the next number
                     try:
                         # Example: <span class="pagination__item--current">1</span> <a href="...">2</a>
                         current_page_el = page.query_selector(".pagination__item--current, .current-page, span.current")
                         if current_page_el:
                             current_num = int(current_page_el.inner_text().strip())
                             next_num = current_num + 1
                             logger.info(f"Trying to click page {next_num} via number link")
                             next_btn = page.query_selector(f"a:has-text('{next_num}'), a[aria-label='Page {next_num}']")
                     except:
                         pass

                if not next_btn:
                     # Check if there is a "Load More" button
                     next_btn = page.query_selector(".load-more-button, button.load-more, button:has-text('Load more'), button:has-text('Load more results'), a:has-text('Show more results')")
                     
                if next_btn and not next_btn.is_disabled() and next_btn.is_visible():
                    try:
                        tag = next_btn.evaluate("el => el.tagName")
                        href = None
                        if tag == "A":
                            href = next_btn.get_attribute("href")
                        logger.info("Navigating to next page...")
                        if href:
                            if href.startswith("/"):
                                parsed = urlparse(url)
                                full = f"{parsed.scheme}://{parsed.netloc}{href}"
                                page.goto(full, wait_until="domcontentloaded", timeout=45000)
                            else:
                                page.goto(href, wait_until="domcontentloaded", timeout=45000)
                        else:
                            next_btn.click()
                            page.wait_for_timeout(3000)
                        if self.stats["pages"] >= max_pages:
                            logger.info(f"Reached max pages target ({max_pages}).")
                            break
                    except:
                        break
                else:
                    # If no next button, maybe it's infinite scroll?
                    # Let's try scrolling down multiple times to be sure
                    prev_count = len(page.query_selector_all(".list__item, .article--result"))
                    logger.info(f"Scrolling... (Current items: {prev_count})")
                    
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000)
                    
                    # Sometimes we need to scroll a bit up and down to trigger
                    page.evaluate("window.scrollBy(0, -100)")
                    page.wait_for_timeout(500)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    
                    new_count = len(page.query_selector_all(".list__item, .article--result"))
                    if new_count > prev_count:
                        logger.info(f"Scrolled and found more items: {new_count}")
                        continue # Loop again to find new jobs
                    else:
                        logger.info("No more items found after scrolling.")
                        # As a fallback, try clicking any visible 'Show more' once more
                        if show_more_attempts < max_pages:
                            more = page.query_selector("button:has-text('Show More'), a:has-text('Show More'), button:has-text('Load more'), a:has-text('Load more')")
                            if more and more.is_visible():
                                try:
                                    logger.info("Fallback: clicking 'Show More'")
                                    more.click()
                                    page.wait_for_timeout(2000)
                                    show_more_attempts += 1
                                    continue
                                except:
                                    pass
                        break
                    
        except Exception as e:
            logger.error(f"Infor scrape error: {e}")
            
        print(f"DEBUG: INFOR SCRAPE FINISHED LOOP. JOBS COUNT: {len(jobs)}")
        
        # Fetch Details via Playwright (Optimized)
        if jobs:
            print(f"DEBUG: STARTING DETAIL FETCH FOR {len(jobs)} JOBS")
            logger.info(f"Fetching details for {len(jobs)} jobs via Playwright navigation...")
            
            for i, job in enumerate(jobs):
                if job.get("description") and len(job.get("description")) > 100: 
                    continue
                
                # Progress Log
                logger.info(f"[{i+1}/{len(jobs)}] Fetching details for: {job['title']}")
                
                try:
                    # Optimized Navigation
                    try:
                        page.goto(job['link'], wait_until="domcontentloaded", timeout=30000)
                        # Wait for content instead of hard sleep
                        try:
                            page.wait_for_selector(".article__content, .article__header", timeout=5000)
                        except:
                            # Proceed anyway, maybe it loaded fast or different structure
                            pass
                    except Exception as nav_err:
                        logger.warning(f"Navigation error for {job['link']}: {nav_err}")
                        continue
                    
                    desc_text = ""
                    
                    # Strategy 1: Fast Generic Class Search (Most reliable for Infor)
                    try:
                        content_els = page.query_selector_all(".article__content")
                        for el in content_els:
                            txt = el.inner_text()
                            # Skip short or "General Info" blocks
                            if len(txt) > 200 and "Job ID" not in txt[:100]:
                                desc_text = txt
                                break
                    except:
                        pass

                    # Strategy 2: Header Search (Fallback)
                    if not desc_text:
                        try:
                            # Look for header and get parent text
                            header = page.query_selector("h3:has-text('Description & Requirements'), h4:has-text('Description & Requirements')")
                            if header:
                                # Try to get the whole container text
                                container = header.evaluate_handle("el => el.closest('.article, .section') || el.parentElement")
                                if container:
                                    desc_text = container.inner_text()
                        except:
                            pass

                    # Strategy 3: Blind Text Grab (Last Resort)
                    if not desc_text:
                         try:
                             # Grab the largest text block on the page
                             desc_text = page.evaluate("""() => {
                                 let maxLen = 0;
                                 let maxEl = null;
                                 document.querySelectorAll('div, section, article').forEach(el => {
                                     if (el.innerText.length > maxLen && el.innerText.length < 10000) {
                                         maxLen = el.innerText.length;
                                         maxEl = el;
                                     }
                                 });
                                 return maxEl ? maxEl.innerText : "";
                             }""")
                         except:
                             pass
                    
                    if desc_text:
                        job["description"] = desc_text
                        logger.info(f"  -> Success. Length: {len(desc_text)}")
                    else:
                        logger.warning("  -> Failed to extract description.")
                        
                except Exception as e:
                    logger.warning(f"Error fetching details for {job['link']}: {e}")
                    pass
        else:
             logger.info("No jobs to fetch details for.")

        return jobs
