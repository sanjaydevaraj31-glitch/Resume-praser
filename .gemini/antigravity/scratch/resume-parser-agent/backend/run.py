"""
Development server runner for Resume Parser Agent.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    try:
        import uvicorn
        print("Starting Resume Parser Agent FastAPI server on http://127.0.0.1:8000 ...")
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    except ImportError:
        print("Uvicorn/FastAPI not installed in current environment.")
        print("To run with full FastAPI backend:")
        print("  pip install -r requirements.txt")
        print("  python run.py")
        print("\nStarting fallback HTTP server for frontend on http://127.0.0.1:8000 ...")
        import http.server
        import socketserver

        frontend_dir = BASE_DIR.parent / "frontend"
        os.chdir(frontend_dir)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("127.0.0.1", 8000), handler) as httpd:
            print(f"Serving frontend from {frontend_dir} on http://127.0.0.1:8000")
            httpd.serve_forever()
