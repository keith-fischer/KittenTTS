"""
KittenTTS Flask API server: accepts POST requests with speech lines (Character|speed|text)
and queues them for playback using the shared Speech class.
"""

import argparse
from flask import Flask, request, jsonify

from speech import Speech

app = Flask(__name__)
speech: Speech | None = None


def get_speech() -> Speech:
    """Lazy-init the Speech instance on first request."""
    global speech
    if speech is None:
        raise RuntimeError("Speech not initialized. Call init_speech() at startup.")
    return speech


@app.route("/speak", methods=["POST"])
def speak() -> tuple[dict, int]:
    """
    Accept a speech line. Body: plain text or JSON with 'line' key.
    Format: Character|speed|text
    """
    s = get_speech()

    if request.is_json:
        data = request.get_json()
        line = data.get("line", "")
    else:
        line = request.get_data(as_text=True)

    line = (line or "").strip()
    if not line:
        return jsonify({"ok": False, "error": "Empty or missing speech line"}), 400

    if s.add_speech_line(line):
        return jsonify({"ok": True, "message": "Queued"}), 200
    return jsonify({"ok": False, "error": "Invalid format. Use: Character|speed|text"}), 400


@app.route("/health", methods=["GET"])
def health() -> tuple[dict, int]:
    """Health check."""
    return jsonify({"ok": True, "service": "KittenTTS"}), 200


def init_speech(
    model_dir: str = "KittenML/",
    model_name: str = "kitten-tts-nano-0.8-fp32",
    default_voice: str = "Leo",
    speed_offset: float = 0.2,
) -> None:
    """Initialize the shared Speech instance. Call before running the server."""
    global speech
    speech = Speech(
        model_dir=model_dir,
        model_name=model_name,
        default_voice=default_voice,
        speed_offset=speed_offset,
    )
    speech.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="KittenTTS API server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=5001, help="Bind port (5000 often used by macOS AirPlay)")
    parser.add_argument("--model-dir", default="KittenML/", help="Model directory")
    parser.add_argument("--model", default="kitten-tts-nano-0.8-fp32", help="Model name")
    parser.add_argument("--voice", default="Leo", help="Default voice")
    parser.add_argument("--speed-offset", type=float, default=0.2, help="Speed offset")
    parser.add_argument("--debug", action="store_true", help="Flask debug mode")
    args = parser.parse_args()

    init_speech(
        model_dir=args.model_dir,
        model_name=args.model,
        default_voice=args.voice,
        speed_offset=args.speed_offset,
    )

    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    finally:
        if speech:
            speech.shutdown()


if __name__ == "__main__":
    main()
