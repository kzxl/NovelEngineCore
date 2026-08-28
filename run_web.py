"""Web Studio Launcher for NovelEngineCore."""

import os
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import uvicorn

if __name__ == "__main__":
    port = 8765
    print("=" * 70)
    print(" NOVEL ENGINE CORE - WEB STUDIO SERVER")
    print(f" [+] URL: http://127.0.0.1:{port}")
    print("=" * 70)
    
    # Set PYTHONPATH
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    uvicorn.run("novel_engine.api.server:app", host="127.0.0.1", port=port, log_level="info")
