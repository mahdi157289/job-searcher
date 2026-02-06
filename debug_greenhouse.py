from playwright.sync_api import sync_playwright
from backend.scraper.strategies.greenhouse import GreenhouseStrategy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_greenhouse():
    # Test URL from job platforms.txt
    url = "https://job-boards.greenhouse.io/rushstreetinteractive?gh_src=57a974504us"
    
    print(f"Testing Greenhouse Strategy with: {url}")
    
    strategy = GreenhouseStrategy()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Navigating to URL...")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("Navigation complete.")
            jobs = strategy.scrape(page, url)
            
            print(f"\nTotal Jobs Found: {len(jobs)}")
            if jobs:
                print("\nFirst 3 Jobs:")
                for job in jobs[:3]:
                    print(f"Title: {job['title']}")
                    print(f"Location: {job['location']}")
                    print(f"Link: {job['link']}")
                    print(f"Desc Length: {len(job.get('description', ''))}")
                    print("-" * 30)
            else:
                print("No jobs found. Inspecting page content...")
                print(page.content()[:1000])
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_greenhouse()
