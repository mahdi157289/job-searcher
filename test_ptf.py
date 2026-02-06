from playwright.sync_api import sync_playwright
import logging
from backend.scraper.strategies.powertofly import PowerToFlyStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ptf():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        strategy = PowerToFlyStrategy()
        url = "https://powertofly.com/jobs/?keywords=AI"
        
        def on_jobs(jobs):
            print(f"Streamed {len(jobs)} jobs")
            if jobs:
                print(f"Sample Job: {jobs[0]['title']} - Link: {jobs[0]['link']}")
                desc = jobs[0].get('description', '')
                print(f"Description Start: {desc[:50]}...")
                if desc == "Loading details...":
                    print("WARNING: Description is still placeholder!")

        print("Starting scrape...")
        jobs = strategy.scrape(page, url, on_jobs_found=on_jobs)
        
        print(f"Final count: {len(jobs)}")
        for j in jobs[:3]:
            print(f"Job: {j['title']} - Desc Len: {len(j.get('description', ''))}")
            if j.get('description') == "Loading details...":
                print("  -> Description NOT updated!")

        browser.close()

if __name__ == "__main__":
    test_ptf()
