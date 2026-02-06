import requests
import sys

def check_service(name, url, expected_status=200):
    print(f"Checking {name} at {url}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {name} is UP (Status: {response.status_code})")
            return True
        else:
            print(f"❌ {name} returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is DOWN (Connection Error)")
        return False
    except Exception as e:
        print(f"❌ {name} Error: {e}")
        return False

def main():
    backend_ok = check_service("Backend API", "http://127.0.0.1:5000/api/scrape/plan")
    
    # Frontend seems to be on IPv6 loopback [::1]
    frontend_ok = check_service("Frontend UI", "http://localhost:5174/")
    
    if backend_ok and frontend_ok:
        print("\n🚀 System is fully operational!")
    else:
        print("\n⚠️ System has issues.")

if __name__ == "__main__":
    main()
