from playwright.sync_api import sync_playwright
import logging

def debug_pagination():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    print(f"Navigating to {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        # 1. Accept Cookies
        try:
            consent_btn = page.query_selector("button:has-text('Accept All'), button:has-text('Accept all'), [aria-label='Accept all cookies']")
            if consent_btn:
                print("Found cookie button, clicking...")
                consent_btn.click()
                page.wait_for_timeout(1000)
        except:
            pass

        # 2. Count jobs on page 1
        jobs_visual = page.query_selector_all(".list__item, .article--result")
        print(f"Visual Items (.list__item): {len(jobs_visual)}")
        
        share_btns = page.query_selector_all("[data-jobname]")
        print(f"Share Buttons ([data-jobname]): {len(share_btns)}")
        
        links = page.query_selector_all('a[href*="/JobDetail/"]')
        print(f"Job Links (a[href*='/JobDetail/']): {len(links)}")
        
        # Check if we have a mismatch
        if len(links) < len(jobs_visual):
            print("WARNING: Fewer links than visual items. Selectors might be missing some jobs.")
            print("\n--- Inspecting Visual Items (First 5) ---")
            for i, item in enumerate(jobs_visual[:5]):
                print(f"Item {i}:")
                # Try to find any anchor
                anchors = item.query_selector_all("a")
                for a in anchors:
                    href = a.get_attribute("href")
                    text = a.inner_text().strip()
                    print(f"  Anchor: Text='{text}', Href='{href}'")
            
        # 3. Look for Pagination controls
        print("\n--- Inspecting Pagination & Footer ---")
        
        # Look for "Showing X of Y" text
        texts = page.evaluate("() => document.body.innerText")
        import re
        matches = re.findall(r"Showing \d+ of \d+|Results \d+ - \d+", texts, re.IGNORECASE)
        print(f"Count Text Matches: {matches}")
        
        # Dump ALL buttons/links with interesting text
        print("Scanning ALL buttons/links for 'More', 'Next', 'Load'...")
        candidates = page.query_selector_all("button, a")
        for c in candidates:
            try:
                t = c.inner_text().strip().lower()
                if not t: continue
                if any(x in t for x in ["show more", "load more", "next", "view more"]):
                    print(f"POTENTIAL BUTTON: Text='{t}', Tag={c.evaluate('el => el.tagName')}, Visible={c.is_visible()}")
            except:
                pass
                
        # Check for Infinite Scroll again with more aggressive scroll
        print("Attempting aggressive scroll...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        
        # 4. Try specific selectors from code
        selectors = [
            "a:has-text('next >>'):visible",
            "a:has-text('next >>')",
            "a:has-text('Next >>')",
            "button.pagination__next", 
            "a.pagination__next", 
            "a[rel='next']", 
            "button:has-text('Next')", 
            "[aria-label='Next']",
            "[aria-label='Next Page']"
        ]
        
        for s in selectors:
            el = page.query_selector(s)
            if el:
                print(f"SELECTOR MATCH '{s}': Visible={el.is_visible()}")
            else:
                print(f"SELECTOR FAIL '{s}'")

        browser.close()

if __name__ == "__main__":
    debug_pagination()
