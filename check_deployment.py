import requests
import time

def check_site(url):
    try:
        response = requests.get(url, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Site is up and running!")
        else:
            print(f"Site returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to site: {e}")

if __name__ == "__main__":
    url = "https://mandtrack.onrender.com/"
    print(f"Checking deployment status for {url}")
    
    # Try a few times with delays
    for i in range(3):
        print(f"\nAttempt {i+1}:")
        check_site(url)
        if i < 2:  # Don't sleep after the last attempt
            print("Waiting 5 seconds before next attempt...")
            time.sleep(5)
