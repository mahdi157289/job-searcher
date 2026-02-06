from playwright.sync_api import sync_playwright
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugFast")

def benchmark_detail_fetch():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Get a few links first
        print("Getting job links...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000) 
        
        # Quick scrape of links
        links = []
        anchors = page.query_selector_all('a[href*="/JobDetail/"]')
        seen = set()
        for a in anchors:
            href = a.get_attribute("href")
            if href and href not in seen:
                if href.startswith("/"):
                    href = f"https://careers.infor.com{href}"
                links.append(href)
                seen.add(href)
                if len(links) >= 3: break
        
        print(f"Found {len(links)} links to test.")
        
        # 2. Benchmark Optimized Fetch
        print("\n--- Starting Optimized Fetch ---")
        start_time = time.time()
        
        for i, link in enumerate(links):
            job_start = time.time()
            print(f"[{i+1}/{len(links)}] Navigating to {link}...")
            
            try:
                # OPTIMIZATION 1: Fast navigation
                page.goto(link, wait_until="domcontentloaded", timeout=30000)
                
                # OPTIMIZATION 2: Wait for selector instead of sleep
                # Wait for either the header or the content
                try:
                    page.wait_for_selector(".article__content, .article__header", timeout=5000)
                except:
                    print("  timeout waiting for selector (continuing)")
                
                # OPTIMIZATION 3: Fast extraction
                desc = ""
                # Try generic content first (fastest)
                content_els = page.query_selector_all(".article__content")
                for el in content_els:
                    txt = el.inner_text()
                    if len(txt) > 200 and "Job ID" not in txt[:50]: # Simple heuristic
                        desc = txt
                        break
                
                if not desc:
                    # Fallback to header search
                    header = page.query_selector("h3:has-text('Description & Requirements')")
                    if header:
                        # try sibling
                        desc = page.evaluate("el => el.parentElement.innerText", header)
                
                print(f"  Fetched in {time.time() - job_start:.2f}s. Desc len: {len(desc)}")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        total_time = time.time() - start_time
        print(f"--- Finished in {total_time:.2f}s (Avg: {total_time/len(links):.2f}s/job) ---")
        
        browser.close()

if __name__ == "__main__":
    benchmark_detail_fetch()
