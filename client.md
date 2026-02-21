# client.py — KittenTTS API Client

Sends speech lines to the KittenTTS server (`server.py`) for text-to-speech playback. Can connect to a running server or optionally start the server as a subprocess.

---

## Quick Start

```bash
# Server must be running first (see server.md)
python server.py &

# Send default speech lines
python client.py

# Start server automatically, send lines, then stop
python client.py --start-server
```

---

## POST Options

### Endpoint

`POST /speak`

### Request Formats

The server accepts speech lines in two formats:

#### 1. JSON body (`Content-Type: application/json`)

```json
{
  "line": "Character|speed|text"
}
```

#### 2. Plain text body (`Content-Type: text/plain`)

```
Character|speed|text
```

### Speech Line Format

`Character|speed|text`

| Field | Description | Example |
|-------|-------------|---------|
| Character | Voice name | `Leo`, `Bella`, `Jasper`, `Kiki`, `Luna`, `Rosie`, `Bruno` |
| speed | Float multiplier (server adds speed_offset) | `1.2`, `1.4`, `1.0` |
| text | Text to speak | `Hello, this is a test.` |

### Responses

| Status | Body | Meaning |
|--------|------|---------|
| 200 | `{"ok": true, "message": "Queued"}` | Line queued successfully |
| 400 | `{"ok": false, "error": "..."}` | Invalid format or empty line |

---

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Server host |
| `--port` | `5001` | Server port (5000 often used by macOS AirPlay) |
| `--start-server` | — | Start server.py as subprocess before sending |
| `--plain` | — | Use plain text POST instead of JSON |
| `--lines` | (default lines) | Custom speech lines to send |

---

## Examples

### cURL — JSON POST

```bash
curl -X POST http://127.0.0.1:5001/speak \
  -H "Content-Type: application/json" \
  -d '{"line": "Leo|1.2|Hello, this is a test."}'
```

### cURL — Plain Text POST

```bash
curl -X POST http://127.0.0.1:5001/speak \
  -H "Content-Type: text/plain" \
  -d "Bella|1.4|Hi there."
```

### Python client — Custom lines

```bash
python client.py --lines "Leo|1.2|First line." "Bella|1.4|Second line."
```

### Python client — Plain text mode

```bash
python client.py --plain
```

---

## Dependencies

- `requests` — HTTP client (in `requirements.txt`)

---

## See Also

- [server.md](server.md) — API server documentation
- [speech.md](speech.md) — Core Speech class used by the server
