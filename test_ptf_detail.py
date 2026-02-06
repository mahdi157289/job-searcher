
import requests
from bs4 import BeautifulSoup

def test_detail():
    # First, get the main page to find a job link
    url = "https://powertofly.com/jobs/?keywords=AI"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Fetching main page: {url}")
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch main page: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    # Try to find a job link
    # Selectors from code: .job.box a
    links = []
    for a in soup.select("a"):
        href = a.get("href", "")
        if "/jobs/detail/" in href:
            full_link = f"https://powertofly.com{href}" if href.startswith("/") else href
            links.append(full_link)
            
    print(f"Found {len(links)} job links")
    if not links:
        print("No job links found via requests on main page.")
        return

    job_link = links[0]
    print(f"Testing detail fetch for: {job_link}")
    
    resp = requests.get(job_link, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch detail page: {resp.status_code}")
        return
        
    soup = BeautifulSoup(resp.text, "html.parser")
    # Selectors from code: #job-description, .job-description, .body, article
    desc_el = soup.select_one("#job-description, .job-description, .body, article")
    
    if desc_el:
        desc = desc_el.get_text(separator="\n").strip()
        print(f"SUCCESS: Found description (length: {len(desc)})")
        print("First 200 chars:")
        print(desc[:200])
    else:
        print("FAILURE: Description element not found with current selectors.")
        print("Available classes in body:")
        # print classes of first few divs
        for div in soup.select("div")[:10]:
            print(div.get("class"))

if __name__ == "__main__":
    test_detail()
