# =====================================================================
# ATLAS PROJECT - MASTER TERMINAL LAUNCHER
# Adaptive Trustworthy Language-Augmented Search
# =====================================================================
import os
import sys
import subprocess
import webbrowser
import time
import socket

def kill_zombie_on_port(port=5000):
    """Kill any zombie process holding the Flask port."""
    print(f"🔍 Checking for zombie processes on port {port}...")
    try:
        # Use netstat to find PIDs on the port (Windows)
        result = subprocess.run(
            ["netstat", "-o", "-n", "-a"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if f"127.0.0.1:{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 0:
                    print(f"   ⚠️ Killing zombie process PID {pid} on port {port}")
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True, timeout=5)
                    time.sleep(1)
    except Exception as e:
        print(f"   (Port check skipped: {e})")

def wait_for_port(port=5000, timeout=20):
    """Wait until Flask binds to the port, with timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.5)
    return False

def main():
    print("=" * 60)
    print("      ATLAS COGNITIVE SYSTEM - MASTER SERVICES LAUNCHER")
    print("=" * 60)
    
    # Locate paths relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_script = os.path.join(current_dir, "backend", "app.py")
    python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")
    frontend_html = os.path.join(current_dir, "frontend", "index.html")
    
    # Check dependencies
    if not os.path.exists(backend_script):
        print(f"❌ LAUNCH ERROR: Could not locate backend/app.py at {backend_script}")
        input("Press Enter to exit...")
        sys.exit(1)
        
    if not os.path.exists(python_exe):
        print(f"⚠️ WARNING: venv environment not detected. Falling back to global python...")
        python_exe = "python"
    
    # Step 0: Kill any zombie processes holding port 5000
    kill_zombie_on_port(5000)
    
    print("🚀 [1/3] Spinning up Flask REST API Service in background thread...")
    try:
        backend_process = subprocess.Popen(
            [python_exe, backend_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
    except Exception as e:
        print(f"❌ LAUNCH ERROR: Failed to start Flask process. {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Step 1: Wait for Flask to actually bind to port 5000
    print("⏳ [2/3] Waiting for Flask to accept connections on port 5000...")
    if wait_for_port(5000, timeout=20):
        print("✅ Flask REST API is now accepting connections.")
    else:
        print("⚠️ WARNING: Flask did not bind within 20 seconds. Opening frontend anyway...")
        print("   (The frontend will auto-reconnect when Flask is ready)")
    
    print("🌐 [3/3] Opening premium browser user dashboard...")
    if os.path.exists(frontend_html):
        abs_front = os.path.abspath(frontend_html)
        webbrowser.open(f"file:///{abs_front}")
    else:
        print("❌ WARNING: Could not find frontend/index.html on local path.")
        
    print("=" * 60)
    print("✨ ATLAS SERVICES FULLY INITIALIZED AND RUNNING!")
    print("   NOTE: ML models may still be loading in the background.")
    print("   Wait for 'ATLAS PIPELINE ACTIVE' in the UI before querying.")
    print("👉 To shut down the services completely, close this window.")
    print("=" * 60)
    
    try:
        # Keep launcher running to track process
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_process.terminate()

if __name__ == "__main__":
    main()
