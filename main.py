if __name__ == "__main__":
    from sys import argv
    if len(argv) != 3:
        print("Usage: python main.py <url> <output_directory> [<proxy>]")
        exit(1)
    from pathlib import Path
    from api import get_availability, download_website
    url = argv[1]
    proxy = argv[3] if len(argv) > 3 else None
    if url.startswith("http://") or url.startswith("https://"):
        url = url.split("://")[1]
    print(f"Fetching availability for {url}")
    data = get_availability(url)
    cnt = 0
    for target in data:
        if target["statuscode"] == "200":
            cnt += 1
    print(f"Found {cnt} entries for {url}")
    for target in data:
        if target["statuscode"] != "200":
            continue
        print(f"Downloading {target['timestamp']} for {url}")
        file = Path(argv[2]) / target["timestamp"] / "index.html"
        file.parent.mkdir(parents=True, exist_ok=True)
        if file.exists():
            print(f"File {file} already exists, skipping download.")
            continue
        file.write_bytes(download_website(url, target["timestamp"], proxy))