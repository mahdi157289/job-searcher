from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class GenericStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return True # Fallback

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Generic: {url}")
        jobs = []
        scraped_links = set()
        
        try:
            # Wait for any potential lazy loading
            try:
                # Initial wait
                page.wait_for_timeout(3000)
                
                # Check if we need to scroll more or wait for frames
                if len(page.frames) > 1:
                    logger.info(f"Generic: Detected {len(page.frames)} frames, waiting for them to load...")
                    page.wait_for_timeout(3000)
                
                # Scroll to bottom to trigger lazy load
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
            except:
                pass

            # Try to determine site name
            site_name = "Generic"
            
            # Method 1-3: Page Metadata (Playwright dependent)
            try:
                # 1. Try Open Graph site name
                og_site = page.query_selector("meta[property='og:site_name']")
                if og_site:
                    content = og_site.get_attribute("content")
                    if content:
                        site_name = content.strip()
                
                # 2. Try application-name
                if site_name == "Generic":
                    app_name = page.query_selector("meta[name='application-name']")
                    if app_name:
                        content = app_name.get_attribute("content")
                        if content:
                            site_name = content.strip()

                # 3. Try title (extract suffix after ' - ' or ' | ')
                if site_name == "Generic" or "site d'offres d'emploi" in site_name.lower():
                    title = page.title()
                    if " - " in title:
                        candidate = title.split(" - ")[-1].strip()
                        if "site d'offres d'emploi" not in candidate.lower():
                            site_name = candidate
                    elif " | " in title:
                        candidate = title.split(" | ")[-1].strip()
                        if "site d'offres d'emploi" not in candidate.lower():
                            site_name = candidate
            except Exception as e:
                logger.warning(f"Generic metadata extraction failed: {e}")
                
            # Method 4: Domain Fallback (Robust, no Playwright dependency)
            if site_name == "Generic" or "site d'offres d'emploi" in site_name.lower():
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    if domain.startswith("www."):
                        domain = domain[4:]
                    # Handle subdomain cases like jobs.company.com -> Company
                    parts = domain.split('.')
                    if len(parts) >= 2:
                        if parts[0] in ['jobs', 'careers', 'apply', 'myworkdayjobs']:
                            site_name = parts[1].capitalize()
                        # Handle talent-soft (e.g. bontaz-career.talent-soft.com -> Bontaz-career)
                        elif 'talent-soft' in domain:
                            site_name = parts[0].replace("-career", "").replace("-jobs", "").capitalize()
                        else:
                            site_name = parts[0].capitalize()
                    else:
                        site_name = domain.capitalize()
                except Exception as e:
                    logger.warning(f"Generic domain fallback failed: {e}")

            logger.info(f"Generic: Determined site name as '{site_name}'")

            # Look for common job keywords in links (in all frames)
            all_frames = page.frames
            logger.info(f"Generic: Checking {len(all_frames)} frames")
            
            # Smart wait: if main frame has very few links, wait longer
            try:
                if len(page.query_selector_all("a")) < 5:
                    logger.info("Generic: Few links found, waiting longer for SPA...")
                    page.wait_for_timeout(10000)
            except:
                pass
            
            all_links = []
            for frame in all_frames:
                try:
                    # If it's a child frame (likely a job board iframe), we want to be more inclusive
                    is_child_frame = frame != page.main_frame
                    frame_links = frame.query_selector_all("a")
                    
                    # Store tuple of (link, is_child_frame)
                    for l in frame_links:
                        all_links.append((l, is_child_frame))
                except:
                    pass
            
            # If no frames or links found in frames, fallback to main page
            if not all_links:
                main_links = page.query_selector_all("a")
                for l in main_links:
                    all_links.append((l, False))

            for link, is_from_child_frame in all_links:
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute("href")
                    
                    if not href or len(href) < 2:
                        continue
                        
                    # Debug logging for potential candidates
                    print(f"DEBUG: Processing link: '{text}' -> '{href}'")
                        
                    # Normalize URL
                    full_link = urljoin(url, href)
                    
                    # Filter out self-links, anchors, and non-job pages
                    if full_link == url or full_link.rstrip('/') == url.rstrip('/'):
                        continue
                    if "#" in href and href.startswith("#"): # Internal anchor
                        # Allow SPA routes (e.g. #/jobs/123)
                        if not (href.startswith("#/") or href.startswith("#!/")):
                            continue
                        
                    # Deduplicate
                    if full_link in scraped_links:
                        print(f"DEBUG: Duplicate: {full_link}")
                        continue
                        
                    text_lower = text.lower()
                    href_lower = href.lower()
                    
                    # Heuristics for Job Links
                    is_job = False
                    
                    # If from child frame, it's very likely a job if it has a title
                    if is_from_child_frame and len(text) > 5:
                        print("DEBUG: Match Child Frame Heuristic")
                        is_job = True
                    
                    if not is_job and any(k in text_lower for k in ["apply", "senior", "junior", "engineer", "developer", "manager", "specialist", "consultant", "analyst", "ingenieur", "technicien", "stage", "alternance", "projet", "qualite", "commercial", "ressources"]):
                         print(f"DEBUG: Match Text Keyword: {[k for k in ['apply', 'senior', 'junior', 'engineer', 'developer', 'manager', 'specialist', 'consultant', 'analyst', 'ingenieur', 'technicien', 'stage', 'alternance', 'projet', 'qualite', 'commercial', 'ressources'] if k in text_lower]}")
                         is_job = True
                    
                    if not is_job and any(k in href_lower for k in ["job", "career", "vacancy", "position", "role", "offre", "emploi", "recrutement"]):
                        if not any(k in href_lower for k in ["search", "results", "filter", "category", "tag", "ma-selection", "liste-toutes-offres", "flux-rss"]):
                            print("DEBUG: Match Href Keyword")
                            is_job = True

                    # Special case for known ATS patterns (Workable, Greenhouse, Lever, Ashby, BambooHR, Bullhorn)
                    if any(k in href_lower for k in ["workable.com", "greenhouse.io", "lever.co", "ashbyhq.com", "bamboohr.com", "bullhorn", "recruitee.com"]):
                        if len(text) > 3:
                            print("DEBUG: Match ATS Pattern")
                            is_job = True
                            
                    # 3. Exclude obvious non-jobs
                    if any(k in href_lower for k in ["login", "signin", "signup", "register", "privacy", "terms", "about", "contact", "blog", "news", "events", "cookie", "google", "youtube", "facebook", "twitter", "linkedin", "instagram", "help", "support"]):
                        is_job = False
                        
                    if is_job:
                        print(f"DEBUG: ACCEPTED: {full_link}")
                        # Clean title
                        clean_title = text.replace('\n', ' ').strip()
                        if len(clean_title) < 3: # Too short
                            continue
                        job = {
                            "title": text[:100], 
                            "company": site_name, # Use site name as company fallback if unknown
                            "location": "Unknown",
                            "link": full_link,
                            "platform": site_name,
                            "description": ""
                        }
                        jobs.append(job)
                        scraped_links.add(full_link)
                        
                except Exception:
                    continue
            
            # Fetch descriptions for found jobs
            logger.info(f"Generic: Found {len(jobs)} potential jobs. Fetching details...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            for job in jobs:
                if len(job.get("description", "")) > 50: # Already has description
                    continue

                # 1. Try requests first (faster)
                html_content = None
                try:
                    resp = requests.get(job['link'], headers=headers, timeout=10, verify=False)
                    if resp.status_code == 200:
                        html_content = resp.text
                except Exception:
                    pass

                # 2. Try parsing requests result
                if html_content:
                    try:
                        soup = BeautifulSoup(html_content, "html.parser")
                        desc_text = ""
                        
                        # Meta description
                        meta = soup.find("meta", attrs={"name": "description"})
                        if meta:
                            desc_text = meta.get("content", "").strip()
                            
                        # Content containers
                        selectors = [
                            "[itemprop='description']",
                            ".job-description",
                            "#job-description",
                            ".offer-description",
                            "#offer-description",
                            ".description",
                            "[class*='description']",
                            ".ts-offer-page__block",
                            "[class*='offer-page']",
                            ".job-details",
                            "article",
                            "main",
                            ".content",
                            "#content"
                        ]
                        
                        best_len = 0
                        for sel in selectors:
                            el = soup.select_one(sel)
                            if el:
                                text = el.get_text(separator="\n").strip()
                                if len(text) > best_len and len(text) > 100:
                                    desc_text = text
                                    best_len = len(text)
                                    
                        if desc_text:
                            job["description"] = desc_text
                    except Exception:
                        pass

                # 3. Fallback to Playwright if no description found (either requests failed or parsing failed)
                if not job.get("description"):
                    try:
                        logger.info(f"Falling back to Playwright for {job['link']}")
                        # Use 'load' state to ensure content is ready
                        page.goto(job['link'], timeout=30000, wait_until="load")
                        try:
                            page.wait_for_selector("body", timeout=5000)
                        except:
                            pass
                            
                        html_content = page.content()
                        
                        if html_content:
                            soup = BeautifulSoup(html_content, "html.parser")
                            desc_text = ""
                            
                            # Same parsing logic for Playwright content
                            meta = soup.find("meta", attrs={"name": "description"})
                            if meta:
                                desc_text = meta.get("content", "").strip()
                                
                            selectors = [
                                "[itemprop='description']",
                                ".job-description",
                                "#job-description",
                                ".offer-description",
                                "#offer-description",
                                ".description",
                                 "[class*='description']",
                                 ".ts-offer-page__block",
                                 "[class*='offer-page']",
                                 ".job-details",
                                "article",
                                "main",
                                ".content",
                                "#content"
                            ]
                            
                            best_len = 0
                            for sel in selectors:
                                el = soup.select_one(sel)
                                if el:
                                    text = el.get_text(separator="\n").strip()
                                    if len(text) > best_len and len(text) > 100:
                                        desc_text = text
                                        best_len = len(text)
                                        
                            if desc_text:
                                job["description"] = desc_text
                                
                    except Exception as e:
                        logger.warning(f"Generic Playwright fallback failed for {job['link']}: {e}")
            
            if on_jobs_found and jobs:
                on_jobs_found(jobs)

        except Exception as e:
            logger.error(f"Generic scrape error: {e}")
            
        return jobs[:20] # Return max 20 to avoid garbage
