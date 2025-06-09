if __name__ == "__main__":
    from sys import argv
    from tqdm import tqdm
    import json
    if len(argv) < 3:
        print("Usage: python main.py <url> <output_directory> [<proxy>] [<data_directory>]")
        exit(1)
    from pathlib import Path
    from api import get_availability, get_files, HEADERS_KEY
    from os import listdir
    from digest import cdx_digest
    import requests
    from const import PROXY_TEST_URL, MAX_RETRIES_DOWNLOAD_FILE
    from parallel import download_all
    url = argv[1].split("?")[0].rstrip("/")
    proxy = argv[3] if len(argv) > 3 else None
    try:
        requests.get(PROXY_TEST_URL, proxies={"http": proxy, "https": proxy}, timeout=10) if proxy else None
        print(f"Using proxy: {proxy}" if proxy else "No proxy specified")
    except requests.RequestException as e:
        print(f"Error with proxy {proxy}: {e}")
        exit(1)
    if url.startswith("http://") or url.startswith("https://"):
        url = url.split("://")[1]
    print(f"Fetching availability for {url}")
    data_dir = Path(argv[4] if len(argv) > 4 else "data")
    pre_file = data_dir / "availability.json"
    if pre_file.exists():
        data: list[dict[HEADERS_KEY, str]] = json.loads(pre_file.read_text())
    else:
        data = get_availability(url=url, proxy=proxy)
        pre_file.write_text(json.dumps(data, indent=4))
    cnt = len(data)
    print(f"Found {cnt} entries for {url}")
    timestamps = set(int(target["timestamp"]) for target in data if target["original"].split("://")[1].split("?")[0].rstrip("/") == url)
    print(f"Found {len(timestamps)} unique timestamps for {url}")
    digest_dir = Path(argv[2]) / "digest"
    while True:
        download_results, downloaded_all, remain_num = download_all(data, digest_dir=digest_dir, proxy=proxy, max_retries=MAX_RETRIES_DOWNLOAD_FILE)
        print(f"Downloaded {len(download_results)} files for {url} to {argv[2]}/digest")
        if downloaded_all:
            break
        print(f"{remain_num} files not downloaded. Attempting to download again...")
    print("Checking file digests")
    for filename in listdir(digest_dir):
        file_path = digest_dir / filename
        if not (file_path.exists() and file_path.is_file()):
            raise FileNotFoundError(f"File {file_path} does not exist or is not a file.")
        sample_digest = cdx_digest(str(file_path))
        if sample_digest != filename:
            raise ValueError(f"Digest mismatch for {file_path}: expected {filename}, got {sample_digest}")
    print("All file digests are correct.")
    manifest_dir = Path(argv[2]) / "manifest"
    with tqdm(total=len(timestamps), desc="Generating manifest", ncols=100) as pbar:
        list_of_timestamps = sorted(timestamps)
        for i, timestamp in enumerate(list_of_timestamps):
            timestamp_file = data_dir / f"{timestamp}.json"
            tqdm.write(f"Generating manifest for timestamp {timestamp}")
            if timestamp_file.exists():
                files = json.loads(timestamp_file.read_text())
            else:
                files = get_files(url=url, from_timestamp=str(timestamp), proxy=proxy, to_timestamp=(str(list_of_timestamps[i + 1]) if i < len(timestamps) - 1 else None))
                timestamp_file.write_text(json.dumps(files, indent=4))
            manifest_file = manifest_dir / f"{timestamp}.json"
            manifest_file.parent.mkdir(parents=True, exist_ok=True)
            manifest_data = {}
            for file in files:
                k = file["original"].split(url)[1]
                v = file["digest"]
                manifest_data[k] = v
            manifest_file.write_text(json.dumps(manifest_data, indent=4))
            pbar.update(1)
        pbar.close()
    print(f"Generated manifest files in {argv[2]}/manifest")
    print("Process completed successfully.")