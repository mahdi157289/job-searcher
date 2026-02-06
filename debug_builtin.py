
import logging
import sys
import json
import os

# Add backend directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.sync_api import sync_playwright
from scraper.strategies import BuiltInStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_builtin_scraping():
    url = "https://builtin.com/jobs/remote"
    strategy = BuiltInStrategy()
    
    print(f"Testing BuiltInStrategy with {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless=False to see what's happening if needed
        context = browser.new_context()
        page = context.new_page()
        
        try:
            results = strategy.scrape(page, url)
            
            print(f"\nFound {len(results)} jobs.")
            
            # Analyze details coverage
            details_count = 0
            sections_found = {"The Role": 0, "Top Skills": 0, "What We Do": 0, "Why Work With Us": 0, "Description": 0}
            
            for i, job in enumerate(results):
                if i < 3:
                    print(f"\n--- Job: {job.get('title')} at {job.get('company')} ---")
                    print(f"Link: {job.get('link')}")
                    print(f"Location: {job.get('location')}")
                    print(f"Posted: {job.get('posted_at')} ({job.get('age_text')})")
                    # print(f"Raw Block Text (DEBUG): {job.get('_debug_block_text')}") # We need to add this to strategy to see it
                
                details = job.get('details', {})
                if details:
                    details_count += 1
                    if i < 5:
                        print("Details found:")
                        for key, value in details.items():
                            print(f"  - {key}: {len(value)} chars")
                else:
                    if i < 5:
                        print("No details found.")
                
                # Count sections (silently for the rest)
                for key in details.keys():
                     # Normalize key for counting
                    k_norm = key
                    if "role" in key.lower(): k_norm = "The Role"
                    elif "skill" in key.lower(): k_norm = "Top Skills"
                    elif "what we do" in key.lower(): k_norm = "What We Do"
                    elif "why" in key.lower(): k_norm = "Why Work With Us"
                    elif "description" in key.lower(): k_norm = "Description"
                    
                    sections_found[k_norm] = sections_found.get(k_norm, 0) + 1

            if len(results) > 5:
                print(f"\n... and {len(results) - 5} more jobs hidden.")
            
            print(f"\nSummary:")
            print(f"Total Jobs: {len(results)}")
            print(f"Jobs with Details: {details_count}")
            print(f"Sections Breakdown: {json.dumps(sections_found, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error during testing: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # Add backend directory to path so imports work
    sys.path.append('backend')
    test_builtin_scraping()
