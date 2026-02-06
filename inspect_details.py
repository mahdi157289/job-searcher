from playwright.sync_api import sync_playwright

def inspect_details():
    infor_url = "https://careers.infor.com/en_US/careers/JobDetail/NET-Developer-Senior-AI-integration/18398"
    snaphunt_url = "https://odixcity.snaphunt.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        print("\n=== VERIFYING INFOR FIX ===")
        try:
            page = context.new_page()
            print(f"Navigating to Infor: {infor_url}")
            page.goto(infor_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # Logic from infor.py
            print("Running infor.py logic...")
            header_el = page.get_by_text("Description & Requirements").first
            if header_el.is_visible():
                print("Header found!")
                header_container = header_el.locator("xpath=../..")
                content_div = header_container.locator("xpath=following-sibling::div[contains(@class, 'article__content')]").first
                
                if content_div.is_visible():
                    text = content_div.inner_text()
                    print(f"SUCCESS! Found content sibling. Length: {len(text)}")
                    print(f"Snippet: {text[:100]}...")
                else:
                    print("Sibling NOT found. Falling back to parent...")
                    text = header_el.locator("xpath=../..").inner_text()
                    print(f"Parent Text Length: {len(text)}")
            else:
                print("Header 'Description & Requirements' NOT found.")

        except Exception as e:
            print(f"Infor Error: {e}")

        print("\n=== VERIFYING SNAPHUNT FIX ===")
        try:
            # First, get a valid job link
            page = context.new_page()
            print(f"Navigating to Snaphunt: {snaphunt_url}")
            page.goto(snaphunt_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            view_btns = page.get_by_text("View Job").all()
            if view_btns:
                print(f"Found {len(view_btns)} 'View Job' buttons. Clicking first one...")
                
                # Check if it opens a new page or navigates current
                # We'll try to handle both
                try:
                    with context.expect_page(timeout=5000) as new_page_info:
                        view_btns[0].click()
                    new_page = new_page_info.value
                    print("Opened a NEW page/tab.")
                    target_page = new_page
                except:
                    print("Did NOT open a new page (timeout waiting). Checking current page URL...")
                    target_page = page
                    
                target_page.wait_for_load_state("domcontentloaded")
                target_page.wait_for_timeout(3000)
                print(f"Target Page URL: {target_page.url}")
                
                real_job_url = target_page.url
                
                # Logic from snaphunt.py
                print("Running snaphunt.py logic...")
                
                # 1. API Interception Simulation (we can't easily simulate API here without mocking, but we test DOM)
                
                # 2. DOM Scraping
                header = target_page.get_by_text("Job Description", exact=True).first
                if not header.is_visible():
                        print("Exact match failed, trying case-insensitive...")
                        header = target_page.get_by_text("Job Description", exact=False).first
                
                if header.is_visible():
                    print("Header 'Job Description' found!")
                    container = header.locator("xpath=..")
                    desc_text = container.inner_text()
                    
                    if len(desc_text) < 100:
                        print("Text too short, going up one level...")
                        container = container.locator("xpath=..")
                        desc_text = container.inner_text()
                    
                    print(f"SUCCESS! Found description. Length: {len(desc_text)}")
                    print(f"Snippet: {desc_text[:100]}...")
                else:
                    print("Header 'Job Description' NOT found.")
                    print("Dumping page text snippet:")
                    print(target_page.inner_text("body")[:500])
                    
            else:
                print("No jobs found to test.")

        except Exception as e:
            print(f"Snaphunt Error: {e}")
            import traceback
            traceback.print_exc()
            
        browser.close()

if __name__ == "__main__":
    inspect_details()
