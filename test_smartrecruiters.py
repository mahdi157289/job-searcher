from playwright.sync_api import sync_playwright
from backend.scraper.strategies.smartrecruiters import SmartRecruitersStrategy
import logging

logging.basicConfig(level=logging.INFO)

def test_smartrecruiters():
    url = "https://careers.smartrecruiters.com/HRSolutions"
    print(f"--- Testing SmartRecruiters Scraper: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        strategy = SmartRecruitersStrategy()
        try:
            print("Navigating...")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            print("Starting scrape...")
            jobs = strategy.scrape(page, url)
            print(f"\n--- SCRAPE RESULTS ---")
            print(f"Total Jobs Found: {len(jobs)}")
            
            if jobs:
                print(f"Sample Job 1: {jobs[0]['title']}")
                print(f"Sample Job Link: {jobs[0]['link']}")
                desc = jobs[0].get('description', '')
                print(f"Sample Description Length: {len(desc)}")
                print(f"Sample Description Preview: {desc[:100]}...")
                
                if len(desc) < 50:
                    print("WARNING: Description is missing or short.")
            else:
                print("No jobs found!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_smartrecruiters()
