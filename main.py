if __name__ == "__main__":
    from sys import argv
    from tqdm import tqdm
    import json
    if len(argv) < 3:
        print("Usage: python main.py <url> <output_directory> [<proxy>]")
        exit(1)
    from pathlib import Path
    from api import get_availability, download_website
    url = argv[1].split("?")[0].rstrip("/")
    proxy = argv[3] if len(argv) > 3 else None
    if url.startswith("http://") or url.startswith("https://"):
        url = url.split("://")[1]
    print(f"Fetching availability for {url}")
    pre_file = Path("availability.json")
    if pre_file.exists():
        data = json.loads(pre_file.read_text())
    else:
        data = get_availability(url, proxy)
        pre_file.write_text(json.dumps(data, indent=4))
    cnt = len(data)
    print(f"Found {cnt} entries for {url}")
    timestamps = set(int(target["timestamp"]) for target in data if target["original"].split("://")[1].split("?")[0].rstrip("/") == url)
    print(f"Found {len(timestamps)} unique timestamps for {url}")
    with tqdm(total=cnt, desc="Downloading files", ncols=100) as pbar:
        for target in data:
            index_timestamp = max((ts for ts in timestamps if ts <= int(target["timestamp"])), default=None)
            if index_timestamp is None:
                raise Exception(f"No previous timestamp found for {target['timestamp']}")
            index_timestamp = str(index_timestamp)
            filename = target["original"].split("?")[0].split(url)[1].lstrip("/")
            if filename == "":
                filename = "index.html"
            file = Path(argv[2]) / index_timestamp / filename
            file.parent.mkdir(parents=True, exist_ok=True)
            if file.exists():
                pbar.update(1)
                continue
            download_url = (url + "/" + filename) if filename != "index.html" else url
            tqdm.write(f"Downloading @ {index_timestamp} - {download_url}")
            file.write_bytes(download_website(download_url, target["timestamp"], proxy))
            pbar.update(1)