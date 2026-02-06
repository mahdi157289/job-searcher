
import requests
from bs4 import BeautifulSoup

url = "https://powertofly.com/jobs/detail/2478182"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Test selectors from the strategy
        selectors = ["#job-description", ".job-description", ".body", "article"]
        found = False
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                print(f"Found description with selector: {sel}")
                print(f"Length: {len(el.get_text())}")
                print("Preview:", el.get_text()[:100])
                found = True
                break
        
        if not found:
            print("No description found with any selector.")
            print("Title:", soup.title.string if soup.title else "No title")
            # Save to file to inspect if needed
            with open("debug_job.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("Saved HTML to debug_job.html")
            
    else:
        print("Failed to fetch.")
        
except Exception as e:
    print(f"Error: {e}")
