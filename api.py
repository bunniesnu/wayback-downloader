import requests
from const import WAYBACK_API_ENDPOINT
import time
from tqdm import tqdm
from typing import Literal

HEADERS_KEY = Literal["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]

def _base_api_call(*, url: str, params: dict[str, str], proxy: str | None = None):
    proxies = {
        'http': proxy,
        'https': proxy,
    } if proxy else None
    params["output"] = "json"
    response = requests.get(WAYBACK_API_ENDPOINT, params=params, proxies=proxies)
    if response.status_code == 200:
        try:
            data: list[list[str]] = response.json()
        except:
            raise Exception(f"Error parsing JSON response: {response.text}")
        if len(data) < 2:
            raise Exception(f"No availability data found for {url}")
        entries = data[1:]
        headers: list[HEADERS_KEY] = data[0] # type: ignore
        values: list[dict[str, str]] = []
        for entry in entries:
            entry_dict: dict[str, str] = {}
            for i, value in enumerate(entry):
                entry_dict[headers[i]] = value
            values.append(entry_dict)
        values.sort(key=lambda x: int(x["timestamp"]))
        return values
    else:
        raise Exception(f"Error fetching availability: {response.status_code} - {response.text}")

def get_availability(*, url: str, proxy: str | None = None):
    params = {
        "url": f"{url}*",
        "filter": "statuscode:20*",
        "collapse": "digest"
    }
    return _base_api_call(url=url, params=params, proxy=proxy)

def get_files(*, url: str, from_timestamp: str, to_timestamp: str | None = None, proxy: str | None = None):
    params = {
        "url": f"{url}*",
        "filter": "statuscode:20*",
        "collapse": "digest",
        "from": from_timestamp
    }
    if to_timestamp:
        params["to"] = to_timestamp
    return _base_api_call(url=url, params=params, proxy=proxy)

def download_website(*, url: str, timestamp: str, proxy: str | None = None):
    proxies = {
        'http': proxy,
        'https': proxy,
    } if proxy else None
    full_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
    retry = 0
    while retry < 3:
        try:
            response = requests.get(full_url, proxies=proxies)
            if response.status_code >= 200 and response.status_code < 210:
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