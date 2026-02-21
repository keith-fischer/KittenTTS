"""
KittenTTS API client: connects to server.py and sends speech lines for playback.

POST OPTIONS
============

Endpoint: POST /speak

The server accepts speech lines in two formats:

1. JSON body (Content-Type: application/json)
   {
     "line": "Character|speed|text"
   }

2. Plain text body (Content-Type: text/plain)
   Character|speed|text

Speech line format: Character|speed|text
  - Character: Voice name (Bella, Luna, Rosie, Kiki, Jasper, Bruno, Leo)
  - speed: Float, e.g. 1.2 (server adds speed_offset, default 0.2)
  - text: Text to speak

Success response (200): {"ok": true, "message": "Queued"}
Error response (400): {"ok": false, "error": "..."}

Example JSON POST:
  curl -X POST http://127.0.0.1:5001/speak \\
    -H "Content-Type: application/json" \\
    -d '{"line": "Leo|1.2|Hello, this is a test."}'

Example plain text POST:
  curl -X POST http://127.0.0.1:5001/speak \\
    -H "Content-Type: text/plain" \\
    -d "Bella|1.4|Hi there."
"""

import argparse
import os
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    requests = None


def wait_for_server(base_url: str, timeout: float = 30.0) -> bool:
    """Poll /health until server is ready or timeout."""
    for _ in range(int(timeout)):
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def speak(base_url: str, line: str, use_json: bool = True) -> tuple[bool, str]:
    """Send a speech line to the server. Returns (success, message)."""
    if not requests:
        return False, "Install requests: pip install requests"

    url = f"{base_url}/speak"
    if use_json:
        resp = requests.post(url, json={"line": line}, timeout=60)
    else:
        resp = requests.post(url, data=line, headers={"Content-Type": "text/plain"}, timeout=60)

    try:
        data = resp.json()
    except Exception:
        return False, f"Non-JSON response: {resp.status_code}"

    if resp.status_code == 200 and data.get("ok"):
        return True, data.get("message", "Queued")
    return False, data.get("error", f"HTTP {resp.status_code}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KittenTTS client: send speech lines to the server",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5001, help="Server port (5000 often used by macOS AirPlay)")
    parser.add_argument("--start-server", action="store_true", help="Start server.py as subprocess before sending")
    parser.add_argument("--plain", action="store_true", help="Use plain text POST instead of JSON")
    parser.add_argument("--lines", nargs="*", help="Speech lines to send (overrides defaults)")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    if args.start_server:
        if not requests:
            print("Install requests: pip install requests")
            sys.exit(1)
        print("Starting server...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        proc = subprocess.Popen(
            [sys.executable, "server.py", "--host", args.host, "--port", str(args.port)],
            cwd=script_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            if not wait_for_server(base_url):
                print("Server failed to start in time")
                proc.terminate()
                sys.exit(1)
            print("Server ready.")
        except Exception as e:
            proc.terminate()
            raise e

    if not requests:
        print("Install requests: pip install requests")
        sys.exit(1)
    # VOICES_SHE = ["Bella", "Luna", "Rosie", "Kiki"]
    # VOICES_HE = ["Jasper", "Bruno", "Leo"]
    lines = args.lines or [
        "Leo|1.2|Leo, Hello, this is a test from the Kitten TTS client.",
        "Bella|1.4|Bella, Hello, this is a test from the Kitten TTS client.",
        "Jasper|1.3|Jasper, Hello, this is a test from the Kitten TTS client.",
        "Luna|1.2|Luna, Hello, this is a test from the Kitten TTS client.",
        "Kiki|1.0|Kiki, Hello, this is a test from the Kitten TTS client.",
        "Bruno|1.3|Kiki, Hello, this is a test from the Kitten TTS client.",
        "Rosie|1.2|Rosie, Hello, this is a test from the Kitten TTS client.",
    ]

    print(f"\nSending {len(lines)} speech line(s) to {base_url}/speak\n")
    for i, line in enumerate(lines, 1):
        ok, msg = speak(base_url, line, use_json=not args.plain)
        if ok:
            print(f"  [{i}] OK: {line[:50]}{'...' if len(line) > 180 else ''}")
        else:
            print(f"  [{i}] FAIL: {msg}")

    if args.start_server:
        proc.terminate()
        proc.wait()

    print("\nDone.")


if __name__ == "__main__":
    main()
