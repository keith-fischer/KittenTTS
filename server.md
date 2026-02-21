# server.py — KittenTTS API Server

Flask API server that accepts POST requests with speech lines and queues them for playback using the shared `Speech` class. Runs on standby for incoming API calls.

---

## Quick Start

```bash
# Start server (default: http://127.0.0.1:5001)
python server.py

# Custom host/port
python server.py --host 0.0.0.0 --port 8080

# Debug mode
python server.py --debug
```

---

## API Endpoints

### POST /speak

Queue a speech line for playback.

**Request body:** See [client.md](client.md) for POST options (JSON or plain text).

**Response:** `{"ok": true, "message": "Queued"}` (200) or `{"ok": false, "error": "..."}` (400)

### GET /health

Health check.

**Response:** `{"ok": true, "service": "KittenTTS"}` (200)

---

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `5001` | Bind port (5000 often used by macOS AirPlay) |
| `--model-dir` | `KittenML/` | Model directory |
| `--model` | `kitten-tts-nano-0.8-fp32` | Model name |
| `--voice` | `Leo` | Default voice for unknown characters |
| `--speed-offset` | `0.2` | Speed offset applied to script values |
| `--debug` | — | Flask debug mode |

---

## Architecture

```
Client POST → Flask /speak → Speech.add_speech_line() → Worker threads → Player thread → Audio
```

The server creates a single `Speech` instance at startup. Each POST to `/speak` calls `speech.add_speech_line(line)`, which queues the line for processing. Worker threads generate audio; the player thread plays clips in order.

---

## Dependencies

- `flask` — Web framework (in `requirements.txt`)
- `speech` — Core Speech class (see [speech.md](speech.md))

---

## See Also

- [client.md](client.md) — Client and POST options
- [speech.md](speech.md) — Core Speech class
- [app.md](app.md) — Script player (uses same Speech class)
