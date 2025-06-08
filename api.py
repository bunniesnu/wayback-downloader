import requests
from const import WAYBACK_API_ENDPOINT
import time
from tqdm import tqdm

def get_availability(url: str):
    params = {
        "url": f"{url}*",
        "output": "json"
    }
    response = requests.get(WAYBACK_API_ENDPOINT, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
        except:
            raise Exception(f"Error parsing JSON response: {response.text}")
        if len(data) < 2:
            raise Exception(f"No availability data found for {url}")
        entries = data[1:]
        headers = data[0]
        values: list[dict[str, str]] = []
        for entry in entries:
            entry_dict: dict[str, str] = {}
            for i, value in enumerate(entry):
                entry_dict[headers[i]] = value
            values.append(entry_dict)
        return values
    else:
        raise Exception(f"Error fetching availability: {response.status_code} - {response.text}")

def download_website(url: str, timestamp: str, proxy: str | None = None):
    proxies = {
        'http': proxy,
        'https': proxy,
    } if proxy else None
    full_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
    retry = 0
    while retry < 3:
        try:
            response = requests.get(full_url, proxies=proxies)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                tqdm.write(f"404 Not Found for {url} at {timestamp}")
                break
            else:
                retry += 1
                if retry >= 3:
                    tqdm.write(f"Failed to download {url}: {response.status_code}")
                    break
        except Exception as e:
            retry += 1
            if retry >= 3:
                raise e
        time.sleep(10 * retry)
    raise Exception(f"Error downloading website: {url} at {timestamp}")