
import logging
import sys
import os

# Add backend directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.sync_api import sync_playwright
from scraper.strategies import AshbyStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ashby_scraping():
    url = "https://jobs.ashbyhq.com/The-Flex"
    
    strategy = AshbyStrategy()
    print(f"Testing AshbyStrategy with {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            print(f"Page Title: {page.title()}")
            
            # Check anchors
            anchors = page.query_selector_all("a")
            print(f"Found {len(anchors)} anchors.")
            
            # Check for specific Ashby classes or structures
            # Often Ashby uses specific paths
            links_with_uuid = 0
            for a in anchors:
                href = a.get_attribute("href")
                if href and "ashbyhq.com" not in href and "/" in href:
                    # print(f" - {href}")
                    if "a19778ae" in href: # Check the one we saw earlier
                        print(f"Sample Job Anchor HTML: {a.inner_html()}")
                        print(f"Sample Job Anchor Text: {a.inner_text()}")
                    pass
            
            results = strategy.scrape(page, url)
            print(f"\nFound {len(results)} jobs for {url}.")
            
            for i, job in enumerate(results):
                if i < 3:
                    print(f"\n--- Job: {job.get('title')} ---")
                    print(f"Company: {job.get('company')}")
                    print(f"Location: {job.get('location')}")
                    print(f"Link: {job.get('link')}")
            
        except Exception as e:
            logger.error(f"Error during testing: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_ashby_scraping()
