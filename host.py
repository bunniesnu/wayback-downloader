import socketserver
import os
from pathlib import Path

import http.server

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

timestamp = input("Enter timestamp (YYYYMMDDHHMMSS): ")
output_dir = input("Enter output directory (default: 'output'): ") or "output"
if not timestamp:
    raise ValueError("Timestamp cannot be empty.")
os.chdir(Path(output_dir) / timestamp)
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving HTTP on port {PORT} (http://localhost:{PORT}/) ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        httpd.server_close()