from typing import List, Dict, Any
from playwright.sync_api import Page
import logging
import re
from urllib.parse import urlparse
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class BuiltInStrategy(BaseStrategy):
    def can_handle(self, url: str) -> bool:
        return "builtin.com" in url

    def scrape(self, page: Page, url: str, on_jobs_found=None) -> List[Dict[str, Any]]:
        logger.info(f"Scraping BuiltIn: {url}")
        jobs: List[Dict[str, Any]] = []
        api_jobs: List[Dict[str, Any]] = []
        scraped_links = set()
        
        last_count = 0
        last_api_count = 0

        def parse_json(obj, base_url: str):
            try:
                if isinstance(obj, dict):
                    title = None
                    company = None
                    href = None
                    posted_at = None
                    posted_text = None
                    
                    def _details_from_obj(o):
                        d = {}
                        try:
                            for kk, vv in o.items():
                                kl = str(kk).lower()
                                if isinstance(vv, str):
                                    tx = re.sub(r'\s+', ' ', vv.strip())
                                    if not tx:
                                        continue
                                    if 'role' in kl and len(tx) > 30:
                                        d.setdefault('the role', tx[:1200])
                                    elif 'skill' in kl and len(tx) > 10:
                                        d.setdefault('top skills', tx[:1200])
                                    elif ('what we do' in kl or 'mission' in kl or 'about' in kl) and len(tx) > 30:
                                        d.setdefault('what we do', tx[:1200])
                                    elif ('why work' in kl or 'why join' in kl or 'why us' in kl) and len(tx) > 30:
                                        d.setdefault('why work with us', tx[:1200])
                                    elif 'description' in kl and len(tx) > 30:
                                        d.setdefault('description', tx[:1200])
                                elif isinstance(vv, list):
                                    try:
                                        joined = ' • '.join([str(x).strip() for x in vv if isinstance(x, str) and x.strip()])
                                        if joined:
                                            if 'skill' in kl:
                                                d.setdefault('top skills', joined[:1200])
                                            elif 'role' in kl:
                                                d.setdefault('the role', joined[:1200])
                                            elif 'why' in kl:
                                                d.setdefault('why work with us', joined[:1200])
                                            elif 'about' in kl or 'mission' in kl:
                                                d.setdefault('what we do', joined[:1200])
                                    except Exception:
                                        pass
                            for v in o.values():
                                if isinstance(v, dict):
                                    dd = _details_from_obj(v)
                                    for k2, v2 in dd.items():
                                        d.setdefault(k2, v2)
                                elif isinstance(v, list):
                                    for it in v:
                                        if isinstance(it, dict):
                                            dd = _details_from_obj(it)
                                            for k2, v2 in dd.items():
                                                d.setdefault(k2, v2)
                        except Exception:
                            pass
                        return d

                    if "title" in obj and isinstance(obj["title"], str):
                        title = obj["title"].strip()
                    if "companyName" in obj and isinstance(obj["companyName"], str):
                        company = obj["companyName"].strip()
                    if "hiringOrganization" in obj and isinstance(obj["hiringOrganization"], dict):
                        n = obj["hiringOrganization"].get("name")
                        if isinstance(n, str) and n.strip():
                            company = n.strip()
                    if "datePosted" in obj and isinstance(obj["datePosted"], str):
                        ds = obj["datePosted"].strip().replace("Z", "+00:00")
                        try:
                            if re.match(r'^\d{4}-\d{2}-\d{2}', ds):
                                posted_at = datetime.fromisoformat(ds[:10])
                        except Exception:
                            posted_at = None
                    for key in ("postedAt", "publishedAt", "publication_date", "publicationDate", "created_at", "createdAt"):
                        if key in obj and isinstance(obj[key], str):
                            ds = obj[key].strip().replace("Z", "+00:00")
                            try:
                                if re.match(r'^\d{4}-\d{2}-\d{2}', ds):
                                    posted_at = datetime.fromisoformat(ds[:10])
                            except Exception:
                                posted_at = None
                    for key in ("timeAgo", "posted", "age_text"):
                        if key in obj and isinstance(obj[key], str):
                            posted_text = obj[key].strip()
                    for k in ("url", "link", "jobUrl"):
                        v = obj.get(k)
                        if isinstance(v, str) and v.strip():
                            href = v.strip()
                            break
                    if not href:
                        for k in ("permalink", "canonical_url", "path"):
                            v = obj.get(k)
                            if isinstance(v, str) and v.strip():
                                href = v.strip()
                                break
                    
                    if title and (company or href):
                        if href and not href.startswith("http") and href.startswith("/"):
                            parsed = urlparse(base_url)
                            href = f"{parsed.scheme}://{parsed.netloc}{href}"
                        
                        if href not in scraped_links:
                            item = {
                                "title": title[:120],
                                "company": company or "Unknown",
                                "location": "Unknown",
                                "link": href or base_url,
                                "platform": "BuiltIn",
                                "description": ""
                            }
                            if posted_at:
                                item["posted_at"] = posted_at
                            if posted_text:
                                item["age_text"] = posted_text
                            try:
                                det = _details_from_obj(obj)
                                if det:
                                    item["details"] = det
                                    # Construct description from details
                                    desc_parts = []
                                    for k, v in det.items():
                                        desc_parts.append(f"{k.title()}:\n{v}")
                                    if desc_parts:
                                        item["description"] = "\n\n".join(desc_parts)
                            except Exception:
                                pass
                            
                            api_jobs.append(item)
                            scraped_links.add(href)
                            
                            # Stream immediately
                            if on_jobs_found:
                                on_jobs_found([item], stats=self.stats)

                    for v in obj.values():
                        parse_json(v, base_url)
                elif isinstance(obj, list):
                    for it in obj:
                        parse_json(it, base_url)
            except Exception:
                pass

        def on_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                if "application/json" in ct:
                    j = resp.json()
                    parse_json(j, url)
            except Exception:
                pass
        
        page.on("response", on_response)
        
        try:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            # Generate pages 1 to 8 to retrieve ~160 jobs
            pages = [url]
            try:
                for i in range(2, 9):
                    sep = "&" if "?" in url else "?"
                    pages.append(f"{url}{sep}page={i}")
                self.stats["pages"] = len(pages)
            except Exception:
                pages = [url]
                self.stats["pages"] = 1
            
            self.stats["pages"] = 0
            
            seen_on_page: set = set()
            
            for i, pu in enumerate(pages):
                self.stats["pages"] = i + 1
                logger.debug(f"Navigating to list page {pu}")
                try:
                    page.goto(pu, timeout=40000, wait_until="domcontentloaded")
                    try:
                        for _ in range(3):
                            page.wait_for_timeout(600)
                            page.evaluate("window.scrollBy(0, document.body.scrollHeight/3)")
                        page.wait_for_selector('a[href^="/job/"]', timeout=20000)
                    except:
                        pass
                    
                    anchors = page.query_selector_all('a[href^="/job/"]')
                    logger.info(f"Found {len(anchors)} job links on {pu}")
        
                    current_page_jobs = []
                    for a in anchors:
                        try:
                            href = a.get_attribute("href") or ""
                            if not href or "auth/login" in href:
                                continue
                            full_link = href if href.startswith("http") else f"{base}{href}"
                            
                            if full_link in scraped_links:
                                continue
                            
                            title = a.inner_text().strip()
                            if not title or len(title) < 3:
                                continue
                            
                            # Extract basic info from card
                            company = "Unknown"
                            location_val = "Unknown"
                            
                            try:
                                # Improved company extraction
                                company_text = a.evaluate("""(el) => {
                                    const card = el.closest('div[id^="job-card"], div.job-item, li, article');
                                    if (card) {
                                        const co = card.querySelector('[data-id="company-title"], .company-title, .job-company, a[href*="/company/"]');
                                        if (co) return co.innerText.trim();
                                    }
                                    return '';
                                }""")
                                
                                if company_text and len(company_text) > 1:
                                    company = company_text

                                # Improved block text extraction for Location & Time
                                block_text = a.evaluate("""(el) => {
                                    const card = el.closest('div[id^="job-card"], div.job-item, li, article');
                                    return card ? card.innerText : '';
                                }""")
                                
                                pt = None
                                if block_text:
                                    lines = [l.strip() for l in block_text.split('\n') if l.strip()]
                                    
                                    # 1. Find Age
                                    age_idx = -1
                                    for i, line in enumerate(lines):
                                        if re.search(r'\\b(ago|today|yesterday|just posted)\\b', line, re.IGNORECASE):
                                            pt = line
                                            age_idx = i
                                            break
                                    
                                    # 2. Find Location
                                    if age_idx != -1 and age_idx + 1 < len(lines):
                                        loc_candidates = []
                                        for i in range(age_idx + 1, len(lines)):
                                            line = lines[i]
                                            if "easy apply" in line.lower(): continue
                                            if re.search(r'\\d+K-\\d+K', line, re.IGNORECASE): continue
                                            if any(x in line.lower() for x in ("level", "junior", "senior", "mid", "experienced")): continue
                                            loc_candidates.append(line)
                                        
                                        if loc_candidates:
                                            location_val = " | ".join(loc_candidates)

                                    if not pt:
                                         mt = re.search(r'(\\d+)\\s*(minute|minutes|hour|hours|day|days)\\s*ago', block_text, re.IGNORECASE)
                                         if mt:
                                             pt = mt.group(0)
                                         else:
                                             for kw in ("just posted", "today", "yesterday"):
                                                 if kw in block_text.lower():
                                                     pt = kw
                                                     break
                            except:
                                pass
                            
                            job = {
                                "title": title[:120],
                                "company": company,
                                "location": location_val,
                                "link": full_link,
                                "platform": "BuiltIn",
                                "description": ""
                            }
                            
                            if pt:
                                job["age_text"] = pt
                            
                            current_page_jobs.append(job)
                            jobs.append(job)
                            scraped_links.add(full_link)
                            
                        except Exception as e:
                            logger.error(f"Error processing anchor: {e}")

                    # Stream found jobs immediately
                    if on_jobs_found and current_page_jobs:
                        on_jobs_found(current_page_jobs)
                    
                    # Now fetch details for these jobs using Requests (faster) or Playwright (fallback)
                    # We do this after streaming the basic list so the UI updates
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    
                    # We will handle detail fetching for ALL jobs at the end, not just current page
                    # to ensure API jobs are also covered.
                    pass 
                            
                except Exception as e:
                    logger.error(f"Error processing page {pu}: {e}")
                    
        except Exception as e:
            logger.error(f"BuiltIn scrape error: {e}")
            
        # Merge API jobs and DOM jobs
        all_jobs = jobs + api_jobs
        # Deduplicate by link
        unique_jobs = []
        seen_links = set()
        for j in all_jobs:
            if j['link'] not in seen_links:
                unique_jobs.append(j)
                seen_links.add(j['link'])

        # Parallel detail fetching for jobs without description
        jobs_to_fetch = [j for j in unique_jobs if not j.get('description')]
        if jobs_to_fetch:
            logger.info(f"Fetching details for {len(jobs_to_fetch)} jobs...")
            import concurrent.futures
            
            def fetch_details(job):
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    resp = requests.get(job['link'], headers=headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        
                        # 1. Try JSON-LD (Most reliable)
                        scripts = soup.find_all("script", type="application/ld+json")
                        for s in scripts:
                            try:
                                data = json.loads(s.string)
                                graph = data.get("@graph", []) if isinstance(data, dict) else (data if isinstance(data, list) else [data])
                                for item in graph:
                                    if item.get("@type") == "JobPosting":
                                        desc = item.get("description")
                                        if desc:
                                            # Clean HTML tags if needed, or keep them if frontend renders HTML
                                            # The sample had <br> tags. Let's keep basic formatting or convert to text.
                                            # For now, let's strip HTML for consistency with other scrapers, 
                                            # or use a simple converter.
                                            clean_desc = BeautifulSoup(desc, "html.parser").get_text(separator="\n\n")
                                            return clean_desc
                            except:
                                pass
                                
                        # 2. Try generic selectors (Fallback)
                        desc_el = soup.select_one("div[class*='description'], .job-description, .job-info, #job-description")
                        if desc_el:
                             # Check if it's the generic "fit analysis" text
                            text = desc_el.get_text(separator="\n").strip()
                            if len(text) > 200: # Threshold to avoid short banners
                                return text
                                
                except Exception as e:
                    pass
                return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_job = {executor.submit(fetch_details, job): job for job in jobs_to_fetch}
                for future in concurrent.futures.as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        desc = future.result()
                        if desc:
                            job['description'] = desc
                            # Stream update
                            if on_jobs_found:
                                on_jobs_found([job])
                    except Exception:
                        pass
                
        return unique_jobs
