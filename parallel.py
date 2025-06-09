from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from api import HEADERS_KEY, download_website
import os

DEFAULT_WORKERS = min(32, (os.cpu_count() or 1) * 4)

def _download_target(target: dict[HEADERS_KEY, str], digest_dir: Path, proxy: str | None = None):
    filename = target["digest"]
    file = digest_dir / filename
    file.parent.mkdir(parents=True, exist_ok=True)
    if file.exists():
        return target, False
    download_url = target["original"]
    file.write_bytes(download_website(url=download_url, timestamp=target["timestamp"], proxy=proxy))
    return target, True

def download_all(data: list[dict[HEADERS_KEY, str]], digest_dir: Path, proxy: str | None = None, max_workers: int | None = None):
    if max_workers is None:
        max_workers = DEFAULT_WORKERS
    to_download = [t for t in data if (not (digest_dir / t["digest"]).exists())]
    print(f"{len(data) - len(to_download)} files already present, {len(to_download)} to download")
    pbar = tqdm(total=len(to_download), desc="Downloading files")
    results: list[tuple[dict[HEADERS_KEY, str], bool]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_download_target, t, digest_dir, proxy): t
            for t in to_download
        }
        for future in as_completed(future_map):
            target, did_download = future.result()
            if did_download:
                tqdm.write(f"Downloaded {target['digest']}")
                pbar.update(1)
            else:
                pbar.update(1)
            results.append((target, did_download))

    pbar.close()
    return results