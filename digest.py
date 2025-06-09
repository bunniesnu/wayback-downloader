from hashlib import sha1
from base64 import b32encode
from pathlib import Path

def cdx_digest(file_path: str):
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    body_bytes = file.read_bytes()
    return b32encode(sha1(body_bytes).digest()).decode('ascii').rstrip('=')