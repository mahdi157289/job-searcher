
import requests
import json

task_id = "16bf0ead-e74e-4c00-aad0-066a4ea7e951"
url = f"http://127.0.0.1:5000/api/scrape/status/{task_id}"

try:
    resp = requests.get(url)
    data = resp.json()
    
    jobs = []
    if data.get("results"):
        for res in data["results"]:
            if res.get("jobs"):
                jobs.extend(res["jobs"])
                
    print(f"Total jobs: {len(jobs)}")
    
    with_desc = [j for j in jobs if j.get("description")]
    print(f"Jobs with description: {len(with_desc)}")
    
    if with_desc:
        print("First description preview:")
        print(with_desc[0]["description"][:100])
        print("Link:", with_desc[0]["link"])
    else:
        print("No descriptions found.")
        
    # Check for "Loading details..."
    loading = [j for j in jobs if j.get("description") == "Loading details..."]
    print(f"Jobs with 'Loading details...': {len(loading)}")

except Exception as e:
    print(f"Error: {e}")
