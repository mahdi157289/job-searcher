from playwright.sync_api import sync_playwright

def inspect_ashby():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = "https://jobs.ashbyhq.com/The-Flex"
        print(f"Visiting {url}")
        page.goto(url)
        page.wait_for_timeout(5000) # Wait for hydration
        
        # Print some interesting elements
        print("Page Title:", page.title())
        
        # Check for links
        links = page.query_selector_all("a")
        print(f"Total links found: {len(links)}")
        for i, link in enumerate(links[:10]):
            print(f"Link {i}: {link.get_attribute('href')} - {link.inner_text()}")
            
        # Check for potential job containers
        divs = page.query_selector_all("div")
        print(f"Total divs: {len(divs)}")
        
        browser.close()

if __name__ == "__main__":
    inspect_ashby()
