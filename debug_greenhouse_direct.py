from playwright.sync_api import sync_playwright
from backend.scraper.strategies.greenhouse import GreenhouseStrategy
import logging

logging.basicConfig(level=logging.INFO)

def test_greenhouse():
    url = "https://job-boards.greenhouse.io/rushstreetinteractive?gh_src=57a974504us"
    strategy = GreenhouseStrategy()
    
    print(f"Testing GreenhouseStrategy with URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url) # Explicit goto to ensure load before scrape called (though scrape calls goto usually? No, scrape takes page, caller usually calls goto, but let's check base strategy usage)
        # Wait, the scrape() method in base strategy usually assumes page is ready? 
        # In engine.py: 
        # page.goto(url)
        # strategy.scrape(page, url)
        # So I need to call page.goto(url) here.
        
        # My previous test script didn't call page.goto(url)! 
        # Wait, let me check debug_builtin_direct.py.
        # It calls strategy.scrape(page, url).
        # Does strategy.scrape call goto?
        # Let's check builtin.py.
        
        try:
            # Let's check if scrape calls goto.
            # BaseStrategy: scrape(page, url).
            # BuiltInStrategy: scrape(page, url).
            # If they don't call goto, then my previous test worked because BuiltIn DOES call goto internally?
            # Or did I miss something?
            
            # Checking builtin.py...
            # I don't have it open. But usually strategies might just parse.
            # If BuiltInStrategy iterates pages, it likely calls goto.
            
            # Checking GreenhouseStrategy in previous turn...
            # It DOES NOT call page.goto(url). It starts with page.wait_for_selector.
            # So I MUST call page.goto(url) before calling scrape.
            
            # This explains why Greenhouse returned 0 jobs!
            # And why BuiltIn worked (because BuiltIn iterates pages and calls page.goto inside the loop).
            
            pass
        except:
            pass
            
        try:
            page.goto(url)
            jobs = strategy.scrape(page, url)
            print(f"Total jobs found: {len(jobs)}")
            if jobs:
                print(f"Sample job: {jobs[0]}")
            else:
                # If still 0, dump content
                with open("greenhouse_dump.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Dumped HTML to greenhouse_dump.html")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_greenhouse()
