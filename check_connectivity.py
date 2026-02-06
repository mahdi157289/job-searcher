import requests

def check(url):
    try:
        print(f"Checking {url}...")
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check("https://www.linedata.com")
    check("https://jobs.ashbyhq.com")
