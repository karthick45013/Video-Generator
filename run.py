"""
Entry point — starts the FastAPI server and opens the browser.
Run: python run.py
"""
import subprocess
import sys
import os
import time
import webbrowser
import threading

PORT = 8000
HOST = "127.0.0.1"
URL  = f"http://{HOST}:{PORT}"

def open_browser():
    time.sleep(2.5)  # Give the server time to start
    webbrowser.open(URL)

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║      Wan2.1 Text-to-Video Generator                  ║
║      Running at: {URL:<34} ║
╚══════════════════════════════════════════════════════╝
⏳  The browser will open automatically in a moment…
⚡  On first launch the model (~5 GB) will be downloaded.
    """)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Change to project root so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start uvicorn
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", HOST,
            "--port", str(PORT),
            "--timeout-keep-alive", "600",   # 10-min keep-alive
            "--timeout-graceful-shutdown", "0",
        ],
        check=True,
    )
