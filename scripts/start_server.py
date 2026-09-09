"""
scripts/start_server.py
One-click launcher: starts FastAPI (uvicorn) + ngrok together.
Run from the FYP root: python scripts/start_server.py
"""
import subprocess
import sys
import os
import time
import signal
import threading
import requests

# Change to project root
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load port from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PORT = int(os.getenv("FASTAPI_PORT", 8000))
PUBLIC_URL = os.getenv("PUBLIC_URL", "")

processes = []


def start_uvicorn():
    """Start the FastAPI server with uvicorn."""
    print(f"\n🚀 Starting FastAPI server on port {PORT}...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0",
         "--port", str(PORT), "--reload"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    processes.append(proc)

    # Stream logs in background thread
    def stream_logs():
        for line in proc.stdout:
            print(f"[FastAPI] {line}", end="")

    t = threading.Thread(target=stream_logs, daemon=True)
    t.start()
    return proc


def wait_for_server(timeout=15):
    """Wait until the FastAPI server is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=1)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_ngrok():
    """Start ngrok tunnel pointing to the FastAPI port."""
    print(f"\n🌐 Starting ngrok tunnel → http://localhost:{PORT}")

    # Check if ngrok is installed
    ngrok_cmd = "ngrok"
    try:
        subprocess.run([ngrok_cmd, "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ngrok not found in PATH.")
        print("   Install from: https://ngrok.com/download")
        print("   Or run: winget install ngrok")
        return None

    proc = subprocess.Popen(
        [ngrok_cmd, "http", str(PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    processes.append(proc)
    time.sleep(3)  # Give ngrok time to establish tunnel

    # Fetch tunnel URL
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        if resp.status_code == 200:
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    url = t.get("public_url", "")
                    print(f"✅ ngrok URL: {url}")
                    return url
    except Exception as e:
        print(f"⚠️  Could not fetch ngrok URL: {e}")
    return None


def cleanup(sig=None, frame=None):
    """Gracefully shut down all processes."""
    print("\n\n🛑 Shutting down...")
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 55)
    print("  FYP Inventory Sync — Server Launcher")
    print("=" * 55)

    # Start FastAPI
    server_proc = start_uvicorn()

    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    if wait_for_server():
        print(f"✅ Server running at: http://localhost:{PORT}")
        print(f"📊 Dashboard: http://localhost:{PORT}/")
        print(f"📚 API Docs:  http://localhost:{PORT}/docs")
    else:
        print("❌ Server failed to start in time")
        cleanup()

    # Start ngrok
    ngrok_url = start_ngrok()
    if ngrok_url:
        print(f"\n🌍 Public URL: {ngrok_url}")
        print(f"📊 Dashboard: {ngrok_url}/")
    else:
        print("\n⚠️  Running locally only (ngrok not started)")

    print("\n" + "=" * 55)
    print("  Press Ctrl+C to stop all services")
    print("=" * 55 + "\n")

    # Keep alive
    try:
        server_proc.wait()
    except KeyboardInterrupt:
        cleanup()
