import json
from selenium import webdriver
import time
from sys import argv
import requests
from pathlib import Path

if len(argv) < 4:
    print("Usage: python sim.py <timestamp> <url> <local_url> [<proxy>]")
    exit(1)
TIMESTAMP = argv[1]
URL = argv[2]
LOCAL_URL = argv[3]
PROXY = argv[4] if len(argv) > 4 else None

proxies = {
    'http': PROXY,
    'https': PROXY,
} if PROXY else None

def handle_404(url: str):
    endpoint = url.replace(LOCAL_URL, '')
    path = Path("output") / TIMESTAMP / endpoint.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"File {path} already exists, skipping download.")
        return
    retry = 0
    while retry < 3:
        try:
            download_url = f"https://web.archive.org/web/{TIMESTAMP}id_/{URL}{endpoint}"
            response = requests.get(download_url, proxies=proxies)
            if response.status_code == 200 or response.status_code == 206:
                path.write_bytes(response.content)
                print(f"Downloaded {endpoint}")
                break
            elif response.status_code == 404:
                print(f"404 Not Found for {url} at {TIMESTAMP}")
                break
            else:
                retry += 1
                if retry >= 3:
                    print(f"Failed to download {download_url}: {response.status_code}")
                    break
        except Exception as e:
            retry += 1
            if retry >= 3:
                raise e
        time.sleep(10 * retry)

options = webdriver.ChromeOptions() 
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = webdriver.Chrome(options=options)

driver.get(LOCAL_URL)

reload = 0

MAX_RELOADS = 10
WAIT_TIME = 10

try:
    while True:
        try:
            _ = driver.title
        except Exception:
            print("Driver closed, reopening...")
            driver.quit()
            driver = webdriver.Chrome(options=options)
            driver.get(LOCAL_URL)
        cnt = 0
        for entry in driver.get_log('performance'):
            message = json.loads(entry['message'])['message']
            if message.get('method') == 'Network.responseReceived':
                resp = message['params']['response']
                if resp.get('status') == 404:
                    cnt += 1
                    handle_404(resp['url'])
        if cnt == 0:
            if reload >= 3:
                if reload >= MAX_RELOADS:
                    print(f"Reloaded {reload} times, stopping.")
                    break
                print("Loaded all asssets.")
                time.sleep(WAIT_TIME)
                reload += 1
                continue
            print("Loaded all asssets.")
            reload += 1
        else:
            reload = 0
        time.sleep(1)
except KeyboardInterrupt:
    print("Monitoring stopped by user. The last timestamp is:", TIMESTAMP)