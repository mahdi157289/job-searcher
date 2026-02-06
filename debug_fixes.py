from playwright.sync_api import sync_playwright
import time
import json

def debug_infor():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    print(f"--- Debugging Infor: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        # Check Pagination
        print("Checking Pagination...")
        # Try different selectors for next button
        next_selectors = [
            "a.pagination__next", 
            "button.pagination__next", 
            "a[aria-label='Next page']", 
            ".pagination .next",
            "li.pagination__item--next a"
        ]
        
        found_next = False
        for sel in next_selectors:
            el = page.query_selector(sel)
            if el:
                print(f"Found Next button with selector: {sel}")
                # Check if visible/enabled
                if el.is_visible():
                    print("Next button is visible")
                else:
                     print("Next button is NOT visible")
                found_next = True
                break
        
        if not found_next:
            print("Next button NOT found with common selectors.")
            # Dump pagination HTML
            pager = page.query_selector(".pagination, .pager, ul[class*='pagination']")
            if pager:
                print(f"Pagination HTML: {pager.inner_html()}")
            else:
                print("No pagination container found.")

        # Check Details Page Structure
        # Click first job to go to details
        print("\nChecking Job Details...")
        job_link = page.query_selector('a[href*="/JobDetail/"]')
        if job_link:
            href = job_link.get_attribute("href")
            print(f"Navigating to job: {href}")
            if href.startswith("/"):
                href = f"https://careers.infor.com{href}"
            
            page.goto(href, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            # Look for "Description & Requirements"
            content = page.content()
            if "Description" in content:
                print("Found 'Description' text in page.")
            if "Requirements" in content:
                 print("Found 'Requirements' text in page.")
                 
            # Try to identify the container
            # Common containers
            containers = [
                ".job-description",
                ".article__content",
                ".description",
                "[itemprop='description']",
                ".jobDetail__description",
                "#job-details"
            ]
            
            for c in containers:
                el = page.query_selector(c)
                if el:
                    print(f"Found description container: {c}")
                    print(f"Text length: {len(el.inner_text())}")
                    break
        else:
            print("No job link found to click.")
            
        browser.close()

def debug_snaphunt():
    url = "https://odixcity.snaphunt.com"
    print(f"\n--- Debugging Snaphunt: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture API
        page.on("response", lambda response: print(f"API Response: {response.url} Status: {response.status}") if "api.snaphunt.com" in response.url and "jobs" in response.url else None)
        
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Scroll down multiple times to trigger pagination
        print("Scrolling...")
        for i in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
        # Check if we can find job details in DOM
        # "View Job" buttons
        btns = page.query_selector_all("text=View Job")
        print(f"Found {len(btns)} 'View Job' buttons after scrolling.")
        
        browser.close()

if __name__ == "__main__":
    # debug_infor()
    debug_snaphunt()
