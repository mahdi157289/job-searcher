from playwright.sync_api import sync_playwright
import logging

def deep_debug():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    print(f"--- Deep Debug Infor: {url} ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Check list items
            items = page.query_selector_all(".list__item")
            print(f"List items found: {len(items)}")
            
            if items:
                print("\n--- Inspecting first 3 list items ---")
                for i, item in enumerate(items[:3]):
                    print(f"\nItem {i+1}:")
                    print(f"Text: {item.inner_text()[:100]}...")
                    # Check for links
                    links = item.query_selector_all("a")
                    print(f"Links count: {len(links)}")
                    for a in links:
                        print(f" - HREF: {a.get_attribute('href')}")
                        print(f" - Text: {a.inner_text()}")
            
            print("\n--- Searching for Pagination/Next Buttons ---")
            # Dump all buttons and likely pagination links
            candidates = page.query_selector_all("button, a.pagination__next, .pagination a")
            print(f"Potential candidates: {len(candidates)}")
            for c in candidates:
                txt = c.inner_text().strip()
                tag = c.evaluate("el => el.tagName")
                cls = c.get_attribute("class")
                if txt or "next" in str(cls).lower():
                    print(f"[{tag}] Text: '{txt}', Class: '{cls}'")

            # Check for 'Next' text specifically
            print("\n--- Text Search for 'Next' ---")
            next_texts = page.query_selector_all("text=Next")
            print(f"Elements with text 'Next': {len(next_texts)}")
            for i, el in enumerate(next_texts):
                print(f"Next Element {i+1}:")
                print(f"  Tag: {el.evaluate('el => el.tagName')}")
                print(f"  Visible: {el.is_visible()}")
                print(f"  OuterHTML: {el.evaluate('el => el.outerHTML')}")
                print(f"  Parent Class: {el.evaluate('el => el.parentElement.className')}")

            # Check for Page Numbers
            print("\n--- Page Numbers ---")
            page_nums = page.query_selector_all(".pagination__item, .pagination a")
            print(f"Pagination items: {len(page_nums)}")
            for p_el in page_nums:
                 print(f"  Text: {p_el.inner_text()}, HREF: {p_el.get_attribute('href')}")
                 
            # Check Job Cards Count (approx)
            print("\n--- Job Cards Count ---")
            # Assuming 'article' or similar holds the job
            articles = page.query_selector_all("article, .article, .job-card, .result-item")
            print(f"Articles/Cards found: {len(articles)}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    deep_debug()
